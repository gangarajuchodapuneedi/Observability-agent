"""HTTP API server for the observability pipeline."""

import sys
import os

# Add parent directory to path if running directly (not as module)
# This must happen before any src.* imports
if __file__:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from flask import Flask, request, jsonify
from flask_cors import CORS
from src.pipeline_types import UserRequest
from src.cache_layer import get_from_cache, set_in_cache
from src.retriever import run_retriever
from src.context_construction import build_context
from src.guardrails import run_input_guardrail, run_output_guardrail
from src.model_gateway import route_model, generate_response, score_response
from src.write_action import perform_write_action
from src.logging_layer import log_event
from src.arch_drift_client import fetch_last_arch_drifts

app = Flask(__name__)
CORS(app)  # Enable CORS for VS Code extension


def detect_arch_drift_intent(question: str) -> bool:
    """
    Detect if the question is about architecture drift.
    Returns True if the question appears to be asking about architecture drift.
    """
    question_lower = question.lower()
    drift_keywords = [
        "architecture drift",
        "arch drift",
        "architectural drift",
        "architecture change",
        "arch change",
        "drift",
        "drifts",
        "architecture evolution",
        "arch evolution"
    ]
    return any(keyword in question_lower for keyword in drift_keywords)


def extract_repo_from_question(question: str) -> str:
    """
    Extract repository name from question, or return default.
    Tries to find a GitHub URL in the question, otherwise uses environment variable or default.
    """
    import os
    import re
    
    # Try to extract GitHub URL from question
    github_url_pattern = r'https?://github\.com/[\w\-\.]+/[\w\-\.]+(?:\.git)?'
    match = re.search(github_url_pattern, question)
    if match:
        repo_url = match.group(0)
        log_event("API", f"Extracted repo from question: {repo_url}")
        return repo_url
    
    # Fall back to environment variable or default
    default_repo = os.getenv("DEFAULT_REPO", "default-repo")
    return default_repo


def build_arch_drift_markdown(drift_data: dict) -> str:
    """
    Convert ArchDrift JSON into a structured, whitespace-friendly summary.
    The output intentionally uses blank lines between sections to avoid the
    webview merging lines into a single paragraph.
    """
    from datetime import datetime
    
    # Accept both "items" and older "drifts" key
    items = drift_data.get("items") or drift_data.get("drifts") or []
    window_summary = drift_data.get("window_summary", {})

    if not items:
        return "No architecture drifts found for this repo in the current analysis window."
    
    # Summary counts – prefer window_summary, otherwise compute
    total_count = window_summary.get("total_drifts", len(items))
    positive_count = window_summary.get(
        "positive",
        sum(1 for item in items if item.get("type") == "positive"),
    )
    negative_count = window_summary.get(
        "negative",
        sum(1 for item in items if item.get("type") == "negative"),
    )

    repo_url = (
        drift_data.get("repo")
        or window_summary.get("repo")
        or items[0].get("repo_url")
        or "default-repo"
    )

    # Most affected area / team – prefer summary, otherwise derive
    most_affected_area = window_summary.get("most_affected_area")
    most_impacted_team = window_summary.get("most_impacted_team")

    if not most_affected_area:
        drift_types: dict[str, int] = {}
        for item in items:
            drift_type = (
                item.get("driftType")
                or item.get("area")
                or item.get("type")
                or "Unknown"
            )
            drift_types[drift_type] = drift_types.get(drift_type, 0) + 1
        most_affected_area = (
            max(drift_types.items(), key=lambda x: x[1])[0] if drift_types else None
        )
    
    if not most_impacted_team:
        team_counts: dict[str, int] = {}
        for item in items:
            teams = item.get("teams", [])
            if isinstance(teams, list):
                for team in teams:
                    team_counts[team] = team_counts.get(team, 0) + 1
        most_impacted_team = (
            max(team_counts.items(), key=lambda x: x[1])[0] if team_counts else None
        )

    def format_date(date_str: str) -> str:
        if not date_str:
            return ""
        try:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            return dt.strftime("%d %b %Y at %I:%M %p")
        except Exception:
            return date_str

    def or_dash(value: str | None) -> str:
        return value if (value and str(value).strip()) else "–"

    lines: list[str] = []
    
    # Header (no markdown headers; explicit blank lines between each line)
    lines.append("ArchDrift – Architectural Drift Map")
    lines.append("")
    lines.append("Repo URL")
    lines.append(repo_url)
    lines.append("")
    lines.append(
        f"In this analysis window: {total_count} drifts ({positive_count} positive, {negative_count} negative)"
    )
    lines.append("")
    lines.append(f"Most affected area: {most_affected_area or '–'}")
    lines.append("")
    lines.append(f"Most impacted team: {most_impacted_team or '–'}")
    lines.append("")
    
    # Drift timeline
    lines.append("Drift Timeline")
    lines.append("")
    
    for item in items:
        raw_date = item.get("date") or item.get("timestamp") or ""
        formatted_date = format_date(raw_date)
        drift_type = item.get("driftType") or item.get("area") or item.get("type") or "Unknown"
        item_type = item.get("type") or item.get("direction") or "unknown"
        teams = item.get("teams", [])
        teams_str = ", ".join(teams) if isinstance(teams, list) and teams else "N/A"
        title = item.get("title") or item.get("id") or "Unknown drift"

        lines.append(f"{formatted_date} – {item_type} – {drift_type} – {teams_str}")
        lines.append(f"{title}")
        lines.append("")

    # Detailed view for the first drift only (per template)
    first = items[0]
    lines.append("------------------------------------------------------------")
    lines.append("")
    
    title = first.get("title") or first.get("id") or "Unknown drift"
    drift_area = first.get("driftType") or first.get("area") or first.get("type") or "Unknown"
    item_type = first.get("type") or first.get("direction") or "unknown"
    raw_date = first.get("date") or first.get("timestamp") or ""
    formatted_date = format_date(raw_date)

    lines.append(f"{title}")
    lines.append("")
    lines.append(f"{drift_area}   {item_type}")
    lines.append("")
    if formatted_date:
        lines.append(f"{formatted_date}")
        lines.append("")
        
    impact_level = first.get("impactLevel")
    lines.append(f"Impact: {impact_level or '–'}")
    risk_areas = first.get("riskAreas", [])
    if risk_areas and isinstance(risk_areas, list):
        lines.append(f"Affects: {', '.join(risk_areas)}")
    else:
        lines.append("Affects: –")
    lines.append("")
        
    summary = first.get("summary")
    lines.append("Summary")
    lines.append(or_dash(summary))
    lines.append("")
        
    functionality = first.get("functionality")
    lines.append("Functionality")
    lines.append(or_dash(functionality))
    lines.append("")
        
    advantage = first.get("advantage")
    lines.append("Advantage")
    lines.append(or_dash(advantage))
    lines.append("")
        
    disadvantage = first.get("disadvantage")
    lines.append("Disadvantage")
    lines.append(or_dash(disadvantage))
    lines.append("")
        
    root_cause = first.get("root_cause")
    lines.append("Root Cause")
    lines.append(or_dash(root_cause))
    lines.append("")
        
    recommended_actions = first.get("recommendedActions", [])
    lines.append("Recommended Actions")
    if recommended_actions and isinstance(recommended_actions, list):
        for action in recommended_actions:
            lines.append(f"- {action}")
    else:
        lines.append("- –")
    lines.append("")
        
    files_changed = first.get("files_changed", [])
    lines.append("Files Changed")
    if files_changed and isinstance(files_changed, list):
        for file_path in files_changed:
            lines.append(f"- {file_path}")
    else:
        lines.append("- –")
    lines.append("")
        
    commit_hash = first.get("commit_hash") or first.get("commit")
    lines.append(f"Commit: {commit_hash or '–'}")
    repo_url_item = first.get("repo_url")
    lines.append(f"Repository: {repo_url_item or repo_url}")
    
    return "\n".join(lines)


