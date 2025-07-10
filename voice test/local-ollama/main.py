# main.py
import os
from dotenv import load_dotenv
from langchain.agents import AgentType, initialize_agent, Tool
from langchain_community.llms import Ollama
import requests
import base64
import time
from IPython.display import Audio, display

# Load environment variables
load_dotenv()

# Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
DEFAULT_MODEL = "sematre/orpheus:en"
DEFAULT_VOICE = "tara"

class OrpheusTTS:
    def __init__(self, host=OLLAMA_HOST):
        self.host = host
    
    def generate_speech(
        self,
        text: str,
        voice: str = DEFAULT_VOICE,
        model: str = DEFAULT_MODEL,
        tags: list = None,
        output_file: str = None
    ) -> str:
        """Generate speech from text using Orpheus TTS"""
        endpoint = f"{self.host}/api/generate"
        payload = {
            "model": model,
            "prompt": text,
            "stream": False,
            "options": {"voice": voice}
        }
        
        if tags:
            payload["options"]["tags"] = tags
        
        try:
            response = requests.post(endpoint, json=payload, timeout=120)
            response.raise_for_status()
            audio_data = base64.b64decode(response.json()["response"])
            
            if not output_file:
                output_file = f"tts_output_{int(time.time())}.wav"
            
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            return output_file
        except Exception as e:
            raise RuntimeError(f"TTS generation failed: {str(e)}")

# Initialize TTS engine
tts_engine = OrpheusTTS()

# Create LangChain Tool
def tts_tool(text: str, voice: str = DEFAULT_VOICE) -> str:
    """Convert text to speech. Use for final responses when speaking to users."""
    audio_file = tts_engine.generate_speech(text, voice=voice)
    return f"Speech generated: {audio_file}"

tts_tool_instance = Tool(
    name="TextToSpeech",
    func=tts_tool,
    description="Useful for converting text responses to spoken audio. Use for final answers when speaking to users."
)

# Initialize LLM
llm = Ollama(
    model="llama3",
    base_url=OLLAMA_HOST,
    temperature=0.7
)

# Create agent with TTS capability
agent = initialize_agent(
    tools=[tts_tool_instance],
    llm=llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True
)

# Voice Assistant Function
def voice_assistant(prompt: str, voice: str = DEFAULT_VOICE):
    """Full voice assistant pipeline"""
    # Step 1: Generate text response
    text_response = agent.run(
        f"Create a spoken response for: {prompt}. "
        "Remember to use the TextToSpeech tool for the final output."
    )
    
    # Step 2: Convert to speech
    audio_file = tts_engine.generate_speech(
        text_response,
        voice=voice,
        tags=["smile"]  # Add emotional inflection
    )
    
    # Step 3: Play audio (in Jupyter)
    if 'IPython' in globals():
        display(Audio(audio_file))
    
    return {
        "text": text_response,
        "audio_file": audio_file
    }

# Example usage
if __name__ == "__main__":
    # Simple TTS demo
    print("Testing TTS...")
    audio_path = tts_engine.generate_speech(
        "Hello world! This is Orpheus TTS integration with LangChain",
        voice="leo",
        tags=["chuckle"]
    )
    print(f"Audio saved to: {audio_path}")
    
    # Full agent demo
    print("\nTesting voice assistant...")
    response = voice_assistant(
        "Explain how large language models work in about 3 sentences",
        voice="zoe"
    )
    print(f"Generated response: {response['text']}")
    print(f"Audio file: {response['audio_file']}")