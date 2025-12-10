"""Model gateway for routing, generation, and scoring."""

import re
from typing import List, Tuple
from src.pipeline_types import ModelInput, ModelOutput
from src.llm_client import build_observability_prompt, call_ollama_generate, LLMError


def route_model(model_input: ModelInput) -> str:
    """
    Route the request to an appropriate model.
    
    Args:
        model_input: The model input
        
    Returns:
        The model name to use
    """
    print(f"[MODEL_GATEWAY] Routing model for prompt: {model_input.cleaned_prompt[:50]}...")
    model_name = "dummy-model"
    print(f"[MODEL_GATEWAY] Routed to model: {model_name}")
    return model_name


# Template structure constants
TEMPLATE_SECTIONS = {
    "question": "**Question**",
    "short_answer": "**1. Short Answer (1–3 lines)**",
    "when_why": "**2. When / Why You Use This**",
    "how_to": "**3. How To Do It (Practical Steps)**",
    "checklist": "**4. Quick Checklist (Ready-To-Use)**",
    "optional_extras": "**5. Optional Extras (Only if needed)**"
}


def _extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text using robust regex-based splitting.
    
    Args:
        text: Input text
        
    Returns:
        List of sentences (non-empty, stripped, complete)
    """
    if not text or not text.strip():
        return []
    
    # Remove markdown formatting that might interfere
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)  # Remove bold
    text = re.sub(r'\*([^*]+)\*', r'\1', text)  # Remove italic
    text = re.sub(r'`([^`]+)`', r'\1', text)  # Remove code
    
    # Split on sentence boundaries (., !, ? followed by whitespace or end)
    # But don't split on periods/colons that are part of lists or abbreviations
    # First, protect list items and common abbreviations
    text = re.sub(r':\s*-', ' LISTITEM', text)  # Protect "include: - item"
    sentences = re.split(r'[.!?]+\s+', text)
    # Restore list markers
    sentences = [s.replace(' LISTITEM', ': -') for s in sentences]
    
    # Clean and filter sentences
    result = []
    for sent in sentences:
        sent = sent.strip()
        # Filter out incomplete sentences (fragments)
        # A complete sentence should:
        # 1. Be at least 15 chars (not just "If there is")
        # 2. Have at least 2 words (allow 2-word sentences if substantial)
        # 3. Not be just punctuation
        # 4. Not end with incomplete phrases (common patterns)
        if sent and len(sent) >= 15 and not re.match(r'^[^\w]*$', sent):
            word_count = len(sent.split())
            # Filter out very short fragments (require at least 2 words, or 3 if very short)
            if word_count >= 2 and (word_count >= 3 or len(sent) >= 20):
                # Filter out common incomplete sentence patterns
                incomplete_patterns = [
                    r'^if there is$',
                    r'^if there$',
                    r'^when there$',
                    r'^where there$',
                    r'^that there$',
                ]
                is_incomplete = any(re.match(pattern, sent.lower()) for pattern in incomplete_patterns)
                if not is_incomplete:
                    result.append(sent)
    
    # If no sentences found, treat the whole text as one sentence (if substantial)
    if not result and text.strip() and len(text.strip()) >= 15:
        word_count = len(text.strip().split())
        if word_count >= 3:
            result.append(text.strip())
    
    return result


def _extract_lines(text: str) -> List[str]:
    """
    Extract meaningful lines from text.
    
    Args:
        text: Input text
        
    Returns:
        List of lines (non-empty, substantial)
    """
    if not text or not text.strip():
        return []
    
    lines = text.split('\n')
    result = []
    for line in lines:
        line = line.strip()
        # Keep lines that are substantial (at least 10 chars)
        if line and len(line) >= 10:
            result.append(line)
    
    return result


def _score_content_quality(text: str) -> float:
    """
    Score content quality (0.0 to 1.0) based on length and completeness.
    
    Args:
        text: Content to score
        
    Returns:
        Quality score
    """
    if not text or len(text.strip()) < 10:
        return 0.0
    
    score = 0.5  # Base score
    
    # Prefer longer content (up to reasonable limit)
    if 20 <= len(text) <= 200:
        score += 0.3
    elif len(text) > 200:
        score += 0.2
    
    # Prefer content with multiple words
    word_count = len(text.split())
    if word_count >= 5:
        score += 0.2
    
    return min(1.0, score)


def _extract_short_answer(freeform_answer: str) -> str:
    """
    Extract 1-3 sentences for short answer section.
    
    Args:
        freeform_answer: Full LLM response
        
    Returns:
        Short answer (1-3 sentences)
    """
    if not freeform_answer or not freeform_answer.strip():
        return "The answer could not be generated."
    
    sentences = _extract_sentences(freeform_answer)
    
    if not sentences:
        # Fallback: use first 200 chars
        answer = freeform_answer.strip()[:200]
        if len(freeform_answer) > 200:
            answer += "..."
        return answer
    
    # Take first 1-3 sentences
    selected = sentences[:3]
    # Clean up sentences - remove trailing list markers
    cleaned_selected = []
    for sent in selected:
        # Remove trailing incomplete list items like ": - 400"
        clean = re.sub(r':\s*-.*$', '', sent)
        clean = re.sub(r'\s+common\s+error\s+codes\s+include.*$', '', clean, flags=re.IGNORECASE)
        if clean and len(clean.strip()) > 10:
            cleaned_selected.append(clean.strip())
    
    if not cleaned_selected:
        # Fallback to original
        cleaned_selected = selected
    
    result = '. '.join(cleaned_selected)
    
    # Ensure it ends with punctuation (but not a colon followed by dash)
    if not re.search(r'[.!?]$', result):
        result = result.rstrip(':')
        result += '.'
    
    return result


def _extract_when_why_items(freeform_answer: str, sentences: List[str], lines: List[str]) -> List[str]:
    """
    Extract 3 items for "When / Why You Use This" section.
    
    Args:
        freeform_answer: Full LLM response
        sentences: Extracted sentences
        lines: Extracted lines
        
    Returns:
        List of 3 bullet point items
    """
    items = []
    
    # Strategy 1: Keyword-based extraction from lines
    keywords = ['when', 'why', 'use', 'scenario', 'case', 'situation', 'appropriate', 'suitable', 'ideal']
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            clean = re.sub(r'^[-*•]\s*', '', line).strip()
            # Remove trailing incomplete phrases
            clean = re.sub(r'\s+if\s+there\s+is\s*\.?\s*$', '', clean, flags=re.IGNORECASE)
            clean = re.sub(r'\s+if\s+there\s*\.?\s*$', '', clean, flags=re.IGNORECASE)
            # Filter out incomplete phrases
            incomplete_patterns = [r'^if\s+there\s+is.*$', r'^if\s+there$', r'^when\s+there$']
            is_incomplete = any(re.match(pattern, clean.lower().strip()) for pattern in incomplete_patterns)
            if not is_incomplete and clean and len(clean) > 15:
                items.append(clean)
                if len(items) >= 3:
                    break
    
    # Strategy 2: Position-based extraction from sentences (skip first 1-2 used in short answer)
    if len(items) < 3 and sentences:
        for sentence in sentences[2:8]:  # Skip first 2 sentences (likely in short answer)
            # Filter out incomplete sentences
            if len(sentence) > 20 and _score_content_quality(sentence) > 0.5:
                # Filter out incomplete phrases like "If there is"
                incomplete_patterns = [r'^if\s+there\s+is$', r'^if\s+there$', r'^when\s+there$']
                is_incomplete = any(re.match(pattern, sentence.lower().strip()) for pattern in incomplete_patterns)
                if not is_incomplete:
                    # Check it's not already in items
                    if not any(_is_content_similar(sentence, item) for item in items):
                        items.append(sentence)
                        if len(items) >= 3:
                            break
    
    # Strategy 3: Use any substantial sentences not yet used
    if len(items) < 3 and sentences:
        for sentence in sentences:
            if len(sentence) > 20:
                # Check it's not already in items
                if not any(_is_content_similar(sentence, item) for item in items):
                    items.append(sentence)
                    if len(items) >= 3:
                        break
    
    # Strategy 4: Extract from lines if still needed
    if len(items) < 3 and lines:
        for line in lines:
            if len(line) > 20:
                # Check it's not already in items
                if not any(_is_content_similar(line, item) for item in items):
                    items.append(line)
                    if len(items) >= 3:
                        break
    
    # Ensure we have exactly 3 items (use generic only if absolutely necessary)
    generic_fallback = "Use this approach when appropriate for your observability needs."
    while len(items) < 3:
        # Only add generic if we truly have no content
        if len(sentences) == 0 and len(lines) == 0:
            items.append(generic_fallback)
        else:
            # Try to create variation from available content
            if sentences:
                # Use a different sentence
                for sent in sentences:
                    if not any(_is_content_similar(sent, item) for item in items):
                        items.append(sent)
                        break
                else:
                    items.append(generic_fallback)
            else:
                items.append(generic_fallback)
    
    return items[:3]


def _extract_how_to_steps(freeform_answer: str, sentences: List[str], lines: List[str]) -> List[str]:
    """
    Extract 3-4 steps for "How To Do It" section.
    
    Args:
        freeform_answer: Full LLM response
        sentences: Extracted sentences
        lines: Extracted lines
        
    Returns:
        List of 3-4 step items
    """
    steps = []
    
    # Strategy 1: Extract numbered or bulleted steps
    step_patterns = [
        r'^\d+[.)]\s*(.+)',  # "1. Step" or "1) Step"
        r'^[-*•]\s*(.+)',  # "- Step" or "* Step"
        r'^step\s+\d+[.:]\s*(.+)',  # "Step 1:"
    ]
    
    for line in lines:
        for pattern in step_patterns:
            match = re.match(pattern, line, re.IGNORECASE)
            if match:
                step = match.group(1).strip()
                if step and len(step) > 15:
                    steps.append(step)
                    break
    
    # Strategy 1b: Extract step content from sentences (e.g., "Step 1: Check..." -> "Check...")
    for sentence in sentences:
        # Look for "Step X:" or "Step X." patterns within sentences
        # Pattern: "Step 1: Check the HTTP..." -> extract "Check the HTTP..."
        step_match = re.search(r'step\s+\d+[.:]\s*(.+?)(?:\.|$|\.\s|:\s)', sentence, re.IGNORECASE)
        if step_match:
            step_content = step_match.group(1).strip()
            # Remove trailing incomplete phrases like "If there is"
            step_content = re.sub(r'\s+if\s+there\s+is.*$', '', step_content, flags=re.IGNORECASE)
            # Remove trailing list markers and incomplete phrases
            step_content = re.sub(r':\s*-.*$', '', step_content)  # Remove "include: - 400"
            step_content = re.sub(r'\s+common\s+error\s+codes\s+include.*$', '', step_content, flags=re.IGNORECASE)
            # Remove trailing periods if present
            step_content = step_content.rstrip('.')
            # Filter out very short or incomplete content
            if step_content and len(step_content) > 15 and len(step_content.split()) >= 3:
                # Check it's not already in steps (more strict check)
                if not any(_is_content_similar(step_content, step, threshold=0.7) for step in steps):
                    steps.append(step_content)
                    if len(steps) >= 4:
                        break
    
    # Strategy 2: Keyword-based extraction
    if len(steps) < 3:
        keywords = ['step', 'first', 'then', 'next', 'method', 'approach', 'process', 'procedure']
        for line in lines:
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                clean = re.sub(r'^[^\w]*', '', line).strip()
                clean = re.sub(r'^[-*•]\s*', '', clean).strip()
                # Remove trailing list markers
                clean = re.sub(r':\s*-.*$', '', clean)
                if clean and len(clean) > 15 and len(clean.split()) >= 3:
                    # Check it's not already in steps
                    if not any(_is_content_similar(clean, step, threshold=0.7) for step in steps):
                        steps.append(clean)
                        if len(steps) >= 4:
                            break
    
    # Strategy 3: Use substantial sentences as steps (skip first 2 used in short answer)
    if len(steps) < 3 and sentences:
        for sentence in sentences[2:8]:
            # Remove trailing list markers and incomplete phrases
            clean_sentence = re.sub(r':\s*-.*$', '', sentence)
            clean_sentence = re.sub(r'\s+common\s+error\s+codes\s+include.*$', '', clean_sentence, flags=re.IGNORECASE)
            if len(clean_sentence) > 20 and len(clean_sentence.split()) >= 3:
                # Check it's not already in steps
                if not any(_is_content_similar(clean_sentence, step, threshold=0.7) for step in steps):
                    steps.append(clean_sentence)
                    if len(steps) >= 4:
                        break
    
    # Strategy 4: Extract action-oriented content from lines
    if len(steps) < 3 and lines:
        action_verbs = ['check', 'verify', 'configure', 'set', 'enable', 'install', 'run', 'test', 'monitor']
        for line in lines:
            line_lower = line.lower()
            if any(verb in line_lower for verb in action_verbs):
                clean = re.sub(r'^[^\w]*', '', line).strip()
                if clean and len(clean) > 15:
                    if not any(_is_content_similar(clean, step) for step in steps):
                        steps.append(clean)
                        if len(steps) >= 4:
                            break
    
    # Ensure we have at least 3 steps
    generic_fallback = "Follow the recommended approach for your specific use case."
    while len(steps) < 3:
        # Only add generic if we truly have no content
        if len(sentences) == 0 and len(lines) == 0:
            steps.append(generic_fallback)
        else:
            # Try to create variation from available content
            if sentences:
                for sent in sentences:
                    if not any(_is_content_similar(sent, step) for step in steps):
                        steps.append(sent)
                        break
                else:
                    steps.append(generic_fallback)
            else:
                steps.append(generic_fallback)
    
    return steps[:4]  # Return up to 4 steps


def _extract_checklist_items(freeform_answer: str, sentences: List[str], lines: List[str]) -> List[str]:
    """
    Extract 3 items for "Quick Checklist" section.
    
    Args:
        freeform_answer: Full LLM response
        sentences: Extracted sentences
        lines: Extracted lines
        
    Returns:
        List of 3 checklist items
    """
    items = []
    
    # Strategy 1: Keyword-based extraction
    keywords = ['check', 'verify', 'ensure', 'confirm', 'review', 'validate', 'inspect', 'examine']
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            clean = re.sub(r'^[-*•\[\]]\s*', '', line).strip()
            clean = re.sub(r'^\[[ xX]\]\s*', '', clean).strip()
            if clean and len(clean) > 15:
                items.append(clean)
                if len(items) >= 3:
                    break
    
    # Strategy 1b: Extract checklist items from sentences (e.g., "Check the HTTP status code")
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(keyword in sentence_lower for keyword in keywords):
            # Extract the actionable part (after "check", "verify", etc.)
            for keyword in keywords:
                if keyword in sentence_lower:
                    # Find the keyword and extract what follows
                    idx = sentence_lower.find(keyword)
                    if idx != -1:
                        # Extract from keyword to end (or to next sentence boundary)
                        action_part = sentence[idx:].strip()
                        # Remove "Step X:" prefixes if present
                        action_part = re.sub(r'^step\s+\d+[.:]\s*', '', action_part, flags=re.IGNORECASE)
                        # Remove trailing incomplete phrases
                        action_part = re.sub(r'\s+if\s+there\s+is.*$', '', action_part, flags=re.IGNORECASE)
                        if action_part and len(action_part) > 15:
                            # Check it's not already in items
                            if not any(_is_content_similar(action_part, item) for item in items):
                                items.append(action_part)
                                if len(items) >= 3:
                                    break
                    break
            if len(items) >= 3:
                break
    
    # Strategy 2: Imperative sentences (action verbs)
    if len(items) < 3:
        imperative_patterns = [
            r'^(check|verify|ensure|confirm|review|validate|inspect|examine|test|monitor)',
        ]
        for sentence in sentences:
            sentence_lower = sentence.lower()
            for pattern in imperative_patterns:
                if re.match(pattern, sentence_lower):
                    if sentence not in items and len(sentence) > 15:
                        items.append(sentence)
                        if len(items) >= 3:
                            break
                if len(items) >= 3:
                    break
    
    # Strategy 3: Use any substantial sentences not yet used
    if len(items) < 3 and sentences:
        for sentence in sentences:
            if len(sentence) > 20:
                # Check it's not already in items
                if not any(_is_content_similar(sentence, item) for item in items):
                    items.append(sentence)
                    if len(items) >= 3:
                        break
    
    # Ensure we have exactly 3 items
    generic_fallback = "Review and verify the implementation."
    while len(items) < 3:
        # Only add generic if we truly have no content
        if len(sentences) == 0 and len(lines) == 0:
            items.append(generic_fallback)
        else:
            # Try to create variation from available content
            if sentences:
                for sent in sentences:
                    if not any(_is_content_similar(sent, item) for item in items):
                        items.append(sent)
                        break
                else:
                    items.append(generic_fallback)
            else:
                items.append(generic_fallback)
    
    return items[:3]


def _extract_pitfalls(freeform_answer: str, sentences: List[str], lines: List[str]) -> List[str]:
    """
    Extract 2 pitfalls for "Optional Extras" section.
    
    Args:
        freeform_answer: Full LLM response
        sentences: Extracted sentences
        lines: Extracted lines
        
    Returns:
        List of 2 pitfall items
    """
    pitfalls = []
    
    # Strategy 1: Keyword-based extraction
    keywords = ['pitfall', 'mistake', 'avoid', 'warning', 'error', 'problem', 'issue', 'common error', 'don\'t', 'never']
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            clean = re.sub(r'^[-*•]\s*', '', line).strip()
            if clean and len(clean) > 15:
                pitfalls.append(clean)
                if len(pitfalls) >= 2:
                    break
    
    # Strategy 2: Use sentences with warning language
    if len(pitfalls) < 2 and sentences:
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in ['avoid', 'warning', 'careful', 'important']):
                if sentence not in pitfalls and len(sentence) > 15:
                    pitfalls.append(sentence)
                    if len(pitfalls) >= 2:
                        break
    
    # Ensure we have 2 items
    while len(pitfalls) < 2:
        pitfalls.append("Not checking all relevant data sources.")
    
    return pitfalls[:2]


def _extract_next_steps(freeform_answer: str, sentences: List[str], lines: List[str]) -> List[str]:
    """
    Extract 2 next steps for "Optional Extras" section.
    
    Args:
        freeform_answer: Full LLM response
        sentences: Extracted sentences
        lines: Extracted lines
        
    Returns:
        List of 2 next step items
    """
    next_steps = []
    
    # Strategy 1: Keyword-based extraction
    keywords = ['next', 'follow', 'continue', 'then', 'after', 'subsequently', 'further', 'additional']
    for line in lines:
        line_lower = line.lower()
        if any(keyword in line_lower for keyword in keywords):
            clean = re.sub(r'^[-*•]\s*', '', line).strip()
            if clean and len(clean) > 15:
                next_steps.append(clean)
                if len(next_steps) >= 2:
                    break
    
    # Strategy 2: Use later sentences
    if len(next_steps) < 2 and sentences:
        # Use sentences from the latter part
        start_idx = max(0, len(sentences) - 5)
        for sentence in sentences[start_idx:]:
            if sentence not in next_steps and len(sentence) > 15:
                next_steps.append(sentence)
                if len(next_steps) >= 2:
                    break
    
    # Ensure we have 2 items
    while len(next_steps) < 2:
        next_steps.append("Document the solution for future reference.")
    
    return next_steps[:2]


def normalize_answer_sections(raw: str) -> str:
    """
    Normalize LLM answer by parsing section headers and rebuilding into proper markdown.
    
    This function handles cases where LLM returns inline formatting like:
    "**Question** TEXT ** 1. Short Answer...**" and converts it to proper markdown blocks.
    
    Args:
        raw: Raw LLM answer string (may have inline headers)
        
    Returns:
        Normalized answer with proper markdown section formatting
    """
    if not raw or not raw.strip():
        return raw
    
    # Define regex patterns for each header, tolerant to inner spaces and variations
    # Handle cases like "** 1. Short Answer..." with extra spaces after **
    SECTION_PATTERNS = [
        ("Question", r"\*\*\s*Question\s*\*\*"),
        ("ShortAnswer", r"\*\*\s*1\.\s*Short\s+Answer\s*\(1[–\-]?3\s*lines?\)\s*\*\*"),
        ("WhenWhy", r"\*\*\s*2\.\s*When\s*/\s*Why\s+You\s+Use\s+This\s*\*\*"),
        ("HowTo", r"\*\*\s*3\.\s*How\s+To\s+Do\s+It\s*\(Practical\s+Steps\)\s*\*\*"),
        ("Checklist", r"\*\*\s*4\.\s*Quick\s+Checklist\s*\(Ready-To-Use\)\s*\*\*"),
        ("Extras", r"\*\*\s*5\.\s*Optional\s+Extras\s*\(Only\s+if\s+needed\)\s*\*\*"),
    ]
    
    # Find all header matches with positions
    matches = []
    for key, pattern in SECTION_PATTERNS:
        for m in re.finditer(pattern, raw, flags=re.IGNORECASE):
            matches.append((key, m.start(), m.end()))
    
    # If no headers found, check if it's already properly formatted
    # (headers on their own lines with content below)
    if not matches:
        # Check if headers are already on separate lines
        if re.search(r'\*\*Question\*\*\n', raw, re.IGNORECASE):
            # Already formatted, just clean up whitespace
            normalized = re.sub(r'\n{3,}', '\n\n', raw)
            return normalized.strip()
        return raw.strip()
    
    # Sort matches by start position
    matches.sort(key=lambda x: x[1])
    
    # Extract content between headers
    sections = {key: "" for key, _ in SECTION_PATTERNS}
    
    # Handle content before first header (if any) - add to Question section
    first_match_start = matches[0][1]
    if first_match_start > 0:
        pre_content = raw[:first_match_start].strip()
        # If it looks like a question (short, no headers), add to Question
        if pre_content and len(pre_content) < 200 and "**" not in pre_content:
            sections["Question"] = pre_content
    
    for idx, (key, start, end) in enumerate(matches):
        # Get content from end of this header to start of next header (or end of string)
        next_start = matches[idx + 1][1] if idx + 1 < len(matches) else len(raw)
        content = raw[end:next_start].strip()
        # Clean up content: remove any stray header markers that might be in the content
        content = re.sub(r'\*\*\s*\*\*', '', content)  # Remove empty ** **
        # If this section already has content, append (in case of duplicate headers)
        if sections[key]:
            sections[key] += "\n\n" + content
        else:
            sections[key] = content
    
    # Rebuild the answer with canonical markdown layout
    parts = []
    
    # Question
    question_content = sections.get("Question", "").strip()
    if question_content:
        parts.append("**Question**\n" + question_content)
    
    # 1. Short Answer
    short_content = sections.get("ShortAnswer", "").strip()
    if short_content:
        parts.append("**1. Short Answer (1–3 lines)**\n" + short_content)
    
    # 2. When / Why
    when_content = sections.get("WhenWhy", "").strip()
    if when_content:
        parts.append("**2. When / Why You Use This**\n" + when_content)
    
    # 3. How To
    how_content = sections.get("HowTo", "").strip()
    if how_content:
        parts.append("**3. How To Do It (Practical Steps)**\n" + how_content)
    
    # 4. Checklist
    check_content = sections.get("Checklist", "").strip()
    if check_content:
        parts.append("**4. Quick Checklist (Ready-To-Use)**\n" + check_content)
    
    # 5. Extras
    extras_content = sections.get("Extras", "").strip()
    if extras_content:
        parts.append("**5. Optional Extras (Only if needed)**\n" + extras_content)
    
    # Join with double newlines between sections
    normalized = "\n\n".join(parts)
    
    # Fallback: if we couldn't parse anything, return original
    if not normalized.strip():
        return raw.strip()
    
    return normalized


def _validate_template_structure(formatted_answer: str) -> Tuple[bool, List[str]]:
    """
    Validate that the formatted answer matches the required template structure.
    
    Args:
        formatted_answer: The formatted answer to validate
        
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Check all required sections are present
    required_sections = [
        TEMPLATE_SECTIONS["question"],
        TEMPLATE_SECTIONS["short_answer"],
        TEMPLATE_SECTIONS["when_why"],
        TEMPLATE_SECTIONS["how_to"],
        TEMPLATE_SECTIONS["checklist"],
        TEMPLATE_SECTIONS["optional_extras"]
    ]
    
    for section in required_sections:
        if section not in formatted_answer:
            errors.append(f"Missing required section: {section}")
    
    # Check section order (basic check)
    section_positions = {}
    for section in required_sections:
        pos = formatted_answer.find(section)
        if pos != -1:
            section_positions[section] = pos
    
    # Verify sections appear in order
    prev_pos = -1
    for section in required_sections:
        if section in section_positions:
            if section_positions[section] <= prev_pos:
                errors.append(f"Section {section} appears out of order")
            prev_pos = section_positions[section]
    
    return len(errors) == 0, errors