def handle_arch_drift_request(question: str) -> dict:
    """
    Handle architecture drift questions.
    For now, always point the user to the ArchDrift UI instead of returning inline content.
    """
    log_event("API", "Routing to ArchDrift handler (link-only mode)")
    repo = extract_repo_from_question(question)
    arch_drift_ui = "http://localhost:5173/"
    # Use markdown link to ensure clickability even if the webview renders plain markdown
    answer = (
        f"Open the ArchDrift view to see architecture drifts for this repo: "
        f"[ArchDrift UI]({arch_drift_ui})\n\n"
        f"Repo: {repo}"
    )

    return {
        "mode": "arch_drift",
        "answer": answer,
        "score": None,
        "source": "arch_drift",
        "trace": {"repo": repo, "link": arch_drift_ui},
        "drift_data": None
    }


def process_question(question: str):
    """Process a question through the pipeline and return the result."""
    log_event("API", f"Processing question: {question[:50]}...")
    
    # Check if this is an architecture drift question
    if detect_arch_drift_intent(question):
        return handle_arch_drift_request(question)
    
    # Default pipeline for text questions
    # Create UserRequest
    user_request = UserRequest(text=question, user_id="api_user")
    
    # Check cache first
    cache_key = f"{user_request.user_id}:{user_request.text}"
    cached_answer = get_from_cache(cache_key)
    
    if cached_answer is not None:
        log_event("API", "Cache hit - returning cached answer")
        return {
            "answer": cached_answer,
            "score": None,
            "source": "cache",
            "trace": {"cached": True}
        }
    
    log_event("API", "Cache miss - processing through pipeline")
    
    # Run pipeline
    items = run_retriever(user_request)
    context = build_context(user_request, items)
    model_input = run_input_guardrail(context)
    model_name = route_model(model_input)
    model_output = generate_response(model_name, model_input)
    model_output = score_response(model_output)
    model_output = run_output_guardrail(model_output)
    perform_write_action(model_output)
    
    # Cache the answer
    set_in_cache(cache_key, model_output.answer)
    
    log_event("API", f"Pipeline complete - answer generated, score: {model_output.score}")
    
    return {
        "answer": model_output.answer,
        "score": model_output.score,
        "source": model_output.source,
        "trace": {}
    }


@app.route('/ask', methods=['POST'])
def ask():
    """Handle POST /ask requests."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "Request body is required"}), 400
        
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "Question is required"}), 400
        
        result = process_question(question)
        return jsonify(result)
    
    except Exception as e:
        log_event("API", f"Error processing request: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok", "service": "observability-agent"})


if __name__ == '__main__':
    print("=" * 60)
    print("Observability Agent API Server")
    print("=" * 60)
    print("Starting server on http://localhost:8000")
    print("Endpoints:")
    print("  POST http://localhost:8000/ask")
    print("  GET  http://localhost:8000/health")
    print("=" * 60)
    app.run(host='localhost', port=8000, debug=True, use_reloader=False)

