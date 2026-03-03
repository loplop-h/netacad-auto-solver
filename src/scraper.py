"""
CCNA Netacad Auto-Solver — Answer Scraper
Scrapes correct answers from ITExamAnswers.net
"""

import requests
import json
import os
import re
import hashlib
from bs4 import BeautifulSoup


CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "exams")


def get_cache_path(url):
    """Generate a cache file path based on URL hash."""
    url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
    safe_name = re.sub(r'[^a-zA-Z0-9]', '_', url.split('/')[-1].replace('.html', ''))[:50]
    return os.path.join(CACHE_DIR, f"{safe_name}_{url_hash}.json")


def scrape_answers(url, use_cache=True):
    """
    Scrape answers from an ITExamAnswers.net page.
    
    Args:
        url: URL of the ITExamAnswers page
        use_cache: Whether to use cached results
        
    Returns:
        List of dicts with 'question', 'answers', 'type' keys
    """
    # Check cache first
    cache_path = get_cache_path(url)
    if use_cache and os.path.exists(cache_path):
        print(f"  📦 Using cached answers from {os.path.basename(cache_path)}")
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    print(f"  🌐 Downloading answers from: {url}")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'lxml')
    
    questions = parse_questions(soup)
    
    # Save to cache
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(cache_path, 'w', encoding='utf-8') as f:
        json.dump(questions, f, ensure_ascii=False, indent=2)
    
    print(f"  ✅ Found {len(questions)} questions with answers")
    return questions


def parse_questions(soup):
    """Parse questions and correct answers from the page HTML."""
    questions = []
    
    # Find the main content area
    content = soup.find('div', class_='entry-content') or soup.find('article') or soup.find('div', class_='post-content')
    if not content:
        content = soup.body
    
    # Strategy: Find all text content and identify questions by numbered patterns
    # Questions are typically numbered (1., 2., etc.)
    # Correct answers are in red/bold or marked with specific styling
    
    all_elements = content.find_all(['p', 'li', 'div', 'span', 'strong', 'ul', 'ol'])
    
    current_question = None
    current_answers = []
    current_options = []
    question_number = 0
    
    # Get the full text content and process line by line
    full_text = content.get_text('\n', strip=False)
    lines = full_text.split('\n')
    
    # Also get HTML to detect red/colored text (correct answers)
    html_content = str(content)
    
    # Find correct answers by looking for red/colored text
    correct_answer_texts = set()
    
    # Look for text in red color (various patterns used by ITExamAnswers)
    for tag in content.find_all(True):
        style = tag.get('style', '')
        color_match = re.search(r'color\s*:\s*(#[0-9a-fA-F]{3,6}|red|rgb\([^)]*\))', style)
        
        is_correct = False
        if color_match:
            color = color_match.group(1).lower()
            # Red-ish colors indicate correct answers
            if color in ['red', '#ff0000', '#f00', '#ff0', '#cc0000', '#ee0000']:
                is_correct = True
            elif color.startswith('#'):
                # Check if it's a red-ish hex color
                hex_color = color.lstrip('#')
                if len(hex_color) == 3:
                    hex_color = ''.join([c*2 for c in hex_color])
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    if r > 180 and g < 100 and b < 100:
                        is_correct = True
            elif 'rgb' in color:
                rgb_match = re.search(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color)
                if rgb_match:
                    r, g, b = int(rgb_match.group(1)), int(rgb_match.group(2)), int(rgb_match.group(3))
                    if r > 180 and g < 100 and b < 100:
                        is_correct = True
        
        # Also check for class-based coloring
        classes = tag.get('class', [])
        if isinstance(classes, list):
            class_str = ' '.join(classes)
        else:
            class_str = str(classes)
        
        if 'correct' in class_str.lower() or 'right' in class_str.lower():
            is_correct = True
        
        if is_correct:
            text = tag.get_text(strip=True)
            if text and len(text) > 2:
                correct_answer_texts.add(text)
    
    # Also look for bold text within list items (another common pattern)
    for li in content.find_all('li'):
        strong = li.find('strong')
        if strong:
            strong_style = strong.get('style', '')
            if 'color' in strong_style:
                text = strong.get_text(strip=True)
                if text:
                    correct_answer_texts.add(text)
    
    # Look for specific patterns: text wrapped in <span> or <strong> with color
    for tag in content.find_all(['span', 'strong', 'b', 'em', 'p']):
        style = tag.get('style', '')
        if not style:
            # Check parent style
            parent = tag.parent
            if parent:
                style = parent.get('style', '')
        
        if 'color' in style.lower():
            text = tag.get_text(strip=True)
            if text and len(text) > 2:
                # Verify it's reddish
                color_match = re.search(r'color\s*:\s*(#[0-9a-fA-F]{3,6}|red)', style, re.IGNORECASE)
                if color_match:
                    correct_answer_texts.add(text)
    
    # Now parse questions from the text
    # Pattern: number followed by period or parenthesis
    question_pattern = re.compile(r'^(\d+)\.\s+(.+)')
    explanation_pattern = re.compile(r'^Explanation', re.IGNORECASE)
    
    i = 0
    processed_lines = [line.strip() for line in lines if line.strip()]
    
    while i < len(processed_lines):
        line = processed_lines[i]
        
        # Check if this is a question
        q_match = question_pattern.match(line)
        if q_match:
            # Save previous question
            if current_question and current_options:
                q_data = finalize_question(current_question, current_options, correct_answer_texts, question_number)
                if q_data:
                    questions.append(q_data)
            
            question_number = int(q_match.group(1))
            current_question = q_match.group(2).strip()
            current_options = []
            i += 1
            
            # Collect options until next question or explanation
            while i < len(processed_lines):
                next_line = processed_lines[i]
                
                # Stop if we hit another question
                if question_pattern.match(next_line):
                    break
                
                # Stop if we hit explanation
                if explanation_pattern.match(next_line):
                    # Skip explanation lines
                    i += 1
                    while i < len(processed_lines) and not question_pattern.match(processed_lines[i]):
                        i += 1
                    break
                
                # Check if it's a "Place the options" or "Match" instruction
                if next_line.startswith('Place the options') or next_line.startswith('Match'):
                    i += 1
                    continue
                
                # This is an option
                # Clean option text (remove leading dashes/bullets)
                option = re.sub(r'^[-–•]\s*', '', next_line).strip()
                if option and len(option) > 1:
                    current_options.append(option)
                
                i += 1
        else:
            i += 1
    
    # Don't forget the last question
    if current_question and current_options:
        q_data = finalize_question(current_question, current_options, correct_answer_texts, question_number)
        if q_data:
            questions.append(q_data)
    
    return questions