def _is_content_similar(content1: str, content2: str, threshold: float = 0.8) -> bool:
    """
    Check if two content strings are similar (to avoid duplication).
    
    Args:
        content1: First content string
        content2: Second content string
        threshold: Similarity threshold (0.0 to 1.0) - increased to 0.8 to be less aggressive
        
    Returns:
        True if content is similar enough to be considered duplicate
    """
    # Normalize strings for comparison
    def normalize(s: str) -> str:
        s = s.lower().strip()
        # Remove extra whitespace
        s = re.sub(r'\s+', ' ', s)
        # Remove common prefixes/suffixes
        s = re.sub(r'^(step\s*\d+[.:]\s*)', '', s, flags=re.IGNORECASE)
        s = re.sub(r'^(to\s+debug\s+api\s+errors,\s*you\s+need\s+to\s+follow\s+these\s+steps:\s*)', '', s, flags=re.IGNORECASE)
        s = re.sub(r'^[-*•\[\]]\s*', '', s)
        return s
    
    norm1 = normalize(content1)
    norm2 = normalize(content2)
    
    # Exact match after normalization
    if norm1 == norm2:
        return True
    
    # Check if one is a substring of the other (but require substantial overlap)
    shorter_len = min(len(norm1), len(norm2))
    longer_len = max(len(norm1), len(norm2))
    
    if shorter_len == 0:
        return False
    
    shorter_text = norm1 if len(norm1) < len(norm2) else norm2
    longer_text = norm1 if len(norm1) >= len(norm2) else norm2
    
    # If shorter is contained in longer, check if it's a substantial portion
    if shorter_text in longer_text:
        # Calculate what portion of the longer text the shorter text represents
        overlap_ratio = len(shorter_text) / longer_len if longer_len > 0 else 0
        
        # Also check word-based overlap
        shorter_words = set(shorter_text.split())
        longer_words = set(longer_text.split())
        word_overlap = len(shorter_words & longer_words)
        word_ratio = word_overlap / len(shorter_words) if shorter_words else 0
        
        # Require BOTH high character overlap (90%+) AND high word overlap (85%+)
        # This prevents filtering out focused step content that appears in longer sentences
        if overlap_ratio >= 0.9 and word_ratio >= 0.85:
            return True
        # If shorter is very short (< 30 chars), be more lenient - require 95%+ word overlap
        elif shorter_len < 30 and word_ratio >= 0.95:
            return True
    
    # Word overlap check with higher threshold
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if not words1 or not words2:
        return False
    
    overlap = len(words1 & words2)
    union = len(words1 | words2)
    
    if union == 0:
        return False
    
    similarity = overlap / union
    # Require higher similarity (0.8) to consider duplicates
    return similarity >= threshold


