import json
from difflib import get_close_matches
from typing import List, Optional
import os
import wolframalpha
import webbrowser

# Wolfram Alpha API setup
app_id = 'TTTH2G-K83HXKUXRH'  # Replace with your Wolfram Alpha App ID
client = wolframalpha.Client(app_id)

query_limit = 100  # Set your desired query limit

def load_knowledge_base(file_path: str) -> dict:
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data: dict = json.load(file)
    else:
        data = {"questions": []}
    return data

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def load_query_count(file_path: str) -> int:
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data: dict = json.load(file)
            return data.get("query_count", 0)
    else:
        return 0

def save_query_count(file_path: str, count: int):
    with open(file_path, 'w') as file:
        json.dump({"query_count": count}, file, indent=2)

def find_best_match(user_question: str, questions: List[str]) -> Optional[str]:
    matches: List[str] = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict, query_count: int) -> Optional[str]:
    for q in knowledge_base["questions"]:
        if q["question"] == question:
            return q["answer"]

    if query_count < query_limit:
        # If question not found, query Wolfram Alpha
        res = client.query(question)
        try:
            answer = next(res.results).text
            return answer
        except StopIteration:
            return None
    else:
        return "Query limit reached. Please try again later."

def google_search(query: str) -> Optional[str]:
    try:
        search_url = f"https://www.google.com/search?q={query}"
        return search_url
    except Exception as e:
        print(f"Error occurred during Google search: {e}")
        return None

def open_google_search(query: str) -> str:
    search_url = google_search(query)
    if search_url:
        webbrowser.open_new_tab(search_url)
        return "I found this information online."
    else:
        return "Sorry, I couldn't perform the Google search."

def chat_bot():
    knowledge_base_path = "knowledge_base.json"
    query_count_path = "query_count.json"

    knowledge_base: dict = load_knowledge_base(knowledge_base_path)
    query_count: int = load_query_count(query_count_path)

    while True:
        user_input: str = input('You: ')

        if user_input.lower() == 'quit':
            break

        # Check if user wants to search up something
        if "search up" in user_input.lower():
            search_query = user_input.lower().replace("search up", "").strip()
            google_result = open_google_search(search_query)
            print(f'ELEY: {google_result}')
        else:
            # Use Wolfram Alpha for other queries
            best_match: Optional[str] = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

            if best_match:
                answer: Optional[str] = get_answer_for_question(best_match, knowledge_base, query_count)
                print(f'ELEY: {answer}')
            else:
                print('ELEY: Loading...')
                answer = get_answer_for_question(user_input, knowledge_base, query_count)
                if answer:
                    print(f'ELEY: {answer}')
                    query_count += 1
                    save_query_count(query_count_path, query_count)
                else:
                    print('ELEY: Sorry, I couldn\'t find an answer for that.')

                # Optionally, you can prompt the user to teach the bot if Wolfram Alpha doesn't provide an answer
                # new_answer: str = input('Type the answer or "skip" to skip: ')
                # if new_answer.lower() != 'skip':
                #     knowledge_base["questions"].append({"question": user_input, "answer": new_answer})
                #     save_knowledge_base(knowledge_base_path, knowledge_base)
                #     print('ELEY: Thank you! I now know the answer.')

if __name__ == '__main__':
    chat_bot()