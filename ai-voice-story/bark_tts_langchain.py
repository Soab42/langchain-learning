# bark_tts_langchain.py
import os
import requests
import base64
import uuid
from pathlib import Path
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda

load_dotenv()

API_TOKEN = os.getenv("HUGGINGFACEHUB_API_TOKEN")
print(f"Using Hugging Face API Token: {API_TOKEN}")
API_URL = "https://api-inference.huggingface.co/models/suno/bark"

def generate_tts_api(text: str, voice_preset: str = "v2/en_speaker_6", filename: str = None) -> str:
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Accept": "application/json",
    }

    payload = {
        "inputs": text,
        "parameters": {
            "voice_preset": voice_preset
        }
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    if response.status_code != 200:
        raise Exception(f"Hugging Face API Error {response.status_code}: {response.text}")

    res_json = response.json()

    # Bark returns base64 WAV audio usually in "audio" or "data"
    audio_base64 = res_json.get("audio") or res_json.get("data")
    if not audio_base64:
        raise Exception("No audio data found in Hugging Face API response.")

    audio_bytes = base64.b64decode(audio_base64)
    filename = filename or f"bark_tts_{uuid.uuid4().hex[:6]}.wav"
    filepath = Path(filename)
    filepath.write_bytes(audio_bytes)

    return str(filepath)

# LangChain-compatible RunnableLambda
bark_tts_chain = RunnableLambda(
    lambda inputs: generate_tts_api(
        text=inputs.get("text", ""),
        voice_preset=inputs.get("voice", "v2/en_speaker_6")
    )
)
