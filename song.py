# pip install gradio_client
from gradio_client import Client
import shutil
import os

# Hugging Face token for GPU quota
hf_token = os.environ.get("HF_TOKEN", "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")

# Initialize the client pointing to ACE-Step Music Studio
print("Connecting to ACE-Step Music Studio...")
client = Client("techfreakworm/ACE-Music-Studio", token="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")

# Lyrics - phonk style (mostly instrumental with ad-libs)
lyrics = """[Intro]
Yeah, uh, let's go

[Drop]
Pull up, skrrt, we ride tonight
Drift phonk, dark vibes, no light
Cowbell hittin, bass so low
Shadow gang, we run the show

[Break]
Uh, yeah, uh

[Drop]
Pull up, skrrt, we ride tonight
Drift phonk, dark vibes, no light
"""

# Generate the song
print("Generating song... This may take a few minutes.")
result = client.predict(
    prompt="aggressive drift phonk, heavy distorted 808 bass, cowbell pattern, dark Memphis rap, phonk for edits, hard hitting drums, lo-fi vinyl crackle, chopped vocal samples, aggressive energy, car drift edit music, fast tempo, trap hi-hats, dark atmosphere, instrumental phonk",
    lyrics=lyrics,
    duration_s=30,
    instrumental_label="With vocals",
    adv_bpm=140,
    api_name="/on_generate_click"
)

# result is a tuple: (audio_filepath, metadata_json, html_info)
audio_path = result[0]
output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_song.wav")

# Copy the generated audio to the project folder
shutil.copy2(audio_path, output_file)
print(f"\nSong saved at: {output_file}")
print("You can play it with: vlc generated_song.wav")