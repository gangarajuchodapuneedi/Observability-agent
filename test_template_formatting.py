"""Comprehensive unit tests for template formatting system."""

import unittest
from src.model_gateway import (
    format_llm_answer_to_template,
    _validate_template_structure,
    _extract_sentences,
    _extract_lines,
    _extract_short_answer,
    _extract_when_why_items,
    _extract_how_to_steps,
    _extract_checklist_items,
    _extract_pitfalls,
    _extract_next_steps,
    TEMPLATE_SECTIONS
)


class TestTemplateFormatting(unittest.TestCase):
    """Test cases for template formatting functionality."""
    
    def test_normal_response_with_good_content(self):
        """Test formatting with a normal, well-structured response."""
        question = "How do I use distributed tracing?"
        answer = """Distributed tracing helps you track requests across services. 
        You should use it when you have microservices. First, instrument your services. 
        Then configure the tracing backend. Check the trace IDs in logs. 
        Avoid sampling too aggressively. Next, set up alerting."""
        
        result = format_llm_answer_to_template(question, answer)
        
        # Validate structure
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Check all sections are present
        self.assertIn(TEMPLATE_SECTIONS["question"], result)
        self.assertIn(TEMPLATE_SECTIONS["short_answer"], result)
        self.assertIn(TEMPLATE_SECTIONS["when_why"], result)
        self.assertIn(TEMPLATE_SECTIONS["how_to"], result)
        self.assertIn(TEMPLATE_SECTIONS["checklist"], result)
        self.assertIn(TEMPLATE_SECTIONS["optional_extras"], result)
        
        # Check question is included
        self.assertIn(question, result)
    
    def test_short_response(self):
        """Test formatting with a very short response (< 50 chars)."""
        question = "What is logging?"
        answer = "Logging records events."
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # All sections should still be present
        self.assertIn(TEMPLATE_SECTIONS["short_answer"], result)
        self.assertIn(TEMPLATE_SECTIONS["when_why"], result)
        self.assertIn(TEMPLATE_SECTIONS["how_to"], result)
    
    def test_empty_response(self):
        """Test formatting with empty response."""
        question = "What is monitoring?"
        answer = ""
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Should still have all sections
        self.assertIn(TEMPLATE_SECTIONS["question"], result)
        self.assertIn(TEMPLATE_SECTIONS["short_answer"], result)
    
    def test_whitespace_only_response(self):
        """Test formatting with whitespace-only response."""
        question = "What is observability?"
        answer = "   \n\t  \n  "
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
    
    def test_single_sentence_response(self):
        """Test formatting with single sentence response."""
        question = "What are metrics?"
        answer = "Metrics are numerical measurements of system behavior."
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Should extract the sentence
        self.assertIn("Metrics are numerical", result)
    
    def test_response_with_no_relevant_keywords(self):
        """Test formatting with response that has no relevant keywords."""
        question = "What is APM?"
        answer = "Application Performance Monitoring tracks application performance. It provides insights. Data collection happens automatically. Analysis reveals patterns. Reporting shows trends."
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Should still extract content using position-based strategy
        self.assertIn(TEMPLATE_SECTIONS["when_why"], result)
        self.assertIn(TEMPLATE_SECTIONS["how_to"], result)
    
    def test_response_with_markdown_formatting(self):
        """Test formatting with markdown-heavy response."""
        question = "How do I set up alerts?"
        answer = """**Alerting** is important. 
        *First* step: Configure thresholds.
        `Check` the metrics.
        ## Setup Process
        1. Define rules
        2. Set notifications"""
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Markdown should be cleaned from extracted content
        self.assertIn(TEMPLATE_SECTIONS["short_answer"], result)
    
    def test_very_long_response(self):
        """Test formatting with very long response."""
        question = "What is observability?"
        answer = "Observability is " + "a very detailed explanation. " * 50
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Should handle long content gracefully
        self.assertIn(TEMPLATE_SECTIONS["short_answer"], result)
    
    def test_response_with_special_characters(self):
        """Test formatting with special characters."""
        question = "What about errors?"
        answer = "Errors occur when: 1) System fails, 2) Network issues, 3) Timeouts! Check logs? Yes! Avoid: mistakes & errors."
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
    
    def test_response_with_numbered_steps(self):
        """Test extraction of numbered steps."""
        question = "How to debug?"
        answer = """Debugging process:
        1. Reproduce the issue
        2. Check logs
        3. Analyze stack traces
        4. Fix the problem"""
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Should extract numbered steps
        self.assertIn("1.", result)
        self.assertIn("2.", result)
        self.assertIn("3.", result)
    
    def test_response_with_bullet_points(self):
        """Test extraction of bullet points."""
        question = "What to check?"
        answer = """Check these items:
        - Logs
        - Metrics
        - Traces"""
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
    
    def test_empty_question(self):
        """Test with empty question."""
        question = ""
        answer = "This is an answer."
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
    
    def test_single_word_answer(self):
        """Test with single word answer."""
        question = "What is it?"
        answer = "Monitoring"
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
    
    def test_response_with_no_sentence_boundaries(self):
        """Test with response that has no sentence boundaries."""
        question = "What is it?"
        answer = "This is a response with no periods or question marks or exclamation points"
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
    
    def test_response_with_keywords_for_all_sections(self):
        """Test with response containing keywords for all sections."""
        question = "How to monitor?"
        answer = """Monitoring is essential. Use it when you need visibility. 
        First step: Set up agents. Then configure dashboards. 
        Check metrics regularly. Verify alerts work. 
        Common mistake: Too many alerts. Avoid alert fatigue.
        Next: Optimize thresholds. Follow best practices."""
        
        result = format_llm_answer_to_template(question, answer)
        
        is_valid, errors = _validate_template_structure(result)
        self.assertTrue(is_valid, f"Template validation failed: {errors}")
        
        # Should extract content for all sections
        self.assertIn("Use it when", result)
        self.assertIn("Set up agents", result)
        self.assertIn("Check metrics", result)


