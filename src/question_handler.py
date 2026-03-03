"""
CCNA Netacad Auto-Solver — Question Handler
Detects question types and selects correct answers on the page.
"""

import re
import time
from .matcher import find_answer_for_option


def detect_question_type(page):
    """
    Detect the type of question currently displayed.
    
    Returns:
        'radio' - single choice (radio buttons)
        'checkbox' - multiple choice (checkboxes)
        'matching' - drag-and-drop matching
        'unknown' - could not determine
    """
    try:
        q_type = page.evaluate("""() => {
            const radios = document.querySelectorAll('input[type="radio"]');
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            const dragItems = document.querySelectorAll('.drag-item, .draggable, [draggable="true"]');
            const matchItems = document.querySelectorAll('.matching-item, .match-item, .category');
            
            if (radios.length > 0) return 'radio';
            if (checkboxes.length > 0) return 'checkbox';
            if (dragItems.length > 0 || matchItems.length > 0) return 'matching';
            return 'unknown';
        }""")
        return q_type
    except Exception:
        return 'unknown'


def get_question_text(page):
    """Extract the current question text from the page."""
    try:
        text = page.evaluate("""() => {
            // Try common question selectors
            const selectors = [
                '.question-text',
                '.question-content',
                '.quiz-question',
                'h3',
                '.question',
                'p'
            ];
            
            for (const sel of selectors) {
                const elem = document.querySelector(sel);
                if (elem && elem.innerText.trim().length > 20) {
                    return elem.innerText.trim();
                }
            }
            
            // Fallback: get all visible text
            return document.body.innerText.substring(0, 3000);
        }""")
        return text
    except Exception:
        return ""


def get_options(page):
    """Get all answer options with their text and element info."""
    try:
        options = page.evaluate("""() => {
            const results = [];
            
            // Try radio buttons
            const radios = document.querySelectorAll('input[type="radio"]');
            if (radios.length > 0) {
                radios.forEach((radio, idx) => {
                    const label = radio.closest('label') || 
                                  document.querySelector(`label[for="${radio.id}"]`) ||
                                  radio.parentElement;
                    const text = label ? label.innerText.trim() : '';
                    results.push({
                        index: idx,
                        text: text,
                        type: 'radio',
                        id: radio.id || '',
                        checked: radio.checked
                    });
                });
                return results;
            }
            
            // Try checkboxes
            const checkboxes = document.querySelectorAll('input[type="checkbox"]');
            if (checkboxes.length > 0) {
                checkboxes.forEach((cb, idx) => {
                    const label = cb.closest('label') || 
                                  document.querySelector(`label[for="${cb.id}"]`) ||
                                  cb.parentElement;
                    const text = label ? label.innerText.trim() : '';
                    results.push({
                        index: idx,
                        text: text,
                        type: 'checkbox',
                        id: cb.id || '',
                        checked: cb.checked
                    });
                });
                return results;
            }
            
            return results;
        }""")
        return options
    except Exception:
        return []


def select_answer(page, option_index, option_type='radio'):
    """Click on a specific answer option by index."""
    try:
        page.evaluate(f"""(data) => {{
            const inputs = document.querySelectorAll('input[type="{data.type}"]');
            if (inputs[data.index]) {{
                inputs[data.index].click();
                // Also try clicking the label
                const label = inputs[data.index].closest('label') || 
                              document.querySelector('label[for="' + inputs[data.index].id + '"]');
                if (label) label.click();
            }}
        }}""", {'index': option_index, 'type': option_type})
        return True
    except Exception:
        return False


def click_submit(page):
    """Find and click the Submit/Next button."""
    try:
        clicked = page.evaluate("""() => {
            // Try various submit button selectors
            const selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button.submit',
                'button.next',
                '.submit-btn',
                '.next-btn',
                'button:has-text("Submit")',
                'button:has-text("Next")',
                'button:has-text("Check")',
            ];
            
            // Try text-based search
            const buttons = document.querySelectorAll('button, input[type="submit"], input[type="button"], a.btn');
            for (const btn of buttons) {
                const text = btn.innerText || btn.value || '';
                if (text.match(/submit|next|check|continue/i)) {
                    btn.click();
                    return true;
                }
            }
            
            // Try selector-based search
            for (const sel of selectors) {
                try {
                    const elem = document.querySelector(sel);
                    if (elem) {
                        elem.click();
                        return true;
                    }
                } catch(e) {}
            }
            
            return false;
        }""")
        return clicked
    except Exception:
        return False


def answer_question(page, answer_data):
    """
    Answer a question on the page using the matched answer data.
    
    Args:
        page: Playwright page object
        answer_data: Dict with 'correct_answers', 'type' keys
    
    Returns:
        True if answered successfully
    """
    options = get_options(page)
    
    if not options:
        return False
    
    correct_answers = answer_data.get('correct_answers', [])
    
    if not correct_answers:
        return False
    
    selected_count = 0
    
    for option in options:
        option_text = option.get('text', '')
        if not option_text:
            continue
        
        if find_answer_for_option(option_text, correct_answers):
            success = select_answer(page, option['index'], option['type'])
            if success:
                selected_count += 1
                time.sleep(0.3)  # Small delay between selections
    
    return selected_count > 0


def get_question_info(page):
    """Get comprehensive info about the current question state."""
    try:
        info = page.evaluate("""() => {
            const body = document.body.innerText;
            
            // Try to find question number indicator
            const numMatch = body.match(/(\\d+)\\s+of\\s+(\\d+)/i);
            
            return {
                bodyText: body.substring(0, 4000),
                questionNum: numMatch ? parseInt(numMatch[1]) : -1,
                totalQuestions: numMatch ? parseInt(numMatch[2]) : -1,
                hasSubmitButton: !!document.querySelector('button, input[type="submit"]'),
                url: window.location.href
            };
        }""")
        return info
    except Exception:
        return {'bodyText': '', 'questionNum': -1, 'totalQuestions': -1}
