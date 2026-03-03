"""
CCNA Netacad Auto-Solver — Fuzzy Question Matcher
Matches test questions to answer key using text similarity.
"""

import re
import difflib


def clean_text(text):
    """Normalize text for comparison."""
    text = text.lower().strip()
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove common noise
    text = re.sub(r'\(choose \w+\.?\)', '', text)
    text = re.sub(r'\(not all options are used\.?\)', '', text)
    text = re.sub(r'refer to the exhibit\.?\s*', '', text)
    text = text.strip()
    return text


def get_keywords(text):
    """Extract significant keywords from text."""
    text = clean_text(text)
    # Remove very common words
    stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                  'should', 'may', 'might', 'must', 'shall', 'can', 'to', 'of', 'in',
                  'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
                  'during', 'before', 'after', 'above', 'below', 'between', 'that',
                  'this', 'these', 'those', 'it', 'its', 'what', 'which', 'who', 'whom',
                  'when', 'where', 'why', 'how', 'and', 'or', 'not', 'no', 'but', 'if'}
    
    words = text.split()
    keywords = [w for w in words if w not in stop_words and len(w) > 2]
    return keywords


def similarity_score(text1, text2):
    """Calculate similarity between two texts (0-1)."""
    clean1 = clean_text(text1)
    clean2 = clean_text(text2)
    
    # Direct sequence matching
    seq_score = difflib.SequenceMatcher(None, clean1, clean2).ratio()
    
    # Keyword overlap
    kw1 = set(get_keywords(text1))
    kw2 = set(get_keywords(text2))
    
    if kw1 and kw2:
        intersection = kw1 & kw2
        union = kw1 | kw2
        keyword_score = len(intersection) / len(union) if union else 0
    else:
        keyword_score = 0
    
    # Combined score (weighted)
    combined = (seq_score * 0.6) + (keyword_score * 0.4)
    
    return combined


def find_best_match(question_text, answer_key, threshold=0.35):
    """
    Find the best matching answer from the answer key for a given question.
    
    Args:
        question_text: The question text from the test
        answer_key: List of dicts from the scraper
        threshold: Minimum similarity score (0-1)
        
    Returns:
        Best matching answer dict, or None
    """
    best_match = None
    best_score = 0
    
    for answer in answer_key:
        score = similarity_score(question_text, answer['question'])
        
        if score > best_score:
            best_score = score
            best_match = answer
    
    if best_score >= threshold:
        return best_match, best_score
    
    return None, 0


def find_answer_for_option(option_text, correct_answers):
    """
    Check if an option text matches any of the correct answers.
    
    Args:
        option_text: Text of the option
        correct_answers: List of correct answer strings
        
    Returns:
        True if this option is correct
    """
    clean_option = clean_text(option_text)
    
    for correct in correct_answers:
        clean_correct = clean_text(correct)
        
        # Exact match
        if clean_option == clean_correct:
            return True
        
        # High similarity
        score = difflib.SequenceMatcher(None, clean_option, clean_correct).ratio()
        if score > 0.75:
            return True
        
        # One contains the other
        if len(clean_option) > 15 and len(clean_correct) > 15:
            if clean_option in clean_correct or clean_correct in clean_option:
                return True
        
        # First N characters match
        min_len = min(len(clean_option), len(clean_correct))
        check_len = min(min_len, 40)
        if check_len > 10 and clean_option[:check_len] == clean_correct[:check_len]:
            return True
    
    return False


if __name__ == '__main__':
    # Quick test
    answer_key = [
        {'question': 'Which information is used by routers to forward a data packet toward its destination?',
         'correct_answers': ['destination IP address'],
         'type': 'single'},
        {'question': 'What are two services provided by the OSI network layer?',
         'correct_answers': ['routing packets toward the destination', 'encapsulating PDUs from the transport layer'],
         'type': 'multiple_2'},
    ]
    
    test_q = "Which information is used by routers to forward data packets?"
    match, score = find_best_match(test_q, answer_key)
    
    if match:
        print(f"Match found! Score: {score:.2f}")
        print(f"Question: {match['question']}")
        print(f"Answers: {match['correct_answers']}")
    else:
        print("No match found")
