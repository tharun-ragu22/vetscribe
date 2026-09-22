import { useState } from 'react';
import { Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';

import type { ApiClient } from '../services/api/ApiClient';
import type { Exam, SoapNote } from '../services/api/types';

export interface ExamEditorProps {
  exam: Exam;
  /** Editing writes through updateExam; the Inject button uses requestInjection. */
  apiClient: Pick<ApiClient, 'updateExam' | 'requestInjection'>;
  /** Called with the persisted exam after a successful save. */
  onSaved?: (exam: Exam) => void;
}

const SECTIONS: ReadonlyArray<readonly [keyof SoapNote, string]> = [
  ['subjective', 'Subjective'],
  ['objective', 'Objective'],
  ['assessment', 'Assessment'],
  ['plan', 'Plan'],
  ['transcript', 'Transcript'],
];

type SaveStatus = 'idle' | 'saving' | 'saved' | 'error';
type InjectStatus = 'idle' | 'sending' | 'sent' | 'error';

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/**
 * The inline SOAP editor (feature B) plus the remote AVImark trigger (feature C).
 *
 * Save writes the edited note through to the backend, which is the authoritative
 * record. "Inject into AVImark" asks the backend to have this exam's note pasted into
 * AVImark on the exam-room PC — the phone never talks to the desktop directly; the
 * desktop tray app polls for the request and does the paste (or shows its Safety
 * Flyout). It's a fire-and-forget request that returns as soon as it's queued.
 */
export function ExamEditor({ exam, apiClient, onSaved }: ExamEditorProps) {
  const [note, setNote] = useState<SoapNote>({
    subjective: exam.subjective,
    objective: exam.objective,
    assessment: exam.assessment,
    plan: exam.plan,
    transcript: exam.transcript,
  });
  const [saveStatus, setSaveStatus] = useState<SaveStatus>('idle');
  const [saveError, setSaveError] = useState<string | null>(null);
  const [injectStatus, setInjectStatus] = useState<InjectStatus>('idle');
  const [injectError, setInjectError] = useState<string | null>(null);

  const setField = (key: keyof SoapNote, value: string) => {
    setNote((current) => ({ ...current, [key]: value }));
    // Any edit invalidates a prior "Saved" confirmation.
    setSaveStatus('idle');
  };

  const handleSave = async () => {
    setSaveStatus('saving');
    setSaveError(null);
    try {
      const updated = await apiClient.updateExam(exam.id, note);
      setSaveStatus('saved');
      onSaved?.(updated);
    } catch (e) {
      setSaveError(messageOf(e));
      setSaveStatus('error');
    }
  };

  const handleInject = async () => {
    setInjectStatus('sending');
    setInjectError(null);
    try {
      await apiClient.requestInjection(exam.id);
      setInjectStatus('sent');
    } catch (e) {
      setInjectError(messageOf(e));
      setInjectStatus('error');
    }
  };

  const saveLabel = saveStatus === 'saving' ? 'Saving…' : 'Save Changes';
  const injectLabel = injectStatus === 'sending' ? 'Sending…' : 'Inject into AVImark';

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {exam.patientName ? <Text style={styles.patient}>{exam.patientName}</Text> : null}

      {SECTIONS.map(([key, label]) => (
        <View key={key} style={styles.field}>
          <Text style={styles.label}>{label}</Text>
          <TextInput
            testID={`field-${key}`}
            style={styles.input}
            value={note[key]}
            onChangeText={(value) => setField(key, value)}
            multiline
          />
        </View>
      ))}

      <Pressable
        accessibilityRole="button"
        style={[styles.button, styles.save, saveStatus === 'saving' && styles.busy]}
        onPress={handleSave}
        disabled={saveStatus === 'saving'}
      >
        <Text style={styles.buttonText}>{saveLabel}</Text>
      </Pressable>
      {saveStatus === 'saved' ? <Text style={styles.ok}>Saved ✓</Text> : null}
      {saveStatus === 'error' ? (
        <Text style={styles.error}>Save failed: {saveError}</Text>
      ) : null}

      <Pressable
        accessibilityRole="button"
        style={[styles.button, styles.inject, injectStatus === 'sending' && styles.busy]}
        onPress={handleInject}
        disabled={injectStatus === 'sending'}
      >
        <Text style={styles.buttonText}>{injectLabel}</Text>
      </Pressable>
      {injectStatus === 'sent' ? (
        <Text style={styles.ok}>Sent to the desktop — it will paste into AVImark.</Text>
      ) : null}
      {injectStatus === 'error' ? (
        <Text style={styles.error}>Injection request failed: {injectError}</Text>
      ) : null}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    padding: 16,
    gap: 14,
    backgroundColor: '#fff',
  },
  patient: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1b3a5b',
  },
  field: {
    gap: 4,
  },
  label: {
    fontSize: 13,
    fontWeight: '700',
    color: '#6b7480',
    textTransform: 'uppercase',
  },
  input: {
    minHeight: 44,
    borderWidth: 1,
    borderColor: '#ccd4dc',
    borderRadius: 8,
    padding: 10,
    fontSize: 15,
    color: '#1a1a1a',
    textAlignVertical: 'top',
  },
  button: {
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  save: {
    backgroundColor: '#1b3a5b',
  },
  inject: {
    backgroundColor: '#1b7f4b',
  },
  busy: {
    opacity: 0.6,
  },
  buttonText: {
    color: '#fff',
    fontSize: 17,
    fontWeight: '700',
  },
  ok: {
    color: '#1b7f4b',
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
  },
  error: {
    color: '#c0392b',
    fontSize: 14,
    textAlign: 'center',
  },
});
