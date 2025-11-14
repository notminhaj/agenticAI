import torch
import torch.nn.functional as F
from torch import Tensor
from transformers import AutoTokenizer, AutoModel
from typing import List, Union

# Global model and tokenizer (loaded once for efficiency)
_tokenizer = None
_model = None


def _get_model():
    """Lazy load the model and tokenizer (only load once)."""
    global _tokenizer, _model
    if _tokenizer is None or _model is None:
        print("Loading E5 model (this may take a moment on first call)...")
        _tokenizer = AutoTokenizer.from_pretrained('intfloat/e5-base-v2')
        _model = AutoModel.from_pretrained('intfloat/e5-base-v2')
    return _tokenizer, _model


def average_pool(last_hidden_states: Tensor,
                 attention_mask: Tensor) -> Tensor:
    """Average pool the hidden states, masking out padding tokens."""
    last_hidden = last_hidden_states.masked_fill(~attention_mask[..., None].bool(), 0.0)
    return last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[..., None]


def rank_passages(query: str, passages: List[str], return_embeddings: bool = False) -> Union[List[float], tuple]:
    """
    Rank passages by their relevance to a query using the E5 embedding model.
    
    Args:
        query (str): The search query (e.g., "Agentic AI")
        passages (List[str]): List of text passages to rank
        return_embeddings (bool): If True, also return the query and passage embeddings
        
    Returns:
        If return_embeddings=False: List[float] - similarity scores for each passage (higher = more relevant)
        If return_embeddings=True: tuple of (scores, query_emb, passage_embs)
            - scores: List[float] - similarity scores
            - query_emb: Tensor - query embedding vector
            - passage_embs: Tensor - passage embedding vectors
    """
    if not passages:
        return [] if not return_embeddings else ([], None, None)
    
    # Get model and tokenizer (lazy loaded)
    tokenizer, model = _get_model()
    
    # Format inputs: E5 model expects "query: " or "passage: " prefixes
    input_texts = [f'query: {query}']
    for passage in passages:
        input_texts.append(f'passage: {passage}')
    
    # Tokenize the input texts
    batch_dict = tokenizer(input_texts, max_length=512, padding=True, truncation=True, return_tensors='pt')
    
    # Get embeddings
    with torch.no_grad():  # Disable gradient computation for inference
        outputs = model(**batch_dict)
        embeddings = average_pool(outputs.last_hidden_state, batch_dict['attention_mask'])
    
    # Normalize embeddings (L2 normalization for cosine similarity)
    embeddings = F.normalize(embeddings, p=2, dim=1)
    
    # Compute similarity scores
    query_emb = embeddings[0]
    passage_embs = embeddings[1:]
    scores = (query_emb @ passage_embs.T).squeeze().tolist()
    
    # Handle single passage case (scores might be a scalar)
    if not isinstance(scores, list):
        scores = [scores]
    
    if return_embeddings:
        return scores, query_emb, passage_embs
    return scores


# Example usage (commented out - can be used for testing)
if __name__ == "__main__":
    topic = "Agentic AI"
    passages = ["Research paper content 1", "Agentic AI Research paper content 2", "AI Research paper content 3", "Gaming paper 4"]
    
    scores = rank_passages(topic, passages)
    print(f"Query: {topic}")
    print(f"Scores: {scores}")
