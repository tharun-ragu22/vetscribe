import { router } from 'expo-router';

import { HistoryScreen } from '../components/HistoryScreen';
import { useServices } from '../services/context';

/** History route: the synced exam feed; tapping a row opens it in the editor. */
export default function HistoryRoute() {
  const { apiClient } = useServices();

  return (
    <HistoryScreen apiClient={apiClient} onOpenExam={(id) => router.push(`/exam/${id}`)} />
  );
}
