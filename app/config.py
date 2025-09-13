from dotenv import load_dotenv
import os

load_dotenv()  # lee .env si existe

APP_ENV = os.getenv("APP_ENV", "local")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "change-me")  # para verificación de webhook


