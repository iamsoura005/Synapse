"""
Voice note delivery for SYNAPSE.
Uses pyttsx3 (https://github.com/nateshmbhat/pyttsx3) — free, open-source, cross-platform.
Replaces ElevenLabs — no API key required, runs offline on all OS.

Install: pip install pyttsx3
"""
import io
import logging
import tempfile
import os
import httpx

logger = logging.getLogger(__name__)

TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendVoice"

RESOLUTION_SCRIPT = """\
Hello, this is your SYNAPSE agent. I've completed a negotiation on your behalf. \
Here's what was agreed: {resolution_summary}. \
Both parties showed {satisfaction_level} satisfaction. \
Your fairness score was {fairness_index}. \
Open the app to review and approve. {contract_note}\
"""


def _get_tts():
    """Initialize pyttsx3 engine for TTS synthesis."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        # Set properties for better voice quality
        engine.setProperty('rate', 150)  # Speed of speech
        engine.setProperty('volume', 0.9)  # Volume level
        return engine
    except ImportError:
        raise RuntimeError(
            "pyttsx3 not installed. Run: pip install pyttsx3"
        )


class VoiceDelivery:
    """Generate voice notes locally using pyttsx3 and deliver via Telegram."""

    def __init__(self):
        self._tts = None  # lazy-loaded on first use

    def _ensure_tts(self):
        if self._tts is None:
            self._tts = _get_tts()
        return self._tts

    async def generate_resolution_voice_note(
        self,
        resolution_text: str,
        agent_voice_id: str = "",          # kept for API compat; unused by pyttsx3
        satisfaction_level: str = "high",
        fairness_index: float = 0.85,
        contract_note: str = "Your agreement has been saved as a Living Contract.",
        output_format: str = "wav",        # pyttsx3 outputs WAV natively
    ) -> bytes:
        """
        Synthesize speech locally with pyttsx3.
        Returns WAV bytes (pyttsx3 writes to temporary file).
        """
        script = RESOLUTION_SCRIPT.format(
            resolution_summary=resolution_text,
            satisfaction_level=satisfaction_level,
            fairness_index=round(fairness_index, 2),
            contract_note=contract_note,
        )

        engine = self._ensure_tts()

        # pyttsx3 writes to a file path
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            engine.save_to_file(script, tmp_path)
            engine.runAndWait()
            
            with open(tmp_path, "rb") as f:
                audio_bytes = f.read()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

        logger.info(f"pyttsx3 synthesized {len(audio_bytes)} bytes of audio.")
        return audio_bytes

    async def send_to_telegram(
        self,
        chat_id: str,
        voice_bytes: bytes,
        caption: str,
    ) -> bool:
        """
        Send audio as a Telegram voice message.
        Telegram accepts OGG Opus, but also WAV for basic playback.
        For production, convert WAV→OGG using ffmpeg if needed.
        """
        from app.config import settings
        url = TELEGRAM_API_URL.format(token=settings.TELEGRAM_BOT_TOKEN)

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    url,
                    data={"chat_id": chat_id, "caption": caption},
                    files={"voice": ("voice.wav", voice_bytes, "audio/wav")},
                    timeout=20.0,
                )
                resp.raise_for_status()
                logger.info(f"Voice note sent to Telegram chat {chat_id}.")
                return True
        except Exception as e:
            logger.error(f"Telegram voice delivery failed for {chat_id}: {e}")
            return False


# ── Optional: OGG Opus conversion (requires ffmpeg on PATH) ──────────────────

def wav_to_ogg_opus(wav_bytes: bytes) -> bytes:
    """
    Convert WAV bytes to OGG Opus using ffmpeg subprocess.
    Only needed if Telegram voice notes require OGG format strictly.
    Requires: ffmpeg installed and on PATH.
    """
    import subprocess
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as wav_tmp:
        wav_tmp.write(wav_bytes)
        wav_path = wav_tmp.name

    ogg_path = wav_path.replace(".wav", ".ogg")
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", wav_path, "-c:a", "libopus", ogg_path],
            check=True, capture_output=True
        )
        with open(ogg_path, "rb") as f:
            return f.read()
    finally:
        for p in [wav_path, ogg_path]:
            if os.path.exists(p):
                os.unlink(p)
