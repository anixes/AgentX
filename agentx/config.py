
# agentx/config.py
# ================
# Global configuration and feature flags for AgentX.

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AGENTX_DIVERSITY_BETA = True

# Telegram Configuration
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ALLOWED_USER_ID = os.getenv("TELEGRAM_ALLOWED_USER_ID")

# Model API Keys
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
