"""LLM provider configuration. Supports Google Gemini and Groq."""
import os
from dotenv import load_dotenv

load_dotenv()

SUPPORTED_PROVIDERS = ("google", "groq")

GOOGLE_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"


def get_llm(provider: str, api_key: str = None, temperature: float = 0.2):
    provider = (provider or "google").lower()

    if provider == "google":
        from langchain_google_genai import ChatGoogleGenerativeAI
        key = api_key or os.getenv("GOOGLE_API_KEY")
        if not key:
            raise ValueError("Google API key not set. Add it in the sidebar or in your .env file.")
        return ChatGoogleGenerativeAI(model=GOOGLE_MODEL, google_api_key=key, temperature=temperature)

    elif provider == "groq":
        from langchain_groq import ChatGroq
        key = api_key or os.getenv("GROQ_API_KEY")
        if not key:
            raise ValueError("Groq API key not set. Add it in the sidebar or in your .env file.")
        return ChatGroq(model=GROQ_MODEL, groq_api_key=key, temperature=temperature)

    raise ValueError(f"Unsupported provider: {provider}. Choose from {SUPPORTED_PROVIDERS}")