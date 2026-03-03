#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════╗
║     CCNA Netacad Auto-Solver  v1.0                       ║
║     Automatic test solver for Cisco Netacad               ║
║     Answers from ITExamAnswers.net                        ║
╚══════════════════════════════════════════════════════════╝

Usage:
    python solver.py

The program will:
  1. Ask for the ITExamAnswers URL (answer key)
  2. Scrape and parse correct answers
  3. Open a browser for you to log into Netacad
  4. Auto-solve the test questions
"""

import sys
import time
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.scraper import scrape_answers
from src.matcher import find_best_match, find_answer_for_option
from src.browser import BrowserController


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ██████╗ ██████╗ ███╗   ██╗ █████╗                        ║
║    ██╔════╝██╔════╝ ████╗  ██║██╔══██╗                       ║
║    ██║     ██║      ██╔██╗ ██║███████║                       ║
║    ██║     ██║      ██║╚██╗██║██╔══██║                       ║
║    ╚██████╗╚██████╗ ██║ ╚████║██║  ██║                       ║
║     ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝╚═╝  ╚═╝                     ║
║                                                              ║
║     🎯 Netacad Auto-Solver v1.0                              ║
║     📚 Automatic CCNA Test Solver                            ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def print_step(step_num, text):
    """Print a formatted step."""
    print(f"\n  {'━'*55}")
    print(f"  📌 Step {step_num}: {text}")
    print(f"  {'━'*55}")


def print_success(text):
    """Print a success message."""
    print(f"  ✅ {text}")


def print_error(text):
    """Print an error message."""
    print(f"  ❌ {text}")


def print_info(text):
    """Print an info message."""
    print(f"  ℹ️  {text}")


def print_progress(current, total, question_text=""):
    """Print progress bar."""
    bar_length = 30
    filled = int(bar_length * current / total) if total > 0 else 0
    bar = '█' * filled + '░' * (bar_length - filled)
    pct = (current / total * 100) if total > 0 else 0
    short_q = question_text[:50] + "..." if len(question_text) > 50 else question_text
    print(f"\r  [{bar}] {current}/{total} ({pct:.0f}%) {short_q}", end='', flush=True)


def solve_test(page, answer_key, browser):
    """
    Main solving loop - reads questions and selects correct answers.
    
    Args:
        page: Playwright page object
        answer_key: List of answer dicts from scraper
        browser: BrowserController instance
    """
    questions_answered = 0
    max_questions = 50  # Safety limit
    consecutive_failures = 0
    max_failures = 5
    
    print_info("Starting auto-solve...")
    print()
    
    while questions_answered < max_questions:
        # Check if test is complete
        if browser.is_test_complete():
            print()
            print_success(f"Test complete! Answered {questions_answered} questions.")
            break
        
        # Get current question text
        page_text = browser.get_page_text()
        
        if not page_text or len(page_text) < 20:
            time.sleep(2)
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                print()
                print_error("Could not read questions after multiple attempts.")
                break
            continue
        
        # Get question progress
        progress = browser.get_current_question_number()
        total = progress.get('total', -1)
        
        # Find matching answer
        match, score = find_best_match(page_text, answer_key)
        
        if match and score > 0.25:
            questions_answered += 1
            q_text = match['question'][:60]
            
            if total > 0:
                print_progress(questions_answered, total, q_text)
            else:
                print(f"  🔍 Q{questions_answered}: {q_text}... (match: {score:.0%})")
            
            correct_answers = match.get('correct_answers', [])
            
            # Try to click each correct answer
            selected = 0
            for answer in correct_answers:
                if browser.find_and_click_radio(answer):
                    selected += 1
                    time.sleep(0.3)
            
            if selected == 0:
                # Fallback: try clicking by text directly
                for answer in correct_answers:
                    if browser.find_and_click_text(answer[:60]):
                        selected += 1
                        time.sleep(0.3)
            
            if selected > 0:
                time.sleep(0.5)
                # Click Submit
                browser.click_submit_button()
                time.sleep(2)
                consecutive_failures = 0
            else:
                print(f"\n  ⚠️  Could not select answer for this question. Skipping...")
                consecutive_failures += 1
                # Try to move to next question
                browser.click_submit_button()
                time.sleep(2)
        else:
            consecutive_failures += 1
            if consecutive_failures >= max_failures:
                print()
                print_error("Could not match questions. The test may be finished or the answer key doesn't match.")
                break
            time.sleep(2)
    
    print()
    return questions_answered


def main():
    """Main entry point."""
    print(BANNER)
    
    # ═══════════════════════════════════════════
    # STEP 1: Get the answer URL
    # ═══════════════════════════════════════════
    print_step(1, "Enter the ITExamAnswers URL")
    print()
    print("  Examples:")
    print("  • https://itexamanswers.net/ccna-1-v7-modules-8-10-communicating-between-networks-exam-answers.html")
    print("  • https://itexamanswers.net/ccna-1-v7-modules-11-13-ip-addressing-exam-answers-full.html")
    print()
    
    answers_url = input("  📎 Answer key URL: ").strip()
    
    if not answers_url:
        print_error("No URL provided. Exiting.")
        return
    
    if not answers_url.startswith('http'):
        answers_url = 'https://' + answers_url
    
    # ═══════════════════════════════════════════
    # STEP 2: Scrape answers
    # ═══════════════════════════════════════════
    print_step(2, "Scraping answers")
    
    try:
        answer_key = scrape_answers(answers_url)
        print_success(f"Found {len(answer_key)} questions with answers")
        
        # Show preview
        print()
        print("  Preview of answers loaded:")
        for q in answer_key[:5]:
            ans_preview = q['correct_answers'][0][:50] if q['correct_answers'] else '???'
            print(f"    Q{q['number']}: {q['question'][:45]}... → {ans_preview}")
        if len(answer_key) > 5:
            print(f"    ... and {len(answer_key) - 5} more questions")
    
    except Exception as e:
        print_error(f"Failed to scrape answers: {e}")
        return
    
    # ═══════════════════════════════════════════
    # STEP 3: Open browser for login
    # ═══════════════════════════════════════════
    print_step(3, "Opening browser")
    
    browser = BrowserController(headless=False, slow_mo=300)
    
    try:
        page = browser.start()
        print_success("Browser launched successfully")
        
        # Navigate to Netacad
        print_info("Navigating to Netacad...")
        browser.navigate("https://www.netacad.com")
        
        # Wait for user to log in and navigate to test
        browser.wait_for_user_login()
        
        # ═══════════════════════════════════════════
        # STEP 4: Auto-solve the test
        # ═══════════════════════════════════════════
        print_step(4, "Auto-solving the test")
        
        questions_answered = solve_test(page, answer_key, browser)
        
        # ═══════════════════════════════════════════
        # RESULTS
        # ═══════════════════════════════════════════
        print()
        print("  " + "═"*55)
        print(f"  🏆 DONE! Answered {questions_answered} questions")
        print("  " + "═"*55)
        print()
        print("  The browser will stay open so you can review results.")
        print("  Press ENTER to close the browser and exit.")
        input()
    
    except KeyboardInterrupt:
        print("\n\n  Interrupted by user.")
    except Exception as e:
        print_error(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        browser.close()
        print_info("Browser closed. Goodbye! 👋")


if __name__ == '__main__':
    main()