def finalize_question(question_text, options, correct_texts, q_number):
    """Determine correct answers for a question."""
    correct_answers = []
    all_options = []
    
    for option in options:
        is_correct = False
        clean_option = option.strip()
        
        # Check if this option text appears in the correct answer set
        for correct in correct_texts:
            # Exact match
            if clean_option == correct:
                is_correct = True
                break
            # Partial match (correct text contains option or vice versa)
            if len(clean_option) > 10:
                if clean_option in correct or correct in clean_option:
                    is_correct = True
                    break
                # Fuzzy: first 30 chars match
                if clean_option[:30].lower() == correct[:30].lower():
                    is_correct = True
                    break
        
        all_options.append(clean_option)
        if is_correct:
            correct_answers.append(clean_option)
    
    # If no correct answers found via color, the first option is often correct
    # (ITExamAnswers typically lists correct answer first)
    if not correct_answers and all_options:
        correct_answers = [all_options[0]]
    
    # Detect question type
    choose_match = re.search(r'\(Choose (\w+)\)', question_text, re.IGNORECASE)
    if choose_match:
        num_word = choose_match.group(1).lower()
        num_map = {'two': 2, 'three': 3, 'four': 4, 'five': 5, '2': 2, '3': 3, '4': 4, '5': 5}
        num_answers = num_map.get(num_word, 1)
        q_type = f'multiple_{num_answers}'
    elif 'match' in question_text.lower() or 'Place the options' in question_text:
        q_type = 'matching'
    else:
        q_type = 'single'
    
    return {
        'number': q_number,
        'question': question_text,
        'options': all_options,
        'correct_answers': correct_answers,
        'type': q_type
    }


if __name__ == '__main__':
    # Test with a sample URL
    import sys
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        url = "https://itexamanswers.net/ccna-1-v7-modules-8-10-communicating-between-networks-exam-answers.html"
    
    results = scrape_answers(url, use_cache=False)
    
    print(f"\n{'='*60}")
    print(f"Total questions found: {len(results)}")
    print(f"{'='*60}\n")
    
    for q in results[:10]:
        print(f"Q{q['number']}: {q['question'][:80]}...")
        print(f"  Type: {q['type']}")
        print(f"  Correct: {q['correct_answers'][:2]}")
        print()
