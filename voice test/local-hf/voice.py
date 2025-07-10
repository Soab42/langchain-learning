import whisper, sounddevice as sd
from langchain_ollama.llms import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from text_to_speech_service import TextToSpeechService

# Initialize modules
stt = whisper.load_model("base.en")
tts = TextToSpeechService()
llm = OllamaLLM(model="llama3.1")  # or llama2, mistral

prompt = ChatPromptTemplate.from_template("User: {text}\nAssistant:")
chain = prompt | llm

def listen_and_respond():
    audio = sd.rec(int(5 * 16000), samplerate=16000, channels=1)
    sd.wait()
    text = stt.transcribe(audio)["text"]
    resp = chain.invoke({"text": text})
    audio_resp, sr = tts.synthesize(resp)
    sd.play(audio_resp, sr)
    sd.wait()

if __name__ == "__main__":
    print("Say something!")
    listen_and_respond()
