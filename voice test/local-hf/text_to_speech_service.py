from transformers import AutoProcessor, BarkModel
import torch
import numpy as np
import warnings

class TextToSpeechService:
    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoProcessor.from_pretrained("suno/bark-small")
        self.model = BarkModel.from_pretrained("suno/bark-small").to(self.device)

    def synthesize(self, text, voice_preset="v2/en_speaker_1"):
        inputs = self.processor(text, voice_preset=voice_preset, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            audio = self.model.generate(**inputs, pad_token_id=10000)
        return audio.cpu().numpy().squeeze(), self.model.generation_config.sample_rate

    def long_synthesize(self, text, **kwargs):
        import nltk
        from nltk.tokenize import sent_tokenize
        sentences = sent_tokenize(text)
        parts = []
        sr = None
        for s in sentences:
            audio, sr = self.synthesize(s, **kwargs)
            parts.append(audio)
            parts.append(np.zeros(int(0.25 * sr)))
        return np.concatenate(parts), sr
