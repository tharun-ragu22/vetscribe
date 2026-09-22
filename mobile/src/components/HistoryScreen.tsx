import { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from 'react-native';

import type { ApiClient } from '../services/api/ApiClient';
import type { Exam } from '../services/api/types';

export interface HistoryScreenProps {
  /** Only the read surface is needed here; the backend is the source of truth. */
  apiClient: Pick<ApiClient, 'fetchHistory'>;
  /** Called with the exam id when a row is tapped (route pushes the editor). */
  onOpenExam?: (id: string) => void;
}

type Status = 'loading' | 'ready' | 'error';

function formatDate(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleString();
}

/**
 * Feature B: the exam history feed, synced across mobile and desktop via the backend.
 * Loads on mount and exposes explicit loading / empty / error (with retry) states so a
 * transient backend hiccup never leaves a blank screen with no way forward.
 */
export function HistoryScreen({ apiClient, onOpenExam }: HistoryScreenProps) {
  const [status, setStatus] = useState<Status>('loading');
  const [exams, setExams] = useState<Exam[]>([]);

  const load = useCallback(async () => {
    setStatus('loading');
    try {
      const result = await apiClient.fetchHistory();
      setExams(result);
      setStatus('ready');
    } catch {
      setStatus('error');
    }
  }, [apiClient]);

  useEffect(() => {
    void load();
  }, [load]);

  if (status === 'loading') {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
        <Text style={styles.muted}>Loading…</Text>
      </View>
    );
  }

  if (status === 'error') {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>Couldn't load exams.</Text>
        <Pressable accessibilityRole="button" style={styles.retry} onPress={load}>
          <Text style={styles.retryText}>Retry</Text>
        </Pressable>
      </View>
    );
  }

  if (exams.length === 0) {
    return (
      <View style={styles.center}>
        <Text style={styles.muted}>No exams yet.</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={exams}
      keyExtractor={(exam) => exam.id}
      contentContainerStyle={styles.list}
      renderItem={({ item }) => (
        <Pressable
          testID={`exam-row-${item.id}`}
          accessibilityRole="button"
          style={styles.row}
          onPress={() => onOpenExam?.(item.id)}
        >
          <Text style={styles.patient}>{item.patientName ?? 'Unknown patient'}</Text>
          <Text style={styles.date}>{formatDate(item.createdAt)}</Text>
          <Text style={styles.snippet} numberOfLines={2}>
            {item.assessment || item.subjective || 'No note yet'}
          </Text>
        </Pressable>
      )}
    />
  );
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    padding: 24,
    backgroundColor: '#fff',
  },
  list: {
    padding: 12,
    gap: 10,
  },
  row: {
    padding: 16,
    borderRadius: 12,
    backgroundColor: '#f2f5f8',
    gap: 4,
  },
  patient: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1b3a5b',
  },
  date: {
    fontSize: 12,
    color: '#6b7480',
  },
  snippet: {
    fontSize: 14,
    color: '#333',
  },
  muted: {
    fontSize: 16,
    color: '#6b7480',
  },
  error: {
    fontSize: 16,
    color: '#c0392b',
    textAlign: 'center',
  },
  retry: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    backgroundColor: '#1b7f4b',
  },
  retryText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '700',
  },
});
