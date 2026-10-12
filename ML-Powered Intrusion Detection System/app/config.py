"""Configuration loaded from environment variables (never hard-code secrets)."""
import os
from dotenv import load_dotenv

load_dotenv()

ABUSEIPDB_API_KEY = os.getenv("ABUSEIPDB_API_KEY", "")
IPINFO_TOKEN = os.getenv("IPINFO_TOKEN", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
PORT = int(os.getenv("PORT", "5000"))

MODEL_DIR = os.getenv("MODEL_DIR", "models")
BINARY_MODEL_PATH = os.path.join(MODEL_DIR, "binary_model.joblib")
ATTACK_MODEL_PATH = os.path.join(MODEL_DIR, "attack_model.joblib")
LABEL_ENCODER_PATH = os.path.join(MODEL_DIR, "label_encoder.joblib")
FEATURE_COLUMNS_PATH = os.path.join(MODEL_DIR, "feature_columns.json")
