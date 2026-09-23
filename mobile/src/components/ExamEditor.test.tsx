import { fireEvent, render, screen, waitFor } from '@testing-library/react-native';

import type { ApiClient } from '../services/api/ApiClient';
import type { Exam } from '../services/api/types';
import { ExamEditor } from './ExamEditor';

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

type EditorApi = Pick<ApiClient, 'updateExam' | 'requestInjection' | 'deleteExam'>;

function makeApiClient(overrides: Partial<EditorApi> = {}): EditorApi {
  return {
    updateExam: jest.fn(async (_id: string, note) => makeExam(note)),
    requestInjection: jest.fn(async () => ({
      id: 'req-1',
      examId: 'exam-1',
      createdAt: '2026-09-22T10:05:00Z',
      status: 'pending',
      outcome: null,
    })),
    deleteExam: jest.fn(async () => {}),
    ...overrides,
  } as unknown as EditorApi;
}

describe('ExamEditor', () => {
  it('pre-fills the SOAP fields from the exam', () => {
    render(<ExamEditor exam={makeExam()} apiClient={makeApiClient()} />);

    expect(screen.getByTestId('field-subjective').props.value).toBe('S');
    expect(screen.getByTestId('field-objective').props.value).toBe('O');
    expect(screen.getByTestId('field-assessment').props.value).toBe('A');
    expect(screen.getByTestId('field-plan').props.value).toBe('P');
  });

  it('saves edited fields back to the backend and confirms', async () => {
    const apiClient = makeApiClient();
    const onSaved = jest.fn();
    render(<ExamEditor exam={makeExam()} apiClient={apiClient} onSaved={onSaved} />);

    fireEvent.changeText(screen.getByTestId('field-assessment'), 'kennel cough');
    fireEvent.press(screen.getByText(/save changes/i));

    await waitFor(() => expect(screen.getByText(/saved/i)).toBeTruthy());
    expect(apiClient.updateExam).toHaveBeenCalledWith('exam-1', {
      subjective: 'S',
      objective: 'O',
      assessment: 'kennel cough',
      plan: 'P',
      transcript: 'vet: hello',
    });
    expect(onSaved).toHaveBeenCalledTimes(1);
  });

  it('surfaces a save failure', async () => {
    const apiClient = makeApiClient({
      updateExam: jest.fn(async () => {
        throw new Error('backend returned 502');
      }),
    });
    render(<ExamEditor exam={makeExam()} apiClient={apiClient} />);

    fireEvent.press(screen.getByText(/save changes/i));

    await waitFor(() => expect(screen.getByText(/502/)).toBeTruthy());
  });

  it('requests a remote AVImark injection for this exam and confirms it was sent', async () => {
    const apiClient = makeApiClient();
    render(<ExamEditor exam={makeExam({ id: 'exam-77' })} apiClient={apiClient} />);

    fireEvent.press(screen.getByText(/inject into avimark/i));

    await waitFor(() => expect(screen.getByText(/sent to the desktop/i)).toBeTruthy());
    expect(apiClient.requestInjection).toHaveBeenCalledWith('exam-77');
  });

  it('surfaces an injection request failure', async () => {
    const apiClient = makeApiClient({
      requestInjection: jest.fn(async () => {
        throw new Error('backend returned 404');
      }),
    });
    render(<ExamEditor exam={makeExam()} apiClient={apiClient} />);

    fireEvent.press(screen.getByText(/inject into avimark/i));

    await waitFor(() => expect(screen.getByText(/404/)).toBeTruthy());
  });

  it('requires a confirming second tap before deleting, then removes it', async () => {
    const apiClient = makeApiClient();
    const onDeleted = jest.fn();
    render(
      <ExamEditor exam={makeExam({ id: 'exam-9' })} apiClient={apiClient} onDeleted={onDeleted} />,
    );

    // First tap only arms the confirmation — nothing is deleted yet.
    fireEvent.press(screen.getByText(/^delete exam$/i));
    expect(apiClient.deleteExam).not.toHaveBeenCalled();
    expect(screen.getByText(/tap again/i)).toBeTruthy();

    // Second tap performs the delete and notifies the caller.
    fireEvent.press(screen.getByText(/tap again/i));
    await waitFor(() => expect(onDeleted).toHaveBeenCalledTimes(1));
    expect(apiClient.deleteExam).toHaveBeenCalledWith('exam-9');
  });

  it('surfaces a delete failure and does not notify the caller', async () => {
    const apiClient = makeApiClient({
      deleteExam: jest.fn(async () => {
        throw new Error('backend returned 500');
      }),
    });
    const onDeleted = jest.fn();
    render(<ExamEditor exam={makeExam()} apiClient={apiClient} onDeleted={onDeleted} />);

    fireEvent.press(screen.getByText(/^delete exam$/i));
    fireEvent.press(screen.getByText(/tap again/i));

    await waitFor(() => expect(screen.getByText(/500/)).toBeTruthy());
    expect(onDeleted).not.toHaveBeenCalled();
  });
});