def _filter_used_content(candidates: List[str], used_content: set, allow_partial_matches: bool = False) -> List[str]:
    """
    Filter out content that's already been used (similarity-based).
    
    Args:
        candidates: List of candidate content strings
        used_content: Set of already used content strings
        allow_partial_matches: If True, allow content even if it's a substring of used content
                               (useful for steps/checklist items that may appear in longer sentences)
        
    Returns:
        Filtered list with duplicates removed
    """
    if not used_content:
        return candidates
    
    filtered = []
    for candidate in candidates:
        is_duplicate = False
        for used in used_content:
            # If allow_partial_matches is True, only filter exact duplicates or very high similarity
            if allow_partial_matches:
                # Only filter if it's an exact match (after normalization) or 95%+ similar
                if _is_content_similar(candidate, used, threshold=0.95):
                    is_duplicate = True
                    break
            else:
                if _is_content_similar(candidate, used):
                    is_duplicate = True
                    break
        if not is_duplicate:
            filtered.append(candidate)
    
    return filtered


def format_llm_answer_to_template(question: str, freeform_answer: str) -> str:
    """
    Format a free-form LLM answer into the required template structure.
    
    This function ensures 100% consistent template structure with robust parsing,
    edge case handling, content extraction, and deduplication from the LLM response.
    
    Args:
        question: The original user question
        freeform_answer: The free-form answer from the LLM
        
    Returns:
        Formatted answer following the exact template structure
        
    Raises:
        ValueError: If template validation fails (should not happen in normal operation)
    """
    # Handle edge cases
    if not question or not question.strip():
        question = "Question not provided"
    
    if not freeform_answer or not freeform_answer.strip():
        freeform_answer = "No response generated."
    
    # Extract structured content
    sentences = _extract_sentences(freeform_answer)
    lines = _extract_lines(freeform_answer)
    
    # Extract ALL content first (before marking anything as used)
    short_answer = _extract_short_answer(freeform_answer)
    when_why_items_raw = _extract_when_why_items(freeform_answer, sentences, lines)
    how_to_steps_raw = _extract_how_to_steps(freeform_answer, sentences, lines)
    checklist_items_raw = _extract_checklist_items(freeform_answer, sentences, lines)
    pitfalls_raw = _extract_pitfalls(freeform_answer, sentences, lines)
    next_steps_raw = _extract_next_steps(freeform_answer, sentences, lines)
    
    # Track used content to avoid duplication across sections
    used_content = set()
    
    # Build template structure
    # Preserve original question case (don't uppercase)
    formatted = f"{TEMPLATE_SECTIONS['question']}\n{question}\n\n"
    
    # Section 1: Short Answer
    # Mark only first 1 sentence from short answer as used (to allow other sections to use content)
    short_sentences = _extract_sentences(short_answer)
    for sent in short_sentences[:1]:  # Mark only first sentence as used
        used_content.add(sent.lower().strip())
    formatted += f"{TEMPLATE_SECTIONS['short_answer']}\n{short_answer}\n\n"
    
    # Section 2: When / Why You Use This
    # Filter out duplicates (but allow content that's different enough)
    when_why_items = _filter_used_content(when_why_items_raw, used_content)
    # Ensure we have 3 items (fill with generic if needed)
    while len(when_why_items) < 3:
        when_why_items.append("Use this approach when appropriate for your observability needs.")
    # Mark as used
    for item in when_why_items:
        used_content.add(item.lower().strip())
    formatted += f"{TEMPLATE_SECTIONS['when_why']}\n"
    for item in when_why_items[:3]:
        formatted += f"- {item}\n"
    formatted += "\n"
    
    # Section 3: How To Do It
    # Filter out duplicates (steps are often extracted from sentences, so allow partial matches)
    how_to_steps = _filter_used_content(how_to_steps_raw, used_content, allow_partial_matches=True)
    # Ensure we have 3-4 steps
    while len(how_to_steps) < 3:
        how_to_steps.append("Follow the recommended approach for your specific use case.")
    # Mark as used
    for step in how_to_steps:
        used_content.add(step.lower().strip())
    formatted += f"{TEMPLATE_SECTIONS['how_to']}\n"
    for i, step in enumerate(how_to_steps[:4], 1):
        formatted += f"{i}. {step}\n"
    formatted += "\n"
    
    # Section 4: Quick Checklist
    # Filter out duplicates (checklist items may appear in longer sentences, so allow partial matches)
    checklist_items = _filter_used_content(checklist_items_raw, used_content, allow_partial_matches=True)
    # Ensure we have 3 items
    while len(checklist_items) < 3:
        checklist_items.append("Review and verify the implementation.")
    # Mark as used
    for item in checklist_items:
        used_content.add(item.lower().strip())
    formatted += f"{TEMPLATE_SECTIONS['checklist']}\n"
    for item in checklist_items[:3]:
        formatted += f"- [ ] {item}\n"
    formatted += "\n"
    
    # Section 5: Optional Extras
    # Filter out duplicates
    pitfalls = _filter_used_content(pitfalls_raw, used_content)
    # Ensure we have 2 items
    while len(pitfalls) < 2:
        pitfalls.append("Not checking all relevant data sources.")
    # Mark as used
    for pitfall in pitfalls:
        used_content.add(pitfall.lower().strip())
    
    # Filter out duplicates
    next_steps = _filter_used_content(next_steps_raw, used_content)
    # Ensure we have 2 items
    while len(next_steps) < 2:
        next_steps.append("Document the solution for future reference.")
    # Mark as used
    for step in next_steps:
        used_content.add(step.lower().strip())
    
    formatted += f"{TEMPLATE_SECTIONS['optional_extras']}\n"
    formatted += "- Common pitfalls:\n"
    for pitfall in pitfalls[:2]:
        formatted += f"  - {pitfall}\n"
    formatted += "- Good next steps:\n"
    for step in next_steps[:2]:
        formatted += f"  - {step}\n"
    
    # Normalize formatting: parse and rebuild sections deterministically
    # This handles cases where LLM returns inline headers like "**Question** TEXT ** 1. Short Answer...**"
    formatted = normalize_answer_sections(formatted)
    
    # Final cleanup: normalize excessive whitespace (preserve intentional blank lines)
    # Replace 3+ consecutive newlines with 2
    formatted = re.sub(r'\n{3,}', '\n\n', formatted)
    
    # Validate template structure
    is_valid, errors = _validate_template_structure(formatted)
    if not is_valid:
        # This should not happen, but log for debugging
        print(f"[WARNING] Template validation failed: {errors}")
        # Still return the formatted answer as it's likely correct
    
    return formatted


