"""Main entry point for the observability pipeline."""

import sys
from src.pipeline_types import UserRequest
from src.cache_layer import get_from_cache, set_in_cache
from src.retriever import run_retriever
from src.context_construction import build_context
from src.guardrails import run_input_guardrail, run_output_guardrail
from src.model_gateway import route_model, generate_response, score_response
from src.write_action import perform_write_action
from src.logging_layer import log_event


def main():
    """Run the observability pipeline."""
    # Read prompt from command line
    prompt = input("Enter your observability question: ")
    if not prompt.strip():
        print("Error: Empty prompt provided")
        sys.exit(1)
    
    # Create UserRequest
    user_request = UserRequest(text=prompt, user_id="demo_user")
    log_event("MAIN", f"Received request from user {user_request.user_id}: {user_request.text}")
    
    # Check cache first
    cache_key = f"{user_request.user_id}:{user_request.text}"
    cached_answer = get_from_cache(cache_key)
    
    if cached_answer is not None:
        log_event("MAIN", "Cache hit - returning cached answer")
        print(f"\n=== FINAL ANSWER (from cache) ===")
        print(cached_answer)
        return
    
    log_event("MAIN", "Cache miss - processing request through pipeline")
    
    # Run retriever
    log_event("MAIN", "Starting retrieval phase")
    items = run_retriever(user_request)
    log_event("MAIN", f"Retrieval complete: {len(items)} items")
    
    # Build context
    log_event("MAIN", "Building context")
    context = build_context(user_request, items)
    log_event("MAIN", "Context built")
    
    # Run input guardrail
    log_event("MAIN", "Running input guardrail")
    model_input = run_input_guardrail(context)
    log_event("MAIN", "Input guardrail passed")
    
    # Route model -> generate -> score
    log_event("MAIN", "Routing to model")
    model_name = route_model(model_input)
    log_event("MAIN", f"Routed to model: {model_name}")
    
    log_event("MAIN", "Generating response")
    model_output = generate_response(model_name, model_input)
    log_event("MAIN", "Response generated")
    
    log_event("MAIN", "Scoring response")
    model_output = score_response(model_output)
    log_event("MAIN", "Response scored")
    
    # Run output guardrail
    log_event("MAIN", "Running output guardrail")
    model_output = run_output_guardrail(model_output)
    log_event("MAIN", "Output guardrail passed")
    
    # Perform write action
    log_event("MAIN", "Performing write action")
    action_result = perform_write_action(model_output)
    log_event("MAIN", f"Write action completed: {action_result.details}")
    
    # Store in cache
    log_event("MAIN", "Storing answer in cache")
    set_in_cache(cache_key, model_output.answer)
    log_event("MAIN", "Answer cached")
    
    # Print final answer
    print(f"\n=== FINAL ANSWER ===")
    print(model_output.answer)
    print(f"\n=== SCORE ===")
    print(model_output.score)
    log_event("MAIN", "Pipeline execution complete")


if __name__ == "__main__":
    main()

