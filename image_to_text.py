import os
import sys
from PIL import Image
from google import genai

API_KEY = "AIzaSyCvkK7uf0zoKBrMabJdSEGJNG-1dliQbbc"
client = genai.Client(api_key=API_KEY)

def describe_culture_from_image(image_path):
    if not os.path.exists(image_path):
        return f"Erreur: L'image '{image_path}' n'existe pas."

    prompt = """
Analyse cette image sans aucun a priori et identifie la culture exacte qu'elle représente. 
Fournis les informations suivantes :
1. L'identification culturelle exacte (ex: Kabyle, Japonaise, Mexicaine, etc.) avec la région précise.
2. Une description précise des éléments visibles qui te permettent d'identifier cette culture (tenues, bijoux, poteries, motifs, etc.).
3. L'année ou la période approximative à laquelle cette scène ou tradition fait référence.
4. Les traditions, l'artisanat ou le contexte historique associés à cette image.

Réponds en français de manière très détaillée, experte et structurée.
"""

    try:
        img = Image.open(image_path)
        
        # Appel à l'API Gemini 2.5 Flash
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, img]
        )
        return response.text

    except Exception as e:
        err = str(e)
        if "403" in err or "401" in err:
            return "⚠️ Clé API invalide ou accès refusé. Vérifiez votre clé Google AI Studio."
        return f"Erreur lors de l'analyse de l'image: {err}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python image_to_text.py <chemin_vers_image>")
        sys.exit(1)

    image_path_input = sys.argv[1]
    print(describe_culture_from_image(image_path_input))