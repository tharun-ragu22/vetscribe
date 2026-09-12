from vetscribe.audio_recorder import AudioRecorder


def test_start_creates_input_stream_and_sets_recording_true(mocker):
    mock_stream_cls = mocker.patch("vetscribe.audio_recorder.sd.InputStream")
    recorder = AudioRecorder(sample_rate=16000, channels=1)

    recorder.start()

    mock_stream_cls.assert_called_once()
    _, kwargs = mock_stream_cls.call_args
    assert kwargs["samplerate"] == 16000
    assert kwargs["channels"] == 1
    mock_stream_cls.return_value.start.assert_called_once()
    assert recorder.is_recording is True
