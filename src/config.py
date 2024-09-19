from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

client = OpenAI(
  api_key='<YOUR_API_KEY>', 
  base_url="https://oai.hconeai.com/v1", 
  default_headers={ 
    "Helicone-Auth": f"Bearer pk-helicone-4vv3wbi-g6dea4y-xer3cki-3utlmtq",
  }
)

client = OpenAI()

# read model from .env file
model = os.environ['OPENAI_MODEL']

# create a directory for saving the chat history
if not os.path.exists("chat_history"):
    os.makedirs("chat_history")

chat_history_path = "chat_history/"