import json
import os
import random
import wolframalpha
import speech_recognition as sr
from difflib import get_close_matches
from typing import List, Optional
from gtts import gTTS
import playsound
import webbrowser

# Wolfram Alpha API setup
APP_ID = 'TTTH2G-K83HXKUXRH'  # Replace with your Wolfram Alpha App ID
client = wolframalpha.Client(APP_ID)

QUERY_LIMIT = 12  # Set your desired query limit

# Path configurations
KNOWLEDGE_BASE_PATH = "knowledge_base.json"
QUERY_COUNT_PATH = "query_count.json"

# Responses for small talk
THANK_YOU_RESPONSES = ["You're welcome!", "Glad I could help!", "Anytime!"]
GOODBYE_RESPONSES = ["Goodbye!", "See you later!", "Take care!"]
CONFUSED_RESPONSES = ["Sorry, I'm not sure what you mean.", "Could you rephrase that?", "I'm having trouble understanding."]
APOLOGY_RESPONSES = ["I apologize if I offended you.", "I'm sorry if my response was inappropriate.", "I didn't mean to upset you."]

# Jokes collection
JOKES = [
    "Why was the equal sign so humble? Because he knew he wasn't less than or greater than anyone else!",
    "Parallel lines have so much in common. It’s a shame they’ll never meet.",
    "Why do plants hate math? Because it gives them square roots!",
    "I would tell you a chemistry joke, but I know I wouldn't get a reaction.",
    "Why do biologists get invited to all the parties? Because they have good genes!",
    "What do you get when you mix sulfur, tungsten, and silver? SWAG!",
    "Why was the math book sad? It had too many problems.",
    "What did the biologist wear to impress their date? Designer genes!",
    "Why was the mole of oxygen molecules excited when he walked out of the singles bar? He got Avogadro's number!",
    "What do you call a tooth in a glass of water? A one molar solution!",
    "Why do programmers prefer dark mode? Because the light attracts bugs!",
    "Why did the physics teacher break up with the biology teacher? There was no chemistry.",
    "How many software engineers does it take to change a light bulb? None, that's a hardware issue.",
    "Why can't you trust an atom? Because they make up everything!",
    "What did one ion say to the other? I've got my ion you.",
    "Why did the computer keep sneezing? It had a virus!",
    "What did the biologist wear to impress their date? Designer genes!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "How does a scientist freshen their breath? With experi-mints!",
    "Why did the biology teacher go to jail? They were caught multiplying in public!"
]

OFFENSIVE_WORDS = ["mean", "swear", "offensive", "badword", "insult"]  # Example offensive words list

EMOTIONS_KEYWORDS = {
    "sad": ["sad", "unhappy", "depressed"],
    "bored": ["bored", "boring", "uninterested"],
    "happy": ["happy", "joy", "glad"]
}

def play_audio(audio_file: str):
    playsound.playsound(audio_file)

def load_knowledge_base(file_path: str) -> dict:
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    else:
        return {"questions": []}

def save_knowledge_base(file_path: str, data: dict):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=2)

def load_query_count(file_path: str) -> int:
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data.get("query_count", 0)
    else:
        return 0

def save_query_count(file_path: str, count: int):
    with open(file_path, 'w') as file:
        json.dump({"query_count": count}, file, indent=2)

def find_best_match(user_question: str, questions: List[str]) -> Optional[str]:
    matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
    return matches[0] if matches else None

def get_answer_for_question(question: str, knowledge_base: dict, query_count: int) -> Optional[str]:
    try:
        for q in knowledge_base["questions"]:
            if q["question"] == question:
                return q["answer"]

        if query_count < QUERY_LIMIT:
            # Query Wolfram Alpha
            res = client.query(question)
            try:
                answer = next(res.results).text
                return answer
            except StopIteration:
                return None
        else:
            return "Query limit reached. Please try again later."
    except Exception as e:
        print(f"Error occurred: {e}")
        return None

def google_search(query: str) -> Optional[str]:
    try:
        search_url = f"https://www.google.com/search?q={query}"
        return search_url
    except Exception as e:
        print(f"Error occurred during Google search: {e}")
        return None

