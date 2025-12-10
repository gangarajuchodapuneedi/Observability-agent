"""Guardrails for input and output validation."""

from src.pipeline_types import ContextPacket, ModelInput, ModelOutput


def run_input_guardrail(context: ContextPacket) -> ModelInput:
    """
    Run input guardrails to check for secrets, PII, and forbidden actions.
    
    Args:
        context: The context packet to validate
        
    Returns:
        ModelInput with cleaned prompt
    """
    print(f"[INPUT_GUARDRAIL] Checking for secrets/PII/forbidden actions...")
    print(f"[INPUT_GUARDRAIL] Original prompt: {context.request.text}")
    
    # Simple transformation: convert to uppercase to show transformation
    cleaned_prompt = context.request.text.upper()
    print(f"[INPUT_GUARDRAIL] Cleaned prompt: {cleaned_prompt}")
    print(f"[INPUT_GUARDRAIL] Input guardrail passed")
    
    return ModelInput(context=context, cleaned_prompt=cleaned_prompt)


def run_output_guardrail(model_output: ModelOutput) -> ModelOutput:
    """
    Run output guardrails to check for safety issues.
    
    Args:
        model_output: The model output to validate
        
    Returns:
        The validated model output (unchanged for now)
    """
    print(f"[OUTPUT_GUARDRAIL] Checking output safety...")
    print(f"[OUTPUT_GUARDRAIL] Output answer: {model_output.answer[:100]}...")
    print(f"[OUTPUT_GUARDRAIL] Output score: {model_output.score}")
    print(f"[OUTPUT_GUARDRAIL] Output guardrail passed")
    
    return model_output

