"""LLM client for calling Ollama API."""

import os
import time
import requests
from typing import Optional, Tuple


class LLMError(Exception):
    """Exception raised when LLM call fails."""
    pass


def build_observability_prompt(question: str, context: Optional[str] = None) -> str:
    """
    Build a prompt for the observability assistant.
    
    Args:
        question: The user's question
        context: Optional context string (formatted retrieved items)
        
    Returns:
        The complete prompt string
    """
    # Ultra-simple prompt - just the question (like the "Say hello" test that worked)
    # We'll format the answer into template structure in post-processing
    prompt = question
    
    # Optionally add context if available (but keep it minimal)
    if context:
        prompt = f"{question}\n\nContext: {context[:200]}"  # Limit context to 200 chars
    
    return prompt


def call_ollama_generate(prompt: str) -> Tuple[str, float]:
    """
    Call Ollama API to generate a response.
    
    Args:
        prompt: The prompt to send to the LLM
        
    Returns:
        Tuple of (answer: str, latency: float in seconds)
        
    Raises:
        LLMError: If the API call fails or returns invalid response
    
    # MANUAL TEST:
    # 1. Start Ollama with tinyllama.
    # 2. Run the API server.
    # 3. POST /ask with {"question": "How do I use distributed tracing?"}.
    # 4. Confirm the response text follows the template:
    #    Question / Short Answer / When / How / Checklist / Optional Extras.
    # 5. Confirm answer is not excessively long and respects our model options.
    """
    ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "tinyllama")  # Default to tinyllama for faster responses
    timeout_sec = int(os.getenv("OLLAMA_TIMEOUT_SEC", "30"))  # Reduced to 30 seconds for faster failure detection
    
    # Model parameters with environment variable support and safe defaults
    temperature = float(os.getenv("OBS_AGENT_LLM_TEMPERATURE", "0.1"))
    top_p = float(os.getenv("OBS_AGENT_LLM_TOP_P", "1.0"))
    num_predict = int(os.getenv("OBS_AGENT_LLM_NUM_PREDICT", "64"))  # Small value like the working test (was 10 in test)
    repeat_penalty = float(os.getenv("OBS_AGENT_LLM_REPEAT_PENALTY", "1.3"))  # Increased to reduce repetition
    
    url = f"{ollama_host}/api/generate"
    
    payload = {
        "model": ollama_model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "top_p": top_p,
            "num_predict": num_predict,
            "repeat_penalty": repeat_penalty
        }
    }
    
    print(f"[LLM] Calling Ollama at {url} with model: {ollama_model}")
    print(f"[LLM] Timeout set to: {timeout_sec} seconds")
    print(f"[LLM] Model options: temperature={temperature}, top_p={top_p}, num_predict={num_predict}, repeat_penalty={repeat_penalty}")
    print(f"[LLM] Prompt length: {len(prompt)} characters")
    
    start_time = time.time()
    
    try:
        print(f"[LLM] Sending request to Ollama...")
        response = requests.post(url, json=payload, timeout=timeout_sec)
        latency = time.time() - start_time
        print(f"[LLM] Response received in {latency:.2f} seconds, status: {response.status_code}")
        
        if response.status_code != 200:
            raise LLMError(f"Ollama API returned status {response.status_code}: {response.text}")
        
        response_json = response.json()
        
        if "response" not in response_json:
            raise LLMError(f"Ollama API response missing 'response' field: {response_json}")
        
        answer = response_json["response"]
        
        return answer, latency
        
    except requests.exceptions.Timeout:
        raise LLMError(f"Ollama API call timed out after {timeout_sec} seconds")
    except requests.exceptions.ConnectionError as e:
        raise LLMError(f"Failed to connect to Ollama at {ollama_host}: {e}")
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Ollama API request failed: {e}")
    except Exception as e:
        raise LLMError(f"Unexpected error calling Ollama: {e}")
