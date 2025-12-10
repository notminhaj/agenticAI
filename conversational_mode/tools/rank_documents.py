from crewai.tools import tool

@tool
def rank_documents(query: str, documents: list, text_key: str = "raw_text") -> list:
    """
    This is a special tool that can rank documents based on relevance to topic.
    This enables you to search for more articles and fetch extra content so that you can present higher quality summaries.

    Rank a list of fetched documents by their relevance to a query using neural embeddings.
    
    This function takes documents returned by fetch() and ranks them using the E5 embedding model.
    Documents are sorted by relevance score (highest first).
    
    Args:
        query (str): The search query to rank documents against
        documents (list): List of document dictionaries (from fetch() or similar)
                         Each dict should contain at least the text_key field
        text_key (str): Key in document dict that contains the text to rank. Default: "raw_text"
        
    Returns:
        list: List of document dictionaries with added "score" field, sorted by score (highest first)
              Each document dict will have:
              - All original fields from input
              - "score" (float): Relevance score (0-1, higher = more relevant)
              
    Example:
        papers = search("Agentic AI", limit=5)
        fetched = [fetch(paper["url"]) for paper in papers]
        ranked = rank_documents("Agentic AI", fetched)
        # ranked[0] is the most relevant paper
    """
    # Import rank_passages - try multiple import paths
    try:
        from nn_model.nn import rank_passages
    except ImportError:
        try:
            from ..nn_model.nn import rank_passages
        except ImportError:
            try:
                from nn_agent_mode.nn import rank_passages
            except ImportError:
                raise ImportError("Could not import rank_passages. Please ensure nn.py with rank_passages function is available.")
    
    # Extract text passages from documents
    passages = []
    valid_docs = []
    
    for doc in documents:
        # Skip error documents
        if doc.get("kind") == "error":
            continue
        
        # Check if text exists and is not empty/whitespace
        text = doc.get(text_key, "")
        if not text or not text.strip():
            continue
        
        # Truncate very long texts to avoid token limits (E5 max is 512 tokens)
        # Rough estimate: ~4 chars per token, so 512 tokens ≈ 2000 chars
        if len(text) > 2000:
            text = text[:2000] + "..."
        
        passages.append(text)
        valid_docs.append(doc)
    
    if not passages:
        print("[WARNING] No valid documents to rank")
        return documents  # Return original if nothing to rank
    
    # Get relevance scores from neural network
    scores = rank_passages(query, passages)
    
    # Add scores to documents and sort by score
    for i, doc in enumerate(valid_docs):
        doc["score"] = scores[i]
    
    # Sort by score (highest first)
    ranked_docs = sorted(valid_docs, key=lambda x: x["score"], reverse=True)
    
    # Add unranked error documents at the end (with debug info)
    # Only include documents that weren't already processed
    processed_urls = {doc.get("url") for doc in valid_docs}
    error_docs = []
    for doc in documents:
        # Skip if already processed
        if doc.get("url") in processed_urls:
            continue
            
        # Check if this document should have been processed but wasn't
        text = doc.get(text_key, "")
        has_text = text and text.strip()
        
        if doc.get("kind") == "error":
            # Error documents get score of 0.0
            doc["score"] = 0.0
            doc["_debug"] = "Error fetching document"
            error_docs.append(doc)
        elif not has_text:
            # Document has no text - assign score of 0 and add debug info
            doc["score"] = 0.0
            doc["_debug"] = "No text content available for ranking"
            error_docs.append(doc)
    
    ranked_docs.extend(error_docs)
    
    if error_docs:
        print(f"[INFO] {len(error_docs)} documents could not be ranked (no text content or errors)")
    print(f"[OK] Ranked {len(ranked_docs)} documents by relevance to '{query}'")
    return ranked_docs

