"""Transcription audio hors-ligne, pour un usage sur le terrain sans connexion
(contrainte 'edge computing'). Utilise un modèle Whisper local léger si le paquet
'openai-whisper' (ou 'faster-whisper') est installé sur la machine du conseiller.

Ce module est volontairement isolé : l'application fonctionne même si aucun modèle
local n'est installé (elle indique alors que la transcription hors-ligne n'est
pas disponible sur ce poste, sans jamais bloquer le reste de l'outil).
"""

_model_cache = None


def offline_transcription_available() -> bool:
    try:
        import whisper  # noqa: F401
        return True
    except ImportError:
        return False


def _get_model():
    global _model_cache
    if _model_cache is None:
        import whisper
        # Modèle "base" : bon compromis précision / ressources pour un usage terrain.
        _model_cache = whisper.load_model("base")
    return _model_cache


def transcribe(audio_path: str, lang: str = "fr") -> str:
    """Transcrit un fichier audio local. `audio_path` doit être un chemin sur disque
    (le modèle Whisper local ne lit pas directement un flux Streamlit UploadedFile,
    d'où la nécessité de sauvegarder le fichier temporairement avant appel)."""
    if not offline_transcription_available():
        raise RuntimeError(
            "Le paquet 'openai-whisper' n'est pas installé sur ce poste. "
            "Installe-le pour activer la transcription hors-ligne (voir README).")

    model = _get_model()
    result = model.transcribe(audio_path, language=lang)
    return result.get("text", "").strip()
