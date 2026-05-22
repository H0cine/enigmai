"""
Cultural Music Generator
Analyse un texte sur l'art/culture d'un pays → génère un prompt musical → crée la musique via sunoapi.org
"""

import os
import time
import json
import requests
from groq import Groq

# ─── Config ────────────────────────────────────────────────────────────────────

GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "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")
SUNO_API_KEY      = os.environ.get("SUNO_API_KEY", "827385c2ce7a2098cc9aab56065951ea")       # clé depuis sunoapi.org/api-key

SUNO_BASE_URL     = "https://api.sunoapi.org/api/v1"

# ─── Client Groq ──────────────────────────────────────────────────────────

client = Groq(api_key=GROQ_API_KEY)

# ─── Analyse culturelle via Groq ────────────────────────────────────────────

SYSTEM_ANALYSE = """
Tu es un expert en ethnomusicologie et en cultures du monde.

Quand l'utilisateur te donne un texte décrivant l'art ou la culture d'un pays/région,
tu dois répondre UNIQUEMENT en JSON valide avec cette structure exacte :

{
  "pays": "Nom du pays ou région",
  "region_musicale": "Ex: Afrique du Nord, Amérique latine, Asie du Sud-Est...",
  "style_musical": "Genre musical principal ex: Gnawa, Cumbia, Gamelan, Flamenco...",
  "instruments": ["instrument1", "instrument2", "instrument3"],
  "tempo": "slow|medium|fast",
  "ambiance": "Description courte de l'ambiance en 5-10 mots",
  "tags_suno": "tag1, tag2, tag3, tag4, tag5",
  "prompt_musical": "Description détaillée en anglais pour Suno (max 200 chars) incluant les instruments, le rythme, l'ambiance et le style régional",
  "titre": "Titre poétique pour la musique en français",
  "explication": "1-2 phrases expliquant pourquoi ce style correspond à la culture décrite"
}

Sois précis sur les instruments traditionnels. Le prompt_musical doit être en anglais pour Suno.
"""

def analyser_culture(texte_utilisateur: str) -> dict:
    """Envoie le texte à Groq (Llama 3.3) pour analyse culturelle → retourne le JSON structuré."""
    print("\n🎭 Analyse culturelle en cours...")

    chat_completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        max_tokens=1024,
        temperature=0.7,
        messages=[
            {"role": "system", "content": SYSTEM_ANALYSE},
            {"role": "user", "content": texte_utilisateur}
        ],
        response_format={"type": "json_object"},
    )

    raw = chat_completion.choices[0].message.content.strip()

    # Nettoyer si le modèle met des backticks
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

# ─── Client sunoapi.org ────────────────────────────────────────────────────────

class SunoAPIClient:
    """
    Client pour sunoapi.org — API tierce stable avec clé Bearer.

    Inscription  : https://sunoapi.org
    Clé API      : https://sunoapi.org/api-key
    Documentation: https://docs.sunoapi.org
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

    def _post(self, endpoint: str, payload: dict) -> dict:
        url = f"{SUNO_BASE_URL}/{endpoint}"
        resp = requests.post(url, json=payload, headers=self.headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Suno API error {resp.status_code}: {resp.text[:400]}")
        data = resp.json()
        if data.get("code") != 200:
            raise RuntimeError(f"Suno API erreur logique: {data.get('msg', data)}")
        return data

    def _get(self, endpoint: str, params: dict = None) -> dict:
        url = f"{SUNO_BASE_URL}/{endpoint}"
        resp = requests.get(url, params=params, headers=self.headers, timeout=30)
        if resp.status_code != 200:
            raise RuntimeError(f"Suno API error {resp.status_code}: {resp.text[:400]}")
        data = resp.json()
        if data.get("code") != 200:
            raise RuntimeError(f"Suno API erreur logique: {data.get('msg', data)}")
        return data

    def lancer_generation(self, prompt: str, titre: str, tags: str,
                          instrumental: bool = True, modele: str = "V4_5") -> str:
        """
        Lance la génération et retourne le taskId.

        Modèles disponibles :
          V4       — jusqu'à 4 min, bonne qualité vocale
          V4_5     — jusqu'à 8 min, excellente compréhension du prompt
          V4_5PLUS — jusqu'à 8 min, meilleure qualité globale
          V5       — dernière génération
          V5_5     — toute dernière version
        """
        print(f"\n🎵 Lancement de la génération Suno...")
        print(f"   Modèle  : {modele}")
        print(f"   Prompt  : {prompt[:80]}...")
        print(f"   Tags    : {tags}")
        print(f"   Titre   : {titre}")

        payload = {
            "prompt":       prompt,
            "title":        titre,
            "tags":         tags,
            "instrumental": instrumental,
            "model":        modele,
            "customMode":   True,     # active le mode custom (titre + tags)
            "callBackUrl":  "https://example.com/webhook",
        }

        data = self._post("generate", payload)
        task_id = data["data"]["taskId"]
        print(f"   ✅ taskId: {task_id}")
        return task_id

    def attendre_resultat(self, task_id: str, timeout: int = 1800) -> list[dict]:
        """
        Poll le statut jusqu'à completion et retourne la liste des clips.
        Statuts possibles : pending | processing | complete | failed
        """
        print(f"\n⏳ Attente de la génération (max {timeout}s)...")
        debut = time.time()

        while time.time() - debut < timeout:
            data = self._get("generate/record-info", {"taskId": task_id})
            
            # safely get response
            response_data = data.get("data") or {}
            
            clips = response_data.get("sunoData") or (response_data.get("response") or {}).get("sunoData", [])
            statut_global = response_data.get("status", "")

            print(f"   Statut: {statut_global} ({int(time.time()-debut)}s)")

            if statut_global in ("complete", "SUCCESS"):
                resultats = []
                for clip in clips:
                    resultats.append({
                        "id":        clip.get("id", ""),
                        "title":     clip.get("title", ""),
                        "audio_url": clip.get("audioUrl", "") or clip.get("audio_url", ""),
                        "image_url": clip.get("imageUrl", "") or clip.get("image_url", ""),
                        "duration":  clip.get("duration", 0),
                        "tags":      clip.get("tags", ""),
                    })
                return resultats

            if statut_global == "failed":
                raise RuntimeError(f"Génération échouée: {data}")

            time.sleep(10)

        raise TimeoutError(f"Génération non terminée après {timeout}s")

    def telecharger_audio(self, url: str, chemin: str):
        """Télécharge un fichier audio depuis l'URL retournée."""
        resp = requests.get(url, stream=True, timeout=60)
        resp.raise_for_status()
        with open(chemin, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)
        taille = os.path.getsize(chemin) / 1024
        print(f"   ✅ Téléchargé: {chemin} ({taille:.0f} KB)")


