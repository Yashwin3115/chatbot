import json
import os
import logging
import asyncio
import serial
import time
import wolframalpha
import speech_recognition as sr
from difflib import get_close_matches
from gtts import gTTS
import playsound
import webbrowser
from typing import List, Optional, Dict

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Wolfram Alpha API setup
APP_ID = 'TTTH2G-K83HXKUXRH'  # Replace with your Wolfram Alpha App ID
client = wolframalpha.Client(APP_ID)
QUERY_LIMIT = 100  # Set your desired query limit

# Arduino Serial Port Setup
ARDUINO_PORT = '/dev/ttyUSB0'  # Replace with your Arduino serial port
BAUD_RATE = 9600

class ChatBot:
    def __init__(self, app_id: str, query_limit: int, knowledge_base_path: str, query_count_path: str, arduino_port: str, baud_rate: int):
        self.client = wolframalpha.Client(app_id)
        self.query_limit = query_limit
        self.knowledge_base_path = knowledge_base_path
        self.query_count_path = query_count_path
        self.knowledge_base = self.load_knowledge_base()
        self.query_count = self.load_query_count()
        self.serial_connection = serial.Serial(arduino_port, baud_rate, timeout=1)
        time.sleep(2)  # Wait for the serial connection to initialize

    def play_audio(self, audio_file: str):
        playsound.playsound(audio_file)

    def load_knowledge_base(self) -> Dict:
        if os.path.exists(self.knowledge_base_path):
            with open(self.knowledge_base_path, 'r') as file:
                return json.load(file)
        else:
            return {"questions": []}

    def save_knowledge_base(self):
        with open(self.knowledge_base_path, 'w') as file:
            json.dump(self.knowledge_base, file, indent=2)

    def load_query_count(self) -> int:
        if os.path.exists(self.query_count_path):
            with open(self.query_count_path, 'r') as file:
                data = json.load(file)
                return data.get("query_count", 0)
        else:
            return 0

    def save_query_count(self):
        with open(self.query_count_path, 'w') as file:
            json.dump({"query_count": self.query_count}, file, indent=2)

    def find_best_match(self, user_question: str, questions: List[str]) -> Optional[str]:
        # Ensure that questions is a list of strings
        if not all(isinstance(q, str) for q in questions):
            logging.error("The questions list must contain only strings.")
            return None
        
        if not isinstance(user_question, str):
            logging.error("User question must be a string.")
            return None
        
        matches = get_close_matches(user_question, questions, n=1, cutoff=0.6)
        if matches:
            logging.info(f"Best match found: {matches[0]}")
            return matches[0]
        else:
            logging.info("No match found.")
            return None

    def get_answer_for_question(self, question: str) -> Optional[str]:
        for q in self.knowledge_base["questions"]:
            if q["question"] == question:
                return q["answer"]

        if self.query_count < self.query_limit:
            res = self.client.query(question)
            try:
                answer = next(res.results).text
                return answer
            except StopIteration:
                return None
        else:
            return "Query limit reached. Please try again later."

    async def google_search(self, query: str) -> Optional[str]:
        try:
            search_url = f"https://www.google.com/search?q={query}"
            return search_url
        except Exception as e:
            logging.error(f"Error occurred during Google search: {e}")
            return None

    async def open_google_search(self, query: str) -> str:
        search_url = await self.google_search(query)
        if search_url:
            webbrowser.open_new_tab(search_url)
            return "I found this information online."
        else:
            return "Sorry, I couldn't perform the Google search."

    async def get_speech_input(self) -> str:
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            logging.info("ELEY: Listening...")
            audio = recognizer.listen(source)
            try:
                user_input = recognizer.recognize_google(audio)
                logging.info(f"You: {user_input}")
                return user_input.lower()
            except sr.UnknownValueError:
                logging.warning("ELEY: Sorry, I did not understand that.")
                return ""
            except sr.RequestError:
                logging.error("ELEY: Could not request results from the recognizer service.")
                return ""

    def text_to_speech(self, text: str, file_name: str):
        tts = gTTS(text=text, lang='en')
        tts.save(file_name)

    def send_command_to_arduino(self, command: str):
        self.serial_connection.write((command + '\n').encode())
        response = self.serial_connection.readline().decode().strip()
        logging.info(f"Arduino response: {response}")
        return response

    async def chat_bot(self):
        while True:
            user_input = await self.get_speech_input()

            if user_input == 'quit':
                self.text_to_speech("Goodbye!", "response.mp3")
                self.play_audio("response.mp3")
                break

            if "thank you" in user_input:
                self.text_to_speech("You're welcome!", "response.mp3")
                self.play_audio("response.mp3")
                break

            if user_input.startswith("google"):
                search_query = user_input.replace("google", "").strip()
                google_result = await self.open_google_search(search_query)
                logging.info(f'ELEY: {google_result}')
                self.text_to_speech(google_result, "response.mp3")
                self.play_audio("response.mp3")
            elif "turn on" in user_input:
                arduino_response = self.send_command_to_arduino("turn_on")
                self.text_to_speech(arduino_response, "response.mp3")
                self.play_audio("response.mp3")
            elif "turn off" in user_input:
                arduino_response = self.send_command_to_arduino("turn_off")
                self.text_to_speech(arduino_response, "response.mp3")
                self.play_audio("response.mp3")
            else:
                best_match = self.find_best_match(user_input, [q["question"] for q in self.knowledge_base["questions"]])

                if best_match:
                    answer = self.get_answer_for_question(best_match)
                    logging.info(f'ELEY: {answer}')
                    self.text_to_speech(answer, "response.mp3")
                    self.play_audio("response.mp3")
                else:
                    logging.info('ELEY: Loading...')
                    answer = self.get_answer_for_question(user_input)
                    if answer:
                        logging.info(f'ELEY: {answer}')
                        self.text_to_speech(answer, "response.mp3")
                        self.play_audio("response.mp3")
                        self.query_count += 1
                        self.save_query_count()
                    else:
                        logging.info('ELEY: Sorry, I couldn\'t find an answer for that.')
                        self.text_to_speech("Sorry, I couldn't find an answer for that.", "response.mp3")
                        self.play_audio("response.mp3")

if __name__ == '__main__':
    bot = ChatBot(APP_ID, QUERY_LIMIT, "knowledge_base.json", "query_count.json", ARDUINO_PORT, BAUD_RATE)
    asyncio.run(bot.chat_bot())
