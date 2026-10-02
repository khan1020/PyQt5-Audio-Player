import sys
import wave
import numpy as np
import pyaudio
from datetime import datetime

from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                             QHBoxLayout, QWidget, QFileDialog, QSlider, QLabel, QStyle)
from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
import pyqtgraph as pg


class AudioPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Professional Audio Player")
        self.setGeometry(100, 100, 800, 500)

        # ----------------- Media & Recording ----------------- #
        self.player = QMediaPlayer()
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)

        self.audio = pyaudio.PyAudio()
        self.is_recording = False
        self.frames = []
        self.stream = None

        # ----------------- Playback waveform ----------------- #
        self.playback_samples = None
        self.playback_timer = QTimer()
        self.playback_timer.timeout.connect(self.update_playback_waveform)

        # ----------------- UI Setup ----------------- #
        self.setup_ui()

    # ----------------- UI Setup ----------------- #
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()

        # Waveform plot
        self.waveform_widget = pg.PlotWidget(title="Audio Waveform")
        self.waveform_widget.setYRange(-32768, 32767)  # 16-bit audio
        layout.addWidget(self.waveform_widget)

        # Timer for recording waveform
        self.record_timer = QTimer()
        self.record_timer.timeout.connect(self.update_record_waveform)
        self.record_timer.start(50)

        # Action buttons
        button_layout = QHBoxLayout()
        self.play_button = QPushButton()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_button.clicked.connect(self.play_pause)

        self.stop_button = QPushButton()
        self.stop_button.setIcon(self.style().standardIcon(QStyle.SP_MediaStop))
        self.stop_button.clicked.connect(self.stop)

        button_layout.addWidget(self.play_button)
        button_layout.addWidget(self.stop_button)

        # Time slider
        time_layout = QHBoxLayout()
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.sliderMoved.connect(self.set_position)
        self.time_slider.setRange(0, 0)
        self.current_time_label = QLabel("0:00")
        self.total_time_label = QLabel("0:00")
        time_layout.addWidget(self.current_time_label)
        time_layout.addWidget(self.time_slider)
        time_layout.addWidget(self.total_time_label)

        # Volume slider
        volume_layout = QHBoxLayout()
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self.set_volume)
        volume_layout.addWidget(QLabel("Volume:"))
        volume_layout.addWidget(self.volume_slider)

        # Upload & record buttons
        action_layout = QHBoxLayout()
        self.upload_button = QPushButton("Upload Audio")
        self.upload_button.clicked.connect(self.upload_audio)
        self.record_button = QPushButton("Start Recording")
        self.record_button.clicked.connect(self.toggle_recording)
        action_layout.addWidget(self.upload_button)
        action_layout.addWidget(self.record_button)

        # Sample label
        self.sample_label = QLabel("Samples: 0 / 0")

        # Add layouts
        layout.addLayout(action_layout)
        layout.addLayout(button_layout)
        layout.addLayout(time_layout)
        layout.addLayout(volume_layout)
        layout.addWidget(self.sample_label)

        central_widget.setLayout(layout)

        self.player.setVolume(70)

    # ----------------- Audio Controls ----------------- #
    def upload_audio(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Upload Audio File", "", "Audio Files (*.wav *.mp3 *.ogg *.m4a)"
        )
        if filename:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(filename)))
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

            # Load WAV for waveform
            if filename.lower().endswith(".wav"):
                with wave.open(filename, 'rb') as wf:
                    frames = wf.readframes(wf.getnframes())
                    self.playback_samples = np.frombuffer(frames, dtype=np.int16)

    def play_pause(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
            self.playback_timer.stop()
        else:
            self.player.play()
            self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
            self.playback_timer.start(50)

    def stop(self):
        self.player.stop()
        self.play_button.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.playback_timer.stop()
        self.waveform_widget.clear()

    def set_position(self, position):
        self.player.setPosition(position)

    def position_changed(self, position):
        self.time_slider.setValue(position)
        self.update_time_label(position, self.current_time_label)

    def duration_changed(self, duration):
        self.time_slider.setRange(0, duration)
        self.update_time_label(duration, self.total_time_label)

    def set_volume(self, volume):
        self.player.setVolume(volume)

    def update_time_label(self, ms, label):
        seconds = ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        label.setText(f"{minutes}:{seconds:02d}")

    # ----------------- Recording ----------------- #
    def toggle_recording(self):
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def start_recording(self):
        self.is_recording = True
        self.record_button.setText("Stop Recording")
        self.frames = []

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=44100,
            input=True,
            frames_per_buffer=1024,
            stream_callback=self.audio_callback
        )
        self.stream.start_stream()

    def stop_recording(self):
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()

        self.is_recording = False
        self.record_button.setText("Start Recording")

        if self.frames:
            filename = f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
                wf.setframerate(44100)
                wf.writeframes(b''.join(self.frames))

            # Trim silence
            trimmed_file, total_samples, useful_samples = self.trim_silence(filename)
            self.sample_label.setText(f"Samples: {useful_samples} / {total_samples}")
            print(f"Trimmed file: {trimmed_file}, Total: {total_samples}, Useful: {useful_samples}")

    def audio_callback(self, in_data, frame_count, time_info, status):
        self.frames.append(in_data)
        return (in_data, pyaudio.paContinue)

    # ----------------- Waveform Updates ----------------- #
    def update_record_waveform(self):
        if self.is_recording and self.frames:
            data = b''.join(self.frames[-5:])
            samples = np.frombuffer(data, dtype=np.int16)
            self.waveform_widget.plot(samples, clear=True, pen='c')

    def update_playback_waveform(self):
        if self.playback_samples is not None:
            pos_ms = self.player.position()
            ptr = int(pos_ms * 44100 / 1000)
            start = max(ptr - 1000, 0)
            end = min(ptr + 1000, len(self.playback_samples))
            self.waveform_widget.plot(self.playback_samples[start:end], clear=True, pen='g')

    # ----------------- Silence Trimming ----------------- #
    def trim_silence(self, filename, threshold=500):
        with wave.open(filename, 'rb') as wf:
            params = wf.getparams()
            frames = wf.readframes(wf.getnframes())
            samples = np.frombuffer(frames, dtype=np.int16)

        # Trim start
        start = 0
        for i, s in enumerate(samples):
            if abs(s) > threshold:
                start = i
                break
        # Trim end
        end = len(samples)
        for i, s in enumerate(samples[::-1]):
            if abs(s) > threshold:
                end = len(samples) - i
                break

        trimmed_samples = samples[start:end]
        trimmed_file = filename.replace(".wav", "_trimmed.wav")
        with wave.open(trimmed_file, 'wb') as wf:
            wf.setnchannels(params.nchannels)
            wf.setsampwidth(params.sampwidth)
            wf.setframerate(params.framerate)
            wf.writeframes(trimmed_samples.tobytes())

        return trimmed_file, len(samples), len(trimmed_samples)

    # ----------------- Cleanup ----------------- #
    def closeEvent(self, event):
        if self.is_recording:
            self.stop_recording()
        self.audio.terminate()
        event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    player = AudioPlayer()
    player.show()
    sys.exit(app.exec_())
