import { router, useLocalSearchParams } from 'expo-router';
import { useEffect, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';

import { ExamEditor } from '../../components/ExamEditor';
import type { Exam } from '../../services/api/types';
import { useServices } from '../../services/context';

/**
 * Exam route: fetches the exam by id from the synced backend and hands it to the
 * editor. The editor owns the save + remote-inject behaviour; this route is just the
 * loader seam.
 */
export default function ExamRoute() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { apiClient } = useServices();
  const [exam, setExam] = useState<Exam | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setExam(null);
    setError(null);
    apiClient
      .getExam(id)
      .then((loaded) => {
        if (active) setExam(loaded);
      })
      .catch(() => {
        if (active) setError("Couldn't load this exam.");
      });
    return () => {
      active = false;
    };
  }, [apiClient, id]);

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  if (!exam) {
    return (
      <View style={styles.center}>
        <ActivityIndicator />
      </View>
    );
  }

  // After deletion the exam no longer exists, so leave this screen.
  return <ExamEditor exam={exam} apiClient={apiClient} onDeleted={() => router.back()} />;
}

const styles = StyleSheet.create({
  center: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    padding: 24,
    backgroundColor: '#fff',
  },
  error: {
    color: '#c0392b',
    fontSize: 16,
    textAlign: 'center',
  },
});
