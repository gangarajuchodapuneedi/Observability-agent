"""Retriever module for web and memory sources."""

from src.pipeline_types import UserRequest, RetrievedItem


def retrieve_from_web(request: UserRequest) -> list[RetrievedItem]:
    """
    Retrieve items from web sources (mock implementation).
    
    Args:
        request: The user request
        
    Returns:
        List of retrieved items from web
    """
    print(f"[RETRIEVER] Retrieving from web for request: {request.text[:50]}...")
    # Return 1-2 fake items
    items = [
        RetrievedItem(source="web", content=f"Web result 1 for: {request.text}"),
        RetrievedItem(source="web", content=f"Web result 2 for: {request.text}")
    ]
    print(f"[RETRIEVER] Retrieved {len(items)} items from web")
    return items


def retrieve_from_memory(request: UserRequest) -> list[RetrievedItem]:
    """
    Retrieve items from external memory (mock implementation).
    
    Args:
        request: The user request
        
    Returns:
        List of retrieved items from memory
    """
    print(f"[RETRIEVER] Retrieving from memory for request: {request.text[:50]}...")
    # Return 1-2 fake items
    items = [
        RetrievedItem(source="memory", content=f"Memory result 1 for: {request.text}")
    ]
    print(f"[RETRIEVER] Retrieved {len(items)} items from memory")
    return items


def run_retriever(request: UserRequest) -> list[RetrievedItem]:
    """
    Run the complete retrieval process from all sources.
    
    Args:
        request: The user request
        
    Returns:
        Combined list of all retrieved items
    """
    print(f"[RETRIEVER] Starting retrieval process...")
    web_items = retrieve_from_web(request)
    memory_items = retrieve_from_memory(request)
    all_items = web_items + memory_items
    print(f"[RETRIEVER] Total items retrieved: {len(all_items)}")
    return all_items

