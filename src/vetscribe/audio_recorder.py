import sounddevice as sd


class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._stream = None
        self._recording = False

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self):
        self._stream = sd.InputStream(samplerate=self.sample_rate, channels=self.channels)
        self._stream.start()
        self._recording = True

    def stop(self):
        self._stream.stop()
        self._stream.close()
        self._recording = False
