import os
import requests
from dotenv import load_dotenv

load_dotenv()

token = os.getenv("BOT_TOKEN")

url = f"https://api.telegram.org/bot{token}/getMe"

response = requests.get(url, timeout=10)

print(response.json())