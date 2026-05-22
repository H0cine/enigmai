from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from gradio_client import Client
import shutil
import subprocess
import os
import uuid
import uvicorn

# Hugging Face token
HF_TOKEN = os.environ.get("HF_TOKEN", "haya ejbet wa7da lik nta")

# Output directory for generated songs
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_songs")
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(
    title="Song Generator API",
    description="API to generate songs using ACE-Step Music Studio and play them automatically.",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class SongRequest(BaseModel):
    prompt: str
    lyrics: str
    duration_s: Optional[int] = 30
    bpm: Optional[int] = 120
    instrumental: Optional[bool] = False
    auto_play: Optional[bool] = True


@app.post("/generate_song")
def generate_song(request: SongRequest):
    """
    Generate a song from a text prompt and lyrics, then auto-play it on the PC.
    """
    if not request.prompt or not request.prompt.strip():
        raise HTTPException(status_code=400, detail="The 'prompt' field cannot be empty.")
    if not request.lyrics or not request.lyrics.strip():
        raise HTTPException(status_code=400, detail="The 'lyrics' field cannot be empty.")

    try:
        # Connect to ACE-Step
        client = Client("techfreakworm/ACE-Music-Studio", token=HF_TOKEN)

        # Generate
        result = client.predict(
            prompt=request.prompt,
            lyrics=request.lyrics,
            duration_s=request.duration_s,
            instrumental_label="Instrumental" if request.instrumental else "With vocals",
            adv_bpm=request.bpm,
            api_name="/on_generate_click"
        )

        # Copy the generated audio to our output folder
        audio_path = result[0]
        filename = f"song_{uuid.uuid4().hex[:8]}.wav"
        output_file = os.path.join(OUTPUT_DIR, filename)
        shutil.copy2(audio_path, output_file)

        # Auto-play with the default music player on the PC
        if request.auto_play:
            subprocess.Popen(["xdg-open", output_file])

        return {
            "status": "success",
            "message": "Song generated and playing!",
            "filename": filename,
            "path": output_file,
            "download_url": f"/download/{filename}"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error during generation: {str(e)}")


@app.get("/play_latest")
def play_latest():
    """Play the most recently generated song with the default music player."""
    songs = sorted(
        [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".wav")],
        key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
        reverse=True
    )
    if not songs:
        raise HTTPException(status_code=404, detail="No songs generated yet.")

    filepath = os.path.join(OUTPUT_DIR, songs[0])
    subprocess.Popen(["xdg-open", filepath])
    return {"status": "playing", "filename": songs[0]}


@app.get("/download/{filename}")
def download_song(filename: str):
    """Download a generated song file."""
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Song not found.")
    return FileResponse(filepath, media_type="audio/wav", filename=filename)


@app.get("/songs")
def list_songs():
    """List all generated songs."""
    songs = [f for f in os.listdir(OUTPUT_DIR) if f.endswith(".wav")]
    songs.sort(key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)), reverse=True)
    return {"songs": songs}


@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Song Generator API.",
        "endpoints": {
            "POST /generate_song": "Generate a song from prompt + lyrics, auto-plays on PC.",
            "GET /play_latest": "Play the most recent song.",
            "GET /songs": "List all generated songs.",
            "GET /download/{filename}": "Download a generated song."
        },
        "docs": "Visit /docs to see the Swagger UI documentation."
    }


if __name__ == "__main__":
    uvicorn.run("song_api:app", host="0.0.0.0", port=8001, reload=True)