class TestHelperFunctions(unittest.TestCase):
    """Test helper functions for text extraction."""
    
    def test_extract_sentences_normal(self):
        """Test sentence extraction from normal text."""
        text = "First sentence with enough words. Second sentence with enough words! Third sentence with enough words?"
        sentences = _extract_sentences(text)
        self.assertEqual(len(sentences), 3)
        self.assertIn("First sentence", sentences[0])
    
    def test_extract_sentences_empty(self):
        """Test sentence extraction from empty text."""
        sentences = _extract_sentences("")
        self.assertEqual(len(sentences), 0)
    
    def test_extract_sentences_no_punctuation(self):
        """Test sentence extraction with no punctuation."""
        text = "This is a sentence with no punctuation"
        sentences = _extract_sentences(text)
        self.assertGreater(len(sentences), 0)
    
    def test_extract_lines_normal(self):
        """Test line extraction from normal text."""
        text = "This is line one with enough characters\nThis is line two with enough characters\nThis is line three with enough characters"
        lines = _extract_lines(text)
        self.assertEqual(len(lines), 3)
    
    def test_extract_lines_empty(self):
        """Test line extraction from empty text."""
        lines = _extract_lines("")
        self.assertEqual(len(lines), 0)
    
    def test_extract_short_answer_normal(self):
        """Test short answer extraction."""
        answer = "First sentence. Second sentence. Third sentence. Fourth sentence."
        short = _extract_short_answer(answer)
        self.assertIn("First sentence", short)
        self.assertIn("Second sentence", short)
    
    def test_extract_short_answer_empty(self):
        """Test short answer extraction from empty text."""
        short = _extract_short_answer("")
        self.assertIn("could not be generated", short)
    
    def test_extract_when_why_items(self):
        """Test when/why items extraction."""
        answer = "Use this when needed. Why use it? Scenario applies. Case study."
        sentences = _extract_sentences(answer)
        lines = _extract_lines(answer)
        items = _extract_when_why_items(answer, sentences, lines)
        self.assertEqual(len(items), 3)
    
    def test_extract_how_to_steps(self):
        """Test how-to steps extraction."""
        answer = "Step 1: Do this. Step 2: Do that. First, prepare. Then execute."
        sentences = _extract_sentences(answer)
        lines = _extract_lines(answer)
        steps = _extract_how_to_steps(answer, sentences, lines)
        self.assertGreaterEqual(len(steps), 3)
        self.assertLessEqual(len(steps), 4)
    
    def test_extract_checklist_items(self):
        """Test checklist items extraction."""
        answer = "Check logs. Verify metrics. Ensure alerts work. Review dashboards."
        sentences = _extract_sentences(answer)
        lines = _extract_lines(answer)
        items = _extract_checklist_items(answer, sentences, lines)
        self.assertEqual(len(items), 3)
    
    def test_extract_pitfalls(self):
        """Test pitfalls extraction."""
        answer = "Common mistake: Wrong config. Avoid this pitfall. Warning: Don't do this."
        sentences = _extract_sentences(answer)
        lines = _extract_lines(answer)
        pitfalls = _extract_pitfalls(answer, sentences, lines)
        self.assertEqual(len(pitfalls), 2)
    
    def test_extract_next_steps(self):
        """Test next steps extraction."""
        answer = "Next, configure. Then follow up. After that, verify. Continue monitoring."
        sentences = _extract_sentences(answer)
        lines = _extract_lines(answer)
        steps = _extract_next_steps(answer, sentences, lines)
        self.assertEqual(len(steps), 2)


class TestTemplateValidation(unittest.TestCase):
    """Test template validation functionality."""
    
    def test_validate_correct_template(self):
        """Test validation of correctly formatted template."""
        template = f"""{TEMPLATE_SECTIONS['question']}
Test question

{TEMPLATE_SECTIONS['short_answer']}
Test answer

{TEMPLATE_SECTIONS['when_why']}
- Item 1
- Item 2
- Item 3

{TEMPLATE_SECTIONS['how_to']}
1. Step 1
2. Step 2
3. Step 3

{TEMPLATE_SECTIONS['checklist']}
- [ ] Item 1
- [ ] Item 2
- [ ] Item 3

{TEMPLATE_SECTIONS['optional_extras']}
- Common pitfalls:
  - Pitfall 1
  - Pitfall 2
- Good next steps:
  - Step 1
  - Step 2"""
        
        is_valid, errors = _validate_template_structure(template)
        self.assertTrue(is_valid, f"Validation failed: {errors}")
        self.assertEqual(len(errors), 0)
    
    def test_validate_missing_section(self):
        """Test validation detects missing section."""
        template = f"""{TEMPLATE_SECTIONS['question']}
Test question

{TEMPLATE_SECTIONS['short_answer']}
Test answer"""
        
        is_valid, errors = _validate_template_structure(template)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)


if __name__ == "__main__":
    unittest.main()

