# PyQt5 Professional Audio Player & Recorder 🎵

A feature-rich desktop audio application built with Python and PyQt5. This application allows users to play existing audio files, record live audio from their microphone, visualize waveforms in real-time, and automatically trim silence from recordings.

## ✨ Features
*   **Media Playback:** Play, pause, and stop audio files with a fully functional scrubber/timeline and volume control.
*   **Live Microphone Recording:** Record audio directly from your microphone into the application.
*   **Real-time Waveform Visualization:** Uses `pyqtgraph` and `numpy` to render a dynamic, live visual waveform of the audio as you record or play it.
*   **Auto-Silence Trimming:** When a recording finishes, the application automatically processes the file to trim dead air (silence below a specific amplitude threshold) from the beginning and end, saving a clean `_trimmed.wav` file.
*   **Multi-Format Support:** Load `.wav`, `.mp3`, `.ogg`, and `.m4a` files.

## 🛠️ Requirements
To run this application, you need Python installed along with the following libraries:
```bash
pip install PyQt5 pyaudio numpy pyqtgraph
```
*(Note: `PyAudio` might require system-level audio headers depending on your OS).*

## 🚀 How to Run
1. Clone this repository.
2. Ensure you have a working microphone connected.
3. Run the application:
```bash
python audio_player.py
```

## 📂 Output Files
Recordings are automatically saved in the same directory using a timestamped format:
*   Raw recording: `recording_YYYYMMDD_HHMMSS.wav`
*   Auto-trimmed version: `recording_YYYYMMDD_HHMMSS_trimmed.wav`
