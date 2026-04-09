"""
Unit tests for speech_to_text.py
Run with: python -m pytest tests/ -v
"""

import os
import sys
import json
import struct
import wave
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Ensure the project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import speech_recognizer as sr_stub  # noqa – imported lazily inside module

from speech_to_text import (
    transcribe_audio_file,
    transcribe_microphone,
    save_transcript,
    _run_recognition,
)


# ─── Helpers ────────────────────────────────────────────────────────────────

def make_silent_wav(path: str, duration_s: float = 1.0, sample_rate: int = 16000):
    """Write a valid silent mono WAV file to *path*."""
    n_frames = int(duration_s * sample_rate)
    with wave.open(path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)           # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(struct.pack("<" + "h" * n_frames, *([0] * n_frames)))


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestTranscribeAudioFile(unittest.TestCase):

    def test_missing_file_returns_error(self):
        result = transcribe_audio_file("nonexistent_file.wav")
        self.assertFalse(result["success"])
        self.assertIn("not found", result["error"])

    @patch("speech_to_text.sr.Recognizer")
    def test_successful_transcription(self, MockRecognizer):
        recognizer_instance = MockRecognizer.return_value
        recognizer_instance.recognize_google.return_value = "hello world"

        mock_audio = MagicMock()
        recognizer_instance.record.return_value = mock_audio

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            make_silent_wav(tmp.name)
            tmp_path = tmp.name

        try:
            with patch("speech_to_text.sr.AudioFile") as MockAudioFile:
                MockAudioFile.return_value.__enter__ = lambda s: s
                MockAudioFile.return_value.__exit__ = MagicMock(return_value=False)

                result = transcribe_audio_file(tmp_path, engine="google")

        finally:
            os.unlink(tmp_path)

        self.assertTrue(result["success"])
        self.assertEqual(result["text"], "hello world")
        self.assertEqual(result["engine"], "google")

    @patch("speech_to_text.sr.Recognizer")
    def test_unknown_value_error(self, MockRecognizer):
        import speech_recognition as sr
        recognizer_instance = MockRecognizer.return_value
        recognizer_instance.recognize_google.side_effect = sr.UnknownValueError()
        recognizer_instance.record.return_value = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            make_silent_wav(tmp.name)
            tmp_path = tmp.name

        try:
            with patch("speech_to_text.sr.AudioFile") as MockAudioFile:
                MockAudioFile.return_value.__enter__ = lambda s: s
                MockAudioFile.return_value.__exit__ = MagicMock(return_value=False)

                result = transcribe_audio_file(tmp_path, engine="google")
        finally:
            os.unlink(tmp_path)

        self.assertFalse(result["success"])
        self.assertIn("not understood", result["error"])

    @patch("speech_to_text.sr.Recognizer")
    def test_request_error(self, MockRecognizer):
        import speech_recognition as sr
        recognizer_instance = MockRecognizer.return_value
        recognizer_instance.recognize_google.side_effect = sr.RequestError("network error")
        recognizer_instance.record.return_value = MagicMock()

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            make_silent_wav(tmp.name)
            tmp_path = tmp.name

        try:
            with patch("speech_to_text.sr.AudioFile") as MockAudioFile:
                MockAudioFile.return_value.__enter__ = lambda s: s
                MockAudioFile.return_value.__exit__ = MagicMock(return_value=False)

                result = transcribe_audio_file(tmp_path, engine="google")
        finally:
            os.unlink(tmp_path)

        self.assertFalse(result["success"])
        self.assertIn("service error", result["error"])


class TestSaveTranscript(unittest.TestCase):

    def test_save_successful_result(self):
        result = {
            "success": True,
            "text": "Test transcript content.",
            "engine": "google",
            "file": "sample.wav",
            "timestamp": "2024-01-01T00:00:00",
            "error": None,
        }
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            out_path = tmp.name

        try:
            saved = save_transcript(result, out_path)
            self.assertEqual(saved, out_path)
            with open(out_path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Test transcript content.", content)
            self.assertIn("google", content)
        finally:
            os.unlink(out_path)

    def test_save_failed_result(self):
        result = {
            "success": False,
            "text": "",
            "engine": "google",
            "file": "bad.wav",
            "timestamp": "2024-01-01T00:00:00",
            "error": "Speech not understood.",
        }
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
            out_path = tmp.name

        try:
            save_transcript(result, out_path)
            with open(out_path, encoding="utf-8") as f:
                content = f.read()
            self.assertIn("Speech not understood.", content)
            self.assertIn("Failed", content)
        finally:
            os.unlink(out_path)


class TestRunRecognition(unittest.TestCase):

    def _base_result(self, engine="google"):
        return {
            "success": False,
            "text": "",
            "engine": engine,
            "file": "test.wav",
            "timestamp": "2024-01-01T00:00:00",
            "error": None,
        }

    def test_invalid_engine_raises(self):
        recognizer = MagicMock()
        audio = MagicMock()
        result = self._base_result("badengine")
        out = _run_recognition(recognizer, audio, "badengine", "en-US", result)
        self.assertFalse(out["success"])
        self.assertIn("Unknown engine", out["error"])

    def test_google_success(self):
        recognizer = MagicMock()
        recognizer.recognize_google.return_value = "this works"
        audio = MagicMock()
        result = self._base_result("google")
        out = _run_recognition(recognizer, audio, "google", "en-US", result)
        self.assertTrue(out["success"])
        self.assertEqual(out["text"], "this works")


if __name__ == "__main__":
    unittest.main(verbosity=2)
