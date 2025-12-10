"""Write action module for performing actions based on model output."""

from src.pipeline_types import ModelOutput, ActionResult


def perform_write_action(output: ModelOutput) -> ActionResult:
    """
    Perform a write action based on the model output (mock implementation).
    
    Args:
        output: The model output to act upon
        
    Returns:
        ActionResult indicating success and details
    """
    print(f"[WRITE_ACTION] Performing write action...")
    print(f"[WRITE_ACTION] Pretend to send email/update DB with this answer: {output.answer[:100]}...")
    
    result = ActionResult(success=True, details="Simulated write complete")
    print(f"[WRITE_ACTION] Write action completed: {result.details}")
    
    return result

