import os
from os import getenv

API_ID = int(os.environ.get("API_ID", "2645474"))  # Replace "123456" with your actual api_id or use .env
API_HASH = os.environ.get("API_HASH", "6c9a5044d2f2c2350ac20b3838a7896e")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "7595907385:AAFxOWCPWCa57YrHyS0THz6TbiNRZdY-GK4")

OWNER_ID = int(os.environ.get("OWNER_ID", "929216155"))  # Your Telegram user ID
SUDO_USERS = list(map(int, os.environ.get("SUDO_USERS", "929216155").split()))  # Space-separated user IDs

MONGO_URL = os.environ.get("MONGO_URL", "mongodb+srv://4gbupload:4gbupload@cluster0.lfgs1vl.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")##your mongo url eg: withmongodb+srv://xxxxxxx:xxxxxxx@clusterX.xxxx.mongodb.net/?retryWrites=true&w=majority
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1002540658580"))  # Telegram channel ID (with -100 prefix)

PREMIUM_LOGS = os.environ.get("PREMIUM_LOGS", "")  # Optional here you'll get all logs
