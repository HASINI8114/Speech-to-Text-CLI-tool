"""
Speech-to-Text Transcription Tool
===================================
Converts audio recordings into text using the SpeechRecognition library.
Supports WAV, AIFF, FLAC, and microphone input.

Usage:
  python speech_to_text.py --file audio.wav
  python speech_to_text.py --mic
  python speech_to_text.py --file audio.wav --engine google
  python speech_to_text.py --help
"""

import argparse
import os
import sys
import json
import datetime

try:
    import speech_recognition as sr
except ImportError:
    print("Error: 'SpeechRecognition' library not found.")
    print("Install it with: pip install SpeechRecognition")
    sys.exit(1)


# ─── Recognizer Engine Map ──────────────────────────────────────────────────

ENGINES = {
    "google":    "recognize_google",
    "sphinx":    "recognize_sphinx",
    "whisper":   "recognize_whisper",
}


# ─── Core Transcription ─────────────────────────────────────────────────────

def transcribe_audio_file(file_path: str, engine: str = "google", language: str = "en-US") -> dict:
    """
    Transcribe speech from an audio file.

    Args:
        file_path: Path to the audio file (.wav, .aiff, .flac).
        engine:    Recognition engine to use (google, sphinx, whisper).
        language:  BCP-47 language tag (e.g. 'en-US', 'hi-IN', 'fr-FR').

    Returns:
        dict with keys: success, text, engine, file, timestamp, error
    """
    result = {
        "success": False,
        "text": "",
        "engine": engine,
        "file": file_path,
        "timestamp": datetime.datetime.now().isoformat(),
        "error": None,
    }

    if not os.path.isfile(file_path):
        result["error"] = f"File not found: {file_path}"
        return result

    recognizer = sr.Recognizer()

    # Tuning knobs – adjust for noisy environments
    recognizer.energy_threshold = 300          # Min audio energy to treat as speech
    recognizer.dynamic_energy_threshold = True  # Auto-adjust threshold

    try:
        with sr.AudioFile(file_path) as source:
            print(f"  Loading '{file_path}' ...")
            audio = recognizer.record(source)   # Read the entire file
    except Exception as exc:
        result["error"] = f"Could not read audio file: {exc}"
        return result

    result = _run_recognition(recognizer, audio, engine, language, result)
    return result


def transcribe_microphone(engine: str = "google", language: str = "en-US",
                          duration: int = None, phrase_limit: int = 10) -> dict:
    """
    Transcribe speech captured from the default microphone.

    Args:
        engine:       Recognition engine.
        language:     BCP-47 language tag.
        duration:     Record for exactly N seconds (None = auto-detect silence).
        phrase_limit: Maximum seconds of speech before stopping (auto mode).

    Returns:
        dict with keys: success, text, engine, timestamp, error
    """
    result = {
        "success": False,
        "text": "",
        "engine": engine,
        "file": "microphone",
        "timestamp": datetime.datetime.now().isoformat(),
        "error": None,
    }

    recognizer = sr.Recognizer()
    recognizer.energy_threshold = 300
    recognizer.dynamic_energy_threshold = True

    try:
        with sr.Microphone() as source:
            print("  Adjusting for ambient noise – please wait ...")
            recognizer.adjust_for_ambient_noise(source, duration=1)

            if duration:
                print(f"  Recording for {duration} second(s) ...")
                audio = recognizer.record(source, duration=duration)
            else:
                print(f"  Listening (up to {phrase_limit}s of speech) ... speak now!")
                audio = recognizer.listen(source, phrase_time_limit=phrase_limit)
    except OSError:
        result["error"] = "No microphone found. Connect a mic and try again."
        return result
    except Exception as exc:
        result["error"] = f"Microphone error: {exc}"
        return result

    result = _run_recognition(recognizer, audio, engine, language, result)
    return result


# ─── Internal Helper ────────────────────────────────────────────────────────

