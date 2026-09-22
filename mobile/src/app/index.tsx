import { router } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';

import { RecorderScreen } from '../components/RecorderScreen';
import { useServices } from '../services/context';

/** Home route: one-tap exam capture, with a link into the synced history feed. */
export default function RecorderRoute() {
  const { audioService, uploadRecording } = useServices();

  return (
    <View style={styles.container}>
      <RecorderScreen
        audioService={audioService}
        uploadRecording={uploadRecording}
        onRecorded={(exam) => router.push(`/exam/${exam.id}`)}
      />
      <Pressable
        accessibilityRole="button"
        style={styles.historyLink}
        onPress={() => router.push('/history')}
      >
        <Text style={styles.historyLinkText}>View Exam History</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  historyLink: {
    alignItems: 'center',
    paddingVertical: 18,
  },
  historyLinkText: {
    color: '#1b3a5b',
    fontSize: 16,
    fontWeight: '600',
  },
});
