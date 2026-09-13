from vetscribe_backend.pipeline import SoapPipeline
from vetscribe_backend.schemas import SoapNote


class FakeTranscriber:
    def __init__(self, text):
        self.text = text
        self.received_audio = None

    def transcribe(self, audio_bytes):
        self.received_audio = audio_bytes
        return self.text


class FakeNoteGenerator:
    def __init__(self, note):
        self.note = note
        self.received_transcript = None

    def generate(self, transcript):
        self.received_transcript = transcript
        return self.note


def test_process_transcribes_then_generates_note_from_transcript():
    expected_note = SoapNote(subjective="s", objective="o", assessment="a", plan="p")
    transcriber = FakeTranscriber(text="owner reports vomiting")
    note_generator = FakeNoteGenerator(note=expected_note)
    pipeline = SoapPipeline(transcriber=transcriber, note_generator=note_generator)

    result = pipeline.process(b"RIFF....audio-bytes....")

    assert transcriber.received_audio == b"RIFF....audio-bytes...."
    assert note_generator.received_transcript == "owner reports vomiting"
    assert result is expected_note
