import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import { ApiClient } from '../services/api/ApiClient';
import { AudioService } from '../services/audio/AudioService';
import type { Recorder, RecordingResult } from '../services/audio/types';
import { ExamEditor } from '../components/ExamEditor';
import { HistoryScreen } from '../components/HistoryScreen';
import { RecorderScreen } from '../components/RecorderScreen';
import { FakeBackend } from './fakeBackend';

/**
 * End-to-end through the real screens, the real ApiClient, and the faithful fake
 * backend — the closest we get to a device run in Node. Drives actual user gestures
 * (tap record, edit + save, tap inject) and asserts on backend state afterwards.
 */
describe('screens end-to-end', () => {
  function client(backend: FakeBackend): ApiClient {
    return new ApiClient({ baseUrl: 'http://clinic:8000', fetch: backend.fetch });
  }

  it('records an exam: tap start/stop uploads mocked audio and persists it', async () => {
    const backend = new FakeBackend();
    const apiClient = client(backend);
    const recorder: Recorder = {
      start: jest.fn(async () => {}),
      stop: jest.fn(async (): Promise<RecordingResult> => ({ uri: 'file:///r.m4a', durationMillis: 3000 })),
    };
    const audioService = new AudioService(recorder);
    const uploadRecording = (_result: RecordingResult) =>
      apiClient.generateNote(new Uint8Array([1, 2, 3]), 'audio/m4a');
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

    await waitFor(() => expect(onRecorded).toHaveBeenCalledTimes(1));
    const history = await apiClient.fetchHistory();
    expect(history).toHaveLength(1);
    expect(onRecorded).toHaveBeenCalledWith(expect.objectContaining({ id: history[0].id }));
  });

  it('history feed lists exams synced from the backend', async () => {
    const backend = new FakeBackend();
    backend.seedExam({ patient_name: 'Rex', assessment: 'Otitis externa' });
    backend.seedExam({ patient_name: 'Bella' });

    render(<HistoryScreen apiClient={client(backend)} />);

    await waitFor(() => expect(screen.getByText('Rex')).toBeTruthy());
    expect(screen.getByText('Bella')).toBeTruthy();
    expect(screen.getByText('Otitis externa')).toBeTruthy();
  });

  it('editor: editing and saving writes through to the backend', async () => {
    const backend = new FakeBackend();
    const seeded = backend.seedExam({ patient_name: 'Rex' });
    const apiClient = client(backend);
    const exam = await apiClient.getExam(seeded.id);

    render(<ExamEditor exam={exam} apiClient={apiClient} />);

    fireEvent.changeText(screen.getByTestId('field-assessment'), 'Gastroenteritis');
    fireEvent.press(screen.getByText(/save changes/i));

    await waitFor(() => expect(screen.getByText(/saved/i)).toBeTruthy());
    const persisted = await apiClient.getExam(seeded.id);
    expect(persisted.assessment).toBe('Gastroenteritis');
  });

  it('editor: tapping Inject enqueues a remote injection for this exam', async () => {
    const backend = new FakeBackend();
    const seeded = backend.seedExam({ patient_name: 'Rex' });
    const apiClient = client(backend);
    const exam = await apiClient.getExam(seeded.id);

    render(<ExamEditor exam={exam} apiClient={apiClient} />);

    fireEvent.press(screen.getByText(/inject into avimark/i));

    await waitFor(() => expect(screen.getByText(/sent to the desktop/i)).toBeTruthy());
    const pending = backend.injectionRequests();
    expect(pending).toHaveLength(1);
    expect(pending[0]).toMatchObject({ exam_id: seeded.id, status: 'pending' });
  });
});