def _run_recognition(recognizer, audio, engine, language, result):
    """Dispatch audio to the chosen recognition engine."""
    print(f"  Transcribing with engine='{engine}', language='{language}' ...")

    try:
        if engine == "google":
            text = recognizer.recognize_google(audio, language=language)

        elif engine == "sphinx":
            # CMU Sphinx – offline, requires pocketsphinx
            try:
                text = recognizer.recognize_sphinx(audio, language=language)
            except sr.RequestError:
                raise sr.RequestError(
                    "Sphinx engine not available. "
                    "Install pocketsphinx: pip install pocketsphinx"
                )

        elif engine == "whisper":
            # OpenAI Whisper – offline, requires openai-whisper
            try:
                text = recognizer.recognize_whisper(audio, language=language.split("-")[0])
            except AttributeError:
                raise sr.RequestError(
                    "Whisper engine not available. "
                    "Install: pip install openai-whisper"
                )

        else:
            raise ValueError(f"Unknown engine: '{engine}'. Choose from: {list(ENGINES)}")

        result["success"] = True
        result["text"] = text

    except sr.UnknownValueError:
        result["error"] = "Speech not understood. Try a clearer recording or a different engine."
    except sr.RequestError as exc:
        result["error"] = f"Recognition service error: {exc}"
    except Exception as exc:
        result["error"] = f"Unexpected error: {exc}"

    return result


# ─── Output Helpers ─────────────────────────────────────────────────────────

def save_transcript(result: dict, output_path: str = None) -> str:
    """Save the transcription result as a .txt file."""
    if output_path is None:
        base = os.path.splitext(result["file"])[0] if result["file"] != "microphone" else "mic_transcript"
        output_path = f"{base}_transcript.txt"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"Speech-to-Text Transcript\n")
        f.write(f"{'='*40}\n")
        f.write(f"Source   : {result['file']}\n")
        f.write(f"Engine   : {result['engine']}\n")
        f.write(f"Timestamp: {result['timestamp']}\n")
        f.write(f"Status   : {'Success' if result['success'] else 'Failed'}\n")
        f.write(f"{'='*40}\n\n")
        if result["success"]:
            f.write(result["text"])
        else:
            f.write(f"[Error] {result['error']}")

    return output_path


def print_result(result: dict):
    """Pretty-print transcription result to stdout."""
    border = "─" * 50
    print(f"\n{border}")
    if result["success"]:
        print("  TRANSCRIPT")
        print(border)
        print(f"\n{result['text']}\n")
    else:
        print("  TRANSCRIPTION FAILED")
        print(border)
        print(f"\n  {result['error']}\n")
    print(border)


# ─── CLI ────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Speech-to-Text Transcription Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python speech_to_text.py --file recording.wav
  python speech_to_text.py --file recording.wav --engine sphinx --language en-US
  python speech_to_text.py --mic --duration 5
  python speech_to_text.py --file audio.wav --save --output result.txt
  python speech_to_text.py --file audio.wav --json
        """,
    )

    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--file", metavar="PATH", help="Path to audio file (.wav/.flac/.aiff)")
    source.add_argument("--mic",  action="store_true", help="Record from microphone")

    parser.add_argument(
        "--engine", choices=list(ENGINES), default="google",
        help="Recognition engine (default: google)",
    )
    parser.add_argument(
        "--language", default="en-US",
        help="BCP-47 language code, e.g. en-US, hi-IN, fr-FR (default: en-US)",
    )
    parser.add_argument(
        "--duration", type=int, default=None,
        help="Mic recording duration in seconds (omit for auto silence-detection)",
    )
    parser.add_argument(
        "--phrase-limit", type=int, default=10,
        help="Max seconds of speech in auto mic mode (default: 10)",
    )
    parser.add_argument(
        "--save", action="store_true",
        help="Save transcript to a .txt file",
    )
    parser.add_argument(
        "--output", metavar="PATH", default=None,
        help="Output file path (used with --save)",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_out",
        help="Print full result as JSON",
    )
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    print("\nSpeech-to-Text Transcription Tool")
    print("=" * 38)

    # Run transcription
    if args.file:
        result = transcribe_audio_file(
            file_path=args.file,
            engine=args.engine,
            language=args.language,
        )
    else:
        result = transcribe_microphone(
            engine=args.engine,
            language=args.language,
            duration=args.duration,
            phrase_limit=args.phrase_limit,
        )

    # Output
    if args.json_out:
        print(json.dumps(result, indent=2))
    else:
        print_result(result)

    if args.save:
        saved_path = save_transcript(result, args.output)
        print(f"  Transcript saved to: {saved_path}\n")

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
