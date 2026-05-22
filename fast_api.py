from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

# Import the main generation function from main.py
from main import generer_musique_culturelle

app = FastAPI(
    title="Cultural Music Generator API",
    description="API to generate cultural music based on text descriptions.",
    version="1.0.0"
)

# Add CORS middleware to allow frontend website to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MusicRequest(BaseModel):
    texte: str
    telecharger: Optional[bool] = False
    modele: Optional[str] = "V4_5"

@app.post("/generate_music")
def generate_music(request: MusicRequest):
    """
    Generate cultural music from a text description.
    """
    if not request.texte or not request.texte.strip():
        raise HTTPException(status_code=400, detail="The 'texte' field cannot be empty.")

    try:
        # Call the existing function from main.py
        result = generer_musique_culturelle(
            texte=request.texte,
            telecharger=request.telecharger,
            modele=request.modele
        )
        
        # Check if it was a simulation due to missing API key
        if result.get("statut") == "simulation":
            # You can handle simulation response here if you want
            pass
            
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred during generation: {str(e)}")

@app.get("/")
def read_root():
    return {
        "message": "Welcome to the Cultural Music Generator API.",
        "endpoints": {
            "POST /generate_music": "Generate music from a cultural text description."
        },
        "docs": "Visit /docs to see the Swagger UI documentation."
    }

if __name__ == "__main__":
    # Run the server with: python fast_api.py
    # or with uvicorn: uvicorn fast_api:app --reload
    uvicorn.run("fast_api:app", host="0.0.0.0", port=8000, reload=True)
