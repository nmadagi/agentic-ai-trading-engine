# ============================================================================
# FILE 1: config.py
# Configuration and environment setup
# ============================================================================

import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

# Load environment variables from Streamlit secrets or .env
for key in ["GROQ_API_KEY", "WORKSPACE_DIR", "APCA_API_KEY_ID", 
            "APCA_API_SECRET_KEY", "APCA_API_BASE_URL"]:
    try:
        if key in st.secrets and not os.getenv(key):
            os.environ[key] = st.secrets[key]
    except Exception:
        pass

RESULTS_FILE = "autohedge_runs.jsonl"
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
APCA_API_KEY_ID = os.getenv("APCA_API_KEY_ID")
APCA_API_SECRET_KEY = os.getenv("APCA_API_SECRET_KEY")