import sys
from unittest.mock import MagicMock

# Mock crewai before importing tools
sys.modules["crewai"] = MagicMock()
sys.modules["crewai.tools"] = MagicMock()

# Mock nn_model to prevent transformers loading via rank_documents -> tools/__init__
sys.modules["nn_model"] = MagicMock()
sys.modules["nn_model.nn"] = MagicMock()
sys.modules["transformers"] = MagicMock()
sys.modules["openai"] = MagicMock()
sys.modules["torch"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["torch.nn.functional"] = MagicMock()
sys.modules["sentence_transformers"] = MagicMock()

# Define a mock tool decorator that preserves the function
def mock_tool(name_or_func):
    if callable(name_or_func):
        name_or_func.func = name_or_func
        return name_or_func
    def wrapper(func):
        func.func = func
        return func
    return wrapper

mock_crewai_tools = MagicMock()
mock_crewai_tools.tool = mock_tool
sys.modules["crewai.tools"] = mock_crewai_tools

from unittest import TestCase, main
from unittest.mock import patch, MagicMock

from tools.federated_search import (
    federated_search, 
    expand_keywords, 
    search_arxiv, 
    search_brave, 
    search_hackernews,
    search_twitter_via_brave,
    search_substack_via_brave
)
from tools.fetch import fetch
from tools.rank_documents import rank_documents

class TestFederatedSearch(TestCase):

    @patch('tools.federated_search.llm')
    def test_expand_keywords(self, mock_llm):
        # Mock LLM response
        mock_llm.call.return_value = """
        {
            "academic": ["test academic"],
            "general": ["test general"],
            "social": ["test social"]
        }
        """
        keywords = expand_keywords("test topic")
        self.assertEqual(keywords['academic'], ["test academic"])
        self.assertEqual(keywords['general'], ["test general"])

    @patch('tools.federated_search.requests.get')
    def test_search_arxiv(self, mock_get):
        # Mock arXiv response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.content = b"""
        <feed xmlns="http://www.w3.org/2005/Atom">
            <entry>
                <title>Test Paper</title>
                <id>http://arxiv.org/abs/1234.5678</id>
                <summary>Test Summary</summary>
                <published>2024-01-01T00:00:00Z</published>
            </entry>
        </feed>
        """
        mock_get.return_value = mock_response
        
        results = search_arxiv(["test"], 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "Test Paper")
        self.assertEqual(results[0]['source'], "arxiv")

    @patch('tools.federated_search.requests.get')
    def test_search_brave(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {"title": "Brave Result", "url": "http://example.com", "description": "Desc", "age": "1d"}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        # Mock API key presence
        with patch('tools.federated_search.BRAVE_API_KEY', 'fake_key'):
            results = search_brave(["test"], 1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['title'], "Brave Result")
            self.assertEqual(results[0]['source'], "brave_web")

    @patch('tools.federated_search.requests.get')
    def test_search_hackernews(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "hits": [
                {"title": "HN Story", "url": "http://hn.com/story", "points": 100, "num_comments": 50, "created_at": "2024-01-01"}
            ]
        }
        mock_get.return_value = mock_response
        
        results = search_hackernews(["test"], 1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['title'], "HN Story")
        self.assertEqual(results[0]['source'], "hackernews")

    @patch('tools.federated_search.requests.get')
    def test_search_twitter_via_brave(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {"title": "Twitter Post", "url": "https://twitter.com/user/123", "description": "Tweet content", "age": "1h"}
                ]
            }
        }
        mock_get.return_value = mock_response
        
        with patch('tools.federated_search.BRAVE_API_KEY', 'fake_key'):
            results = search_twitter_via_brave(["test"], 1)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]['title'], "Twitter Post")
            self.assertEqual(results[0]['source'], "twitter_web")
            
            # Verify query param
            args, kwargs = mock_get.call_args
            self.assertIn("site:twitter.com OR site:x.com", kwargs['params']['q'])

    @patch('tools.federated_search.rank_documents')
    @patch('tools.federated_search.fetch')
    @patch('tools.federated_search.expand_keywords')
    @patch('tools.federated_search.search_arxiv')
    @patch('tools.federated_search.search_brave')
    @patch('tools.federated_search.search_hackernews')
    @patch('tools.federated_search.search_twitter_via_brave')
    @patch('tools.federated_search.search_substack_via_brave')
    def test_federated_search_integration(self, mock_substack, mock_twitter, mock_hn, mock_brave, mock_arxiv, mock_expand, mock_fetch, mock_rank):
        # Setup mocks
        mock_expand.return_value = {"academic": ["a"], "general": ["g"], "social": ["s"]}
        mock_arxiv.return_value = [{"title": "Arxiv Paper", "url": "http://arxiv.org/1", "source": "arxiv", "snippet": "s", "timestamp": "t"}]
        mock_brave.return_value = [{"title": "Web Page", "url": "http://web.com/1", "source": "brave_web", "snippet": "s", "timestamp": "t"}]
        mock_hn.return_value = []
        mock_twitter.return_value = []
        mock_twitter.return_value = []
        mock_substack.return_value = []
        
        # Mock fetch and rank
        mock_fetch.func.return_value = {"raw_text": "Full content of the paper"}
        # rank_documents.func returns the list with scores
        mock_rank.func.return_value = [
            {"title": "Arxiv Paper", "url": "http://arxiv.org/1", "source": "arxiv", "snippet": "s", "timestamp": "t", "raw_text": "Full content", "score": 0.9},
            {"title": "Web Page", "url": "http://web.com/1", "source": "brave_web", "snippet": "s", "timestamp": "t", "raw_text": "Full content", "score": 0.8}
        ]
        
        # Run search
        result_str = federated_search.func("test topic", limit=2)
        
        self.assertIn("Federated Search Results", result_str)
        self.assertIn("[ARXIV] Arxiv Paper", result_str)
        self.assertIn("[BRAVE_WEB] Web Page", result_str)

if __name__ == '__main__':
    main()
