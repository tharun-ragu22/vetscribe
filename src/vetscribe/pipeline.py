import enum


class PipelineState(enum.Enum):
    IDLE = "idle"
    RECORDING = "recording"
    PROCESSING = "processing"


class Pipeline:
    def __init__(self, recorder, api_client, injector, on_flyout_needed):
        self.recorder = recorder
        self.api_client = api_client
        self.injector = injector
        self.on_flyout_needed = on_flyout_needed
        self.state = PipelineState.IDLE

    def toggle_recording(self):
        if self.state == PipelineState.IDLE:
            self.recorder.start()
            self.state = PipelineState.RECORDING
