from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI()

# read model from .env file
model = os.environ['OPENAI_MODEL']

# create a directory for saving the chat history
if not os.path.exists("chat_history"):
    os.makedirs("chat_history")

chat_history_path = "chat_history/"