"""Context construction module."""

from src.pipeline_types import UserRequest, RetrievedItem, ContextPacket


def build_context(request: UserRequest, items: list[RetrievedItem]) -> ContextPacket:
    """
    Build a context packet from the request and retrieved items.
    
    Args:
        request: The user request
        items: List of retrieved items
        
    Returns:
        A ContextPacket containing the request and items
    """
    print(f"[CONTEXT] Building context packet...")
    print(f"[CONTEXT] Request text: {request.text[:50]}...")
    print(f"[CONTEXT] Number of items: {len(items)}")
    for i, item in enumerate(items, 1):
        print(f"[CONTEXT] Item {i}: source={item.source}, content={item.content[:50]}...")
    
    context = ContextPacket(request=request, items=items)
    print(f"[CONTEXT] Context packet built successfully")
    return context

