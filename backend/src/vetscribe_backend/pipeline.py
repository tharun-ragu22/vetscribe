from vetscribe_backend.note_generation import NoteGenerator
from vetscribe_backend.schemas import SoapResult
from vetscribe_backend.transcription import Transcriber


class SoapPipeline:
    def __init__(self, transcriber: Transcriber, note_generator: NoteGenerator):
        self.transcriber = transcriber
        self.note_generator = note_generator

    def process(self, audio_bytes: bytes) -> SoapResult:
        transcript = self.transcriber.transcribe(audio_bytes)
        note = self.note_generator.generate(transcript)
        return SoapResult(note=note, transcript=transcript)
