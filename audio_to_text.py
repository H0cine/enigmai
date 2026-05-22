import os
import sys
from groq import Groq

API_KEY = "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"
client = Groq(api_key=API_KEY)

def describe_culture_from_audio(audio_path):
    if not os.path.exists(audio_path):
        return f"Erreur: L'audio '{audio_path}' n'existe pas."

    try:
        print("🎤 1. Transcription de l'audio en texte (Modèle Whisper-Large-v3)...")
        with open(audio_path, "rb") as file:
            transcription = client.audio.transcriptions.create(
              file=(os.path.basename(audio_path), file.read()),
              model="whisper-large-v3",
            )
        lyrics = transcription.text
        
        if not lyrics or lyrics.strip() == "":
            return "Aucune parole ou voix n'a pu être détectée dans l'audio. (Groq ne peut pas analyser la musique instrumentale)."
            
        print(f"✅ Paroles extraites : \"{lyrics[:150]}...\"\n")

        print("🧠 2. Analyse de la culture basée UNIQUEMENT sur le texte (Modèle Llama 3.3 70B)...")
        prompt = f"""
Voici la transcription textuelle (les paroles) d'un extrait musical :
"{lyrics}"

En te basant UNIQUEMENT sur ces paroles, la langue utilisée, l'argot et le contexte des mots, essaie de deviner sachant que la musique vient d'algérie :
1. L'identification culturelle et géographique (ex: Kabyle, Algérien, Français, Américain, etc.).
2. Le style musical probable ou le contexte traditionnel souvent associé à ce genre de paroles.
3. Les thèmes abordés dans la chanson.

Réponds en français de manière très détaillée et structurée. (Précise bien que ton analyse se base sur le texte et non sur la mélodie).
"""
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.3
        )
        return response.choices[0].message.content

    except Exception as e:
        return f"❌ Erreur lors de l'analyse avec Groq: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python audio_to_text.py <chemin_vers_audio>")
        sys.exit(1)

    audio_path_input = sys.argv[1]
    print(describe_culture_from_audio(audio_path_input))