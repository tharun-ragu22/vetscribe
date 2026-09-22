import { createContext, useContext, useMemo, type ReactNode } from 'react';

import { loadConfig } from '../config/env';
import { ApiClient } from './api/ApiClient';
import type { Exam } from './api/types';
import { AudioService } from './audio/AudioService';
import { readRecording } from './audio/readRecording';
import type { RecordingResult } from './audio/types';
import { useExpoAudioRecorder } from './audio/useExpoAudioRecorder';

/**
 * The app's wired collaborators, provided once at the root and consumed by the route
 * screens — the mobile analogue of the desktop app's build_app(). Screens receive
 * these through props for testability; only the route files reach for this context.
 */
export interface Services {
  apiClient: ApiClient;
  audioService: AudioService;
  /** Reads a finished recording off disk and uploads it, returning the created exam. */
  uploadRecording: (result: RecordingResult) => Promise<Exam>;
}

const ServicesContext = createContext<Services | null>(null);

export function ServicesProvider({ children }: { children: ReactNode }) {
  // The real microphone Recorder is hook-managed by expo-audio, so it must be
  // obtained here and fed into the AudioService instance.
  const recorder = useExpoAudioRecorder();

  const services = useMemo<Services>(() => {
    const config = loadConfig();
    const apiClient = new ApiClient({ baseUrl: config.apiUrl, apiKey: config.apiKey });
    const audioService = new AudioService(recorder);
    const uploadRecording = async (result: RecordingResult): Promise<Exam> => {
      const bytes = await readRecording(result.uri);
      // expo-audio's HIGH_QUALITY preset records AAC in an .m4a container.
      return apiClient.generateNote(bytes, 'audio/m4a');
    };
    return { apiClient, audioService, uploadRecording };
  }, [recorder]);

  return <ServicesContext.Provider value={services}>{children}</ServicesContext.Provider>;
}

export function useServices(): Services {
  const services = useContext(ServicesContext);
  if (!services) {
    throw new Error('useServices must be used within a ServicesProvider');
  }
  return services;
}
