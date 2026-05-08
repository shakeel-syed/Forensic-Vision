import warnings
# Ignore the Pydantic V1 compatibility warnings specifically for Python 3.14+
warnings.filterwarnings("ignore", message=".*Pydantic V1 functionality.*")
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load API Key from .env
load_dotenv()

# Initialize the model
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.7,
    max_tokens=None,
    timeout=None,
    max_retries=2,
)

# Simple invocation
response = llm.invoke("Explain Quantum Entanglement in one sentence.")
print(response.content)