def open_google_search(query: str) -> Optional[str]:
    search_url = google_search(query)
    if search_url:
        webbrowser.open_new_tab(search_url)
        return "I found this information online."
    else:
        return "Sorry, I couldn't perform the Google search."

def get_speech_input() -> str:
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("ELEY: Listening...")
        audio = recognizer.listen(source)
        try:
            user_input = recognizer.recognize_google(audio)
            print(f"You: {user_input}")
            return user_input.lower()
        except sr.UnknownValueError:
            print("ELEY: Sorry, I did not understand that.")
            return ""
        except sr.RequestError:
            print("ELEY: Could not request results from the recognizer service.")
            return ""

def text_to_speech(text: str, file_name: str):
    tts = gTTS(text=text, lang='en')
    tts.save(file_name)

def tell_joke() -> str:
    return random.choice(JOKES)

def detect_emotion(user_input: str) -> Optional[str]:
    for emotion, keywords in EMOTIONS_KEYWORDS.items():
        if any(keyword in user_input.lower() for keyword in keywords):
            return emotion
    return None

def respond_to_emotion(emotion: str) -> str:
    if emotion == "sad":
        return "I'm sorry to hear that. Is there something specific you'd like to talk about?"
    elif emotion == "bored":
        return "Here are a few things you could try: read a book, watch a movie, or try a new hobby."
    else:
        return "I'm here to chat! What's on your mind?"

def chat_bot():
    knowledge_base = load_knowledge_base(KNOWLEDGE_BASE_PATH)
    query_count = load_query_count(QUERY_COUNT_PATH)

    while True:
        user_input = get_speech_input()

        if user_input.lower() == 'quit':
            response = random.choice(GOODBYE_RESPONSES)
            text_to_speech(response, "response.mp3")
            play_audio("response.mp3")
            break

        if "thank you" in user_input.lower():
            response = random.choice(THANK_YOU_RESPONSES)
            text_to_speech(response, "response.mp3")
            play_audio("response.mp3")
            continue

        # Check for offensive language
        if any(word in user_input.lower() for word in OFFENSIVE_WORDS):
            apology = random.choice(APOLOGY_RESPONSES)
            print(f'ELEY: {apology}')
            text_to_speech(apology, "response.mp3")
            play_audio("response.mp3")
            continue

        # Check for emotions
        emotion = detect_emotion(user_input)
        if emotion:
            response = respond_to_emotion(emotion)
            print(f'ELEY: {response}')
            text_to_speech(response, "response.mp3")
            play_audio("response.mp3")
            continue

        if user_input.lower().startswith("google"):
            search_query = user_input.lower().replace("google", "").strip()
            google_result = open_google_search(search_query)
            print(f'ELEY: {google_result}')
            text_to_speech(google_result, "response.mp3")
            play_audio("response.mp3")
        elif "joke" in user_input.lower():
            joke = tell_joke()
            print(f'ELEY: {joke}')
            text_to_speech(joke, "response.mp3")
            play_audio("response.mp3")
        else:
            best_match = find_best_match(user_input, [q["question"] for q in knowledge_base["questions"]])

            if best_match:
                answer = get_answer_for_question(best_match, knowledge_base, query_count)
                if answer:
                    print(f'ELEY: {answer}')
                    text_to_speech(answer, "response.mp3")
                    play_audio("response.mp3")
                else:
                    print(random.choice(CONFUSED_RESPONSES))
                    text_to_speech(random.choice(CONFUSED_RESPONSES), "response.mp3")
                    play_audio("response.mp3")
            else:
                print('ELEY: Loading...')
                answer = get_answer_for_question(user_input, knowledge_base, query_count)
                if answer:
                    print(f'ELEY: {answer}')
                    text_to_speech(answer, "response.mp3")
                    play_audio("response.mp3")
                    query_count += 1
                    save_query_count(QUERY_COUNT_PATH, query_count)
                else:
                    print(random.choice(CONFUSED_RESPONSES))
                    text_to_speech(random.choice(CONFUSED_RESPONSES), "response.mp3")
                    play_audio("response.mp3")

if __name__ == '__main__':
    chat_bot()