# Observability Pipeline Learning Project

A minimal Python project that simulates an observability pipeline from user request through to final action and logging.

## Architecture

The pipeline follows this flow:

```
User -> Cache -> Retriever (Web + External Memory) -> Context construction 
-> Input guardrail -> Model Gateway (Routing, Generation, Score) 
-> Output guardrail -> Write Action -> Logging / Monitoring & Analytics
```

## Project Structure

- `src/types.py` - Data classes for the pipeline
- `src/cache_layer.py` - Simple in-memory cache
- `src/retriever.py` - Web and memory retrieval (mock)
- `src/context_construction.py` - Context packet builder
- `src/guardrails.py` - Input and output guardrails
- `src/model_gateway.py` - Model routing, generation, and scoring
- `src/write_action.py` - Action execution (mock)
- `src/logging_layer.py` - Event and error logging
- `src/main.py` - Pipeline orchestration

## Usage

Run the pipeline from the command line:

```bash
python -m src.main
```

You will be prompted to enter an observability question, and the pipeline will process it through all stages.

## Note

This is a teaching/demo project. All components are mock implementations that log their operations without calling real external services or LLM APIs.

