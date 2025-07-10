from huggingface_hub import InferenceClient

import os

client = InferenceClient(
    api_key=os.environ["HF_TOKEN"],
    provider="auto",   # Automatically selects best provider
)

# Chat completion
completion = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-V3-0324",
    messages=[{"role": "user", "content": "A story about hiking in the mountains"}]
)

# Image generation
image = client.text_to_image(
    prompt="A serene lake surrounded by mountains at sunset, photorealistic style",
    model="black-forest-labs/FLUX.1-dev"
)

client.text_to_speech(
    text="Once upon a time, in a land far away, there lived a brave knight.",
    voice="v2/en_speaker_6",  # Example voice preset
    model="suno/bark"
)
# Save the image
print("Image URL:", image)
