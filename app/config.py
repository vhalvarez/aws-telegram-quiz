from dotenv import load_dotenv
import os

load_dotenv()  # lee .env si existe

APP_ENV = os.getenv("APP_ENV", "local")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "change-me")  # para verificación de webhook

# Si es 1/true, devolvemos el texto de respuesta en el HTTP response (útil para pruebas con curl)
LOCAL_ECHO = os.getenv("LOCAL_ECHO", "1").lower() in ("1", "true", "yes")