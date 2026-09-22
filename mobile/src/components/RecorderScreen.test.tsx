import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { AudioService } from '../services/audio/AudioService';
import type { Recorder, RecordingResult } from '../services/audio/types';
import type { Exam } from '../services/api/types';
import { RecorderScreen } from './RecorderScreen';

/** A fake Recorder so the whole real AudioService state machine runs in the test. */
function makeRecorder(overrides: Partial<Recorder> = {}): jest.Mocked<Recorder> {
  return {
    start: jest.fn(async () => {}),
    stop: jest.fn(async (): Promise<RecordingResult> => ({
      uri: 'file:///rec.m4a',
      durationMillis: 4200,
    })),
    ...overrides,
  } as jest.Mocked<Recorder>;
}

const exam: Exam = {
  id: 'exam-9',
  createdAt: '2026-09-22T10:00:00Z',
  patientName: 'Rex',
  subjective: 'S',
  objective: 'O',
  assessment: 'A',
  plan: 'P',
  transcript: 'vet: hello',
};

describe('RecorderScreen', () => {
  it('shows a start control when idle', () => {
    const audioService = new AudioService(makeRecorder());
    render(<RecorderScreen audioService={audioService} uploadRecording={jest.fn()} />);

    expect(screen.getByText(/start/i)).toBeTruthy();
  });

  it('starts the recorder and reflects the recording state when tapped', async () => {
    const recorder = makeRecorder();
    const audioService = new AudioService(recorder);
    render(<RecorderScreen audioService={audioService} uploadRecording={jest.fn()} />);

    fireEvent.press(screen.getByText(/start/i));

    await waitFor(() => expect(screen.getByText(/stop/i)).toBeTruthy());
    expect(recorder.start).toHaveBeenCalledTimes(1);
    expect(audioService.isRecording).toBe(true);
  });

  it('on stop, uploads the recording and reports the created exam, then returns to idle', async () => {
    const recorder = makeRecorder();
    const audioService = new AudioService(recorder);
    const uploadRecording = jest.fn(async () => exam);
    const onRecorded = jest.fn();
    render(
      <RecorderScreen
        audioService={audioService}
        uploadRecording={uploadRecording}
        onRecorded={onRecorded}
      />,
    );

    fireEvent.press(screen.getByText(/start/i));
    await waitFor(() => expect(screen.getByText(/stop/i)).toBeTruthy());
    fireEvent.press(screen.getByText(/stop/i));

    await waitFor(() => expect(onRecorded).toHaveBeenCalledWith(exam));
    expect(uploadRecording).toHaveBeenCalledWith({ uri: 'file:///rec.m4a', durationMillis: 4200 });
    // back to idle, ready for the next exam
    await waitFor(() => expect(screen.getByText(/start/i)).toBeTruthy());
    expect(audioService.state).toBe('idle');
  });

  it('surfaces a start failure and stays idle', async () => {
    const recorder = makeRecorder({
      start: jest.fn(async () => {
        throw new Error('microphone permission denied');
      }),
    });
    const audioService = new AudioService(recorder);
    render(<RecorderScreen audioService={audioService} uploadRecording={jest.fn()} />);

    fireEvent.press(screen.getByText(/start/i));

    await waitFor(() => expect(screen.getByText(/permission denied/i)).toBeTruthy());
    expect(screen.getByText(/start/i)).toBeTruthy();
    expect(audioService.state).toBe('idle');
  });

  it('surfaces an upload failure and returns to idle', async () => {
    const recorder = makeRecorder();
    const audioService = new AudioService(recorder);
    const uploadRecording = jest.fn(async () => {
      throw new Error('backend returned 502');
    });
    render(<RecorderScreen audioService={audioService} uploadRecording={uploadRecording} />);

    fireEvent.press(screen.getByText(/start/i));
    await waitFor(() => expect(screen.getByText(/stop/i)).toBeTruthy());
    fireEvent.press(screen.getByText(/stop/i));

    await waitFor(() => expect(screen.getByText(/502/)).toBeTruthy());
    await waitFor(() => expect(screen.getByText(/start/i)).toBeTruthy());
    expect(audioService.state).toBe('idle');
  });
});
