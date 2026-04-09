# Speech-to-Text Transcription Tool

A lightweight Python CLI that converts audio recordings (and live microphone input) into text using the [`SpeechRecognition`](https://github.com/Uberi/speech_recognition) library.

---

## Features

| Feature | Detail |
|---|---|
| **Audio file transcription** | WAV, AIFF, FLAC |
| **Live microphone input** | Auto silence-detection or fixed duration |
| **Multiple engines** | Google Web Speech (online), CMU Sphinx (offline), OpenAI Whisper (offline) |
| **Multi-language** | Pass any BCP-47 tag (`en-US`, `hi-IN`, `fr-FR`, …) |
| **Save transcripts** | Plain-text output with metadata header |
| **JSON output** | Machine-readable results for downstream pipelines |
| **Unit-tested** | `pytest`-based test suite included |

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/speech-to-text.git
cd speech-to-text
pip install -r requirements.txt
```

> **Microphone support** requires PyAudio:
> - macOS / Linux: `pip install pyaudio`
> - Windows: `pip install pipwin && pipwin install pyaudio`

---

## Quick Start

### Transcribe an audio file
```bash
python speech_to_text.py --file recording.wav
```

### Record from microphone (auto-detect speech end)
```bash
python speech_to_text.py --mic
```

### Record for exactly 5 seconds
```bash
python speech_to_text.py --mic --duration 5
```

### Use CMU Sphinx (offline)
```bash
pip install pocketsphinx
python speech_to_text.py --file recording.wav --engine sphinx
```

### Use OpenAI Whisper (offline, highly accurate)
```bash
pip install openai-whisper
python speech_to_text.py --file recording.wav --engine whisper
```

### Transcribe in Hindi and save to file
```bash
python speech_to_text.py --file speech.wav --language hi-IN --save --output transcript.txt
```

### Get JSON output
```bash
python speech_to_text.py --file recording.wav --json
```

---

## CLI Reference

```
usage: speech_to_text.py [-h] (--file PATH | --mic)
                         [--engine {google,sphinx,whisper}]
                         [--language LANGUAGE]
                         [--duration DURATION]
                         [--phrase-limit PHRASE_LIMIT]
                         [--save] [--output PATH]
                         [--json]

Options:
  --file PATH           Path to audio file (.wav / .flac / .aiff)
  --mic                 Record from default microphone
  --engine ENGINE       google (default) | sphinx | whisper
  --language LANGUAGE   BCP-47 code, e.g. en-US, hi-IN (default: en-US)
  --duration N          Record mic for exactly N seconds
  --phrase-limit N      Max seconds of speech in auto mic mode (default: 10)
  --save                Write transcript to a .txt file
  --output PATH         Output file path (used with --save)
  --json                Print full result as JSON
```

---

## Project Structure

```
speech-to-text/
├── speech_to_text.py        # Main CLI tool
├── requirements.txt         # Python dependencies
├── README.md
└── tests/
    └── test_speech_to_text.py  # Unit tests (pytest)
```

---

## Running Tests

```bash
pip install pytest
pytest tests/ -v
```

---

## Engine Comparison

| Engine | Requires Internet | Accuracy | Notes |
|---|---|---|---|
| `google` | Yes | High | Default. Free, rate-limited. |
| `sphinx` | No | Medium | Install `pocketsphinx`. |
| `whisper` | No | Very High | Install `openai-whisper`. Slower. |

---

## Supported Audio Formats

| Format | Notes |
|---|---|
| WAV | Best compatibility, no conversion needed |
| FLAC | Lossless, well supported |
| AIFF | macOS native format |
| MP3 | Requires `pydub` + `ffmpeg` (pre-convert to WAV) |

---

## License

MIT — free to use, modify, and distribute.
