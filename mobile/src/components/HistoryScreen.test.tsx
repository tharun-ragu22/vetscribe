import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import type { ApiClient } from '../services/api/ApiClient';
import type { Exam } from '../services/api/types';
import { HistoryScreen } from './HistoryScreen';

function makeExam(overrides: Partial<Exam> = {}): Exam {
  return {
    id: 'exam-1',
    createdAt: '2026-09-22T10:00:00Z',
    patientName: 'Rex',
    subjective: 'S',
    objective: 'O',
    assessment: 'A',
    plan: 'P',
    transcript: 'vet: hello',
    ...overrides,
  };
}

/** A fake exposing just the ApiClient surface HistoryScreen depends on. */
function makeApiClient(fetchHistory: jest.Mock): Pick<ApiClient, 'fetchHistory'> {
  return { fetchHistory } as unknown as Pick<ApiClient, 'fetchHistory'>;
}

describe('HistoryScreen', () => {
  it('loads and renders the synced exams newest-first', async () => {
    const exams = [
      makeExam({ id: 'exam-1', patientName: 'Rex' }),
      makeExam({ id: 'exam-2', patientName: 'Bella' }),
    ];
    const fetchHistory = jest.fn(async () => exams);
    render(<HistoryScreen apiClient={makeApiClient(fetchHistory)} />);

    await waitFor(() => expect(screen.getByText('Rex')).toBeTruthy());
    expect(screen.getByText('Bella')).toBeTruthy();
    expect(fetchHistory).toHaveBeenCalledTimes(1);
  });

  it('shows an empty state when there are no exams', async () => {
    const fetchHistory = jest.fn(async () => []);
    render(<HistoryScreen apiClient={makeApiClient(fetchHistory)} />);

    await waitFor(() => expect(screen.getByText(/no exams yet/i)).toBeTruthy());
  });

  it('shows an error with a retry that refetches', async () => {
    const fetchHistory = jest
      .fn()
      .mockRejectedValueOnce(new Error('backend returned 502'))
      .mockResolvedValueOnce([makeExam({ patientName: 'Rex' })]);
    render(<HistoryScreen apiClient={makeApiClient(fetchHistory)} />);

    await waitFor(() => expect(screen.getByText(/couldn't load/i)).toBeTruthy());

    fireEvent.press(screen.getByText(/retry/i));

    await waitFor(() => expect(screen.getByText('Rex')).toBeTruthy());
    expect(fetchHistory).toHaveBeenCalledTimes(2);
  });

  it('opens an exam when its row is tapped', async () => {
    const fetchHistory = jest.fn(async () => [makeExam({ id: 'exam-42', patientName: 'Rex' })]);
    const onOpenExam = jest.fn();
    render(<HistoryScreen apiClient={makeApiClient(fetchHistory)} onOpenExam={onOpenExam} />);

    await waitFor(() => expect(screen.getByText('Rex')).toBeTruthy());
    fireEvent.press(screen.getByTestId('exam-row-exam-42'));

    expect(onOpenExam).toHaveBeenCalledWith('exam-42');
  });
});