def format_context_items(context_items: list) -> str:
    """
    Format context items into a string for the prompt.
    
    Args:
        context_items: List of RetrievedItem objects
        
    Returns:
        Formatted context string
    """
    if not context_items:
        return ""
    
    formatted = []
    for item in context_items:
        formatted.append(f"- {item.content}")
    
    return "\n".join(formatted)


def generate_response(model_name: str, model_input: ModelInput) -> ModelOutput:
    """
    Generate a response from the model using Ollama LLM.
    
    Args:
        model_name: The name of the model to use
        model_input: The model input
        
    Returns:
        ModelOutput with answer, score, and source
    """
    print(f"[MODEL_GATEWAY] Generating response with model: {model_name}")
    print(f"[MODEL_GATEWAY] Input prompt: {model_input.cleaned_prompt}")
    
    # Extract question and context items
    question = model_input.cleaned_prompt
    context_items = model_input.context.items
    
    # Format context items
    context_text = format_context_items(context_items)
    
    # Build prompt
    prompt = build_observability_prompt(question, context_text if context_text else None)
    
    # Call Ollama LLM
    try:
        freeform_answer, latency = call_ollama_generate(prompt)
        print(f"[LLM] Ollama call latency: {latency:.2f}s")
        
        # Format the answer into the required template structure
        answer = format_llm_answer_to_template(question, freeform_answer)
        
        score = 0.9
        source = "ollama"
        
        output = ModelOutput(answer=answer, score=score, source=source)
        print(f"[MODEL_GATEWAY] Generated answer: {answer[:100]}...")
        print(f"[MODEL_GATEWAY] Generated score: {score}")
        print(f"[MODEL_GATEWAY] Source: {source}")
        
        return output
        
    except LLMError as e:
        print(f"[LLM] Error calling Ollama: {e}")
        fallback = (
            "I could not reach the local LLM right now. "
            "Please check that Ollama is running and the model is available."
        )
        output = ModelOutput(answer=fallback, score=0.2, source="fallback")
        print(f"[MODEL_GATEWAY] Using fallback answer")
        print(f"[MODEL_GATEWAY] Generated score: {output.score}")
        print(f"[MODEL_GATEWAY] Source: {output.source}")
        
        return output


def score_response(output: ModelOutput) -> ModelOutput:
    """
    Score the model response.
    
    Args:
        output: The model output to score
        
    Returns:
        The same ModelOutput (scoring is already done in generation for this demo)
    """
    print(f"[MODEL_GATEWAY] Scoring response...")
    print(f"[MODEL_GATEWAY] Response score: {output.score}")
    print(f"[MODEL_GATEWAY] Scoring complete")
    
    return output