# ─── Pipeline principal ────────────────────────────────────────────────────────

def generer_musique_culturelle(texte: str,
                               telecharger: bool = True,
                               modele: str = "V4_5") -> dict:
    """
    Pipeline complet : texte → Groq → Suno → MP3.

    Args:
        texte:       Texte décrivant l'art/culture d'un pays
        telecharger: Si True, télécharge les MP3 dans output_audio/
        modele:      Modèle Suno à utiliser (V4 | V4_5 | V4_5PLUS | V5 | V5_5)

    Returns:
        Dict avec analyse culturelle, clips (audio_url, fichier_local...) et statut
    """

    # 1. Analyse Claude/Groq
    analyse = analyser_culture(texte)

    print(f"\n📍 Pays détecté    : {analyse['pays']}")
    print(f"🎼 Style musical   : {analyse['style_musical']}")
    print(f"🪘 Instruments     : {', '.join(analyse['instruments'])}")
    print(f"💬 Explication     : {analyse['explication']}")

    # 2. Vérification clé Suno
    if not SUNO_API_KEY:
        print("\n⚠️  SUNO_API_KEY non défini — simulation sans génération réelle")
        print("   Inscris-toi sur https://sunoapi.org puis : export SUNO_API_KEY='...'")
        return {"analyse": analyse, "clips": [], "statut": "simulation"}

    # 3. Génération Suno
    suno = SunoAPIClient(SUNO_API_KEY)

    task_id = suno.lancer_generation(
        prompt=analyse["prompt_musical"],
        titre=analyse["titre"],
        tags=analyse["tags_suno"],
        instrumental=True,
        modele=modele,
    )

    # 4. Attente
    clips = suno.attendre_resultat(task_id)

    print(f"\n🎉 {len(clips)} morceau(x) généré(s) !")
    for i, clip in enumerate(clips, 1):
        print(f"\n  [{i}] {clip['title']}")
        print(f"      Audio : {clip['audio_url']}")
        if clip.get("image_url"):
            print(f"      Image : {clip['image_url']}")

    # 5. Téléchargement optionnel
    if telecharger:
        os.makedirs("output_audio", exist_ok=True)
        style_safe = analyse["style_musical"].replace(" ", "_").replace("/", "-")
        for clip in clips:
            nom = f"output_audio/{clip['id'][:8]}_{style_safe}.mp3"
            try:
                suno.telecharger_audio(clip["audio_url"], nom)
                clip["fichier_local"] = nom
            except Exception as e:
                print(f"   ⚠️  Téléchargement échoué: {e}")

    return {"analyse": analyse, "clips": clips, "statut": "succès"}


# ─── Interface CLI ─────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  🌍 Générateur de Musique Culturelle par IA")
    print("=" * 60)

    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY non défini")
        print("   export GROQ_API_KEY='gsk_...'")
        return

    if not SUNO_API_KEY:
        print("⚠️  SUNO_API_KEY non défini (mode simulation)")
        print("   1. Inscris-toi sur https://sunoapi.org")
        print("   2. Va sur https://sunoapi.org/api-key")
        print("   3. export SUNO_API_KEY='ta_clé'\n")

    print("Décrivez l'art, la culture ou les traditions d'un pays/région.")
    print("Tapez 'fin' sur une ligne vide pour lancer la génération.\n")

    lignes = []
    while True:
        ligne = input(">>> ")
        if ligne.strip().lower() == "fin":
            break
        lignes.append(ligne)

    texte = "\n".join(lignes).strip()
    if not texte:
        print("Texte vide, arrêt.")
        return

    try:
        resultat = generer_musique_culturelle(texte, telecharger=True, modele="V4_5")
        print("\n" + "=" * 60)
        print("  RÉSULTAT FINAL")
        print("=" * 60)
        print(json.dumps(resultat, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        raise


if __name__ == "__main__":
    main()