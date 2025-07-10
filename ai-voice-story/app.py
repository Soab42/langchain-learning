# app.py
import streamlit as st
from langchain_ollama import ChatOllama
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from bark_tts_langchain import bark_tts_chain

# Voice options
voices = {
    "Mia (Professional, Female)": "v2/en_speaker_6",
    "Leo (Authoritative, Male)": "v2/en_speaker_5",
    "Jess (Youthful, Female)": "v2/en_speaker_2",
    "Tara (Conversational, Female)": "v2/en_speaker_0",
    "Zac (Energetic, Male)": "v2/en_speaker_7",
}

# LangChain LLM
llm = ChatOllama(model="llama3")
prompt = PromptTemplate.from_template("Tell a short bedtime story about {topic}.")
story_chain = prompt | llm | StrOutputParser()

# --- UI ---
st.set_page_config(page_title="AI StoryTeller with Voice 🎙️", layout="centered")
st.title("🌙 AI Bedtime StoryTeller with Voice")
st.write("Let the AI tell your child a magical story... and listen to it!")

topic = st.text_input("Enter a topic (e.g., 'kitten and star')", "kitten and star")

voice_choice = st.selectbox("🎤 Choose a voice", list(voices.keys()))

if st.button("🎧 Generate Story"):
    with st.spinner("Creating story and voice..."):
        story = story_chain.invoke({"topic": topic})
        voice_tag = voices[voice_choice]
        audio_path = bark_tts_chain.invoke({"text": story, "voice": voice_tag})

    st.success("Story is ready!")
    st.subheader("📝 Story")
    st.markdown(f"_{story}_")

    st.subheader("🔊 Listen")
    st.audio(audio_path)
