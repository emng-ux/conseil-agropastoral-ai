"""Transcription audio en ligne. Nécessite une connexion Internet et une clé API
de service de transcription (ex. variable d'environnement TRANSCRIPTION_API_KEY,
selon le fournisseur choisi par l'organisation : OpenAI Whisper API, Google
Speech-to-Text, etc.).

Cette V1 fournit l'interface attendue par l'application (`transcribe`) et une
implémentation de référence pour l'API Whisper (OpenAI-compatible). Adapte la
fonction `transcribe` au fournisseur retenu si besoin.
"""
import os


def online_transcription_available() -> bool:
    return bool(os.environ.get("TRANSCRIPTION_API_KEY"))


def transcribe(audio_file, lang: str = "fr") -> str:
    """Transcrit un fichier audio (objet file-like) en texte.
    Lève une exception si le service n'est pas configuré ou l'appel échoue."""
    if not online_transcription_available():
        raise RuntimeError("Aucune clé de service de transcription configurée "
                            "(TRANSCRIPTION_API_KEY).")

    import openai  # dépendance optionnelle, seulement utile en ligne

    client = openai.OpenAI(api_key=os.environ["TRANSCRIPTION_API_KEY"])
    result = client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file,
        language=lang,
    )
    return result.text
