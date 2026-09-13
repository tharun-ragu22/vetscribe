from vetscribe_backend.note_generation import NoteGenerator
from vetscribe_backend.schemas import SoapNote
from vetscribe_backend.transcription import Transcriber


class SoapPipeline:
    def __init__(self, transcriber: Transcriber, note_generator: NoteGenerator):
        self.transcriber = transcriber
        self.note_generator = note_generator

    def process(self, audio_bytes: bytes) -> SoapNote:
        transcript = self.transcriber.transcribe(audio_bytes)
        return self.note_generator.generate(transcript)
