import { useMemo } from 'react';
import {
  RecordingPresets,
  requestRecordingPermissionsAsync,
  setAudioModeAsync,
  useAudioRecorder,
} from 'expo-audio';

import type { Recorder, RecordingResult } from './types';

/**
 * The real microphone-backed Recorder, adapting expo-audio's hook API to our
 * Recorder interface. This is the thin, untested edge of the audio module: it only
 * translates between expo-audio and AudioService, which owns all the decision logic
 * and is exercised in Node against a fake Recorder.
 *
 * expo-audio is hook-first (the recorder instance is created and lifecycle-managed
 * by useAudioRecorder), so the native seam is a hook rather than a plain class. A
 * screen calls this hook and hands the returned Recorder to an AudioService. It is
 * only meaningful on a physical device, so it has no unit test.
 */
export function useExpoAudioRecorder(): Recorder {
  const recorder = useAudioRecorder(RecordingPresets.HIGH_QUALITY);

  return useMemo<Recorder>(
    () => ({
      async start(): Promise<void> {
        const permission = await requestRecordingPermissionsAsync();
        if (!permission.granted) {
          throw new Error('microphone permission denied');
        }
        // iOS records silently unless the session is switched into record mode.
        await setAudioModeAsync({ allowsRecording: true, playsInSilentMode: true });
        await recorder.prepareToRecordAsync();
        recorder.record();
      },
      async stop(): Promise<RecordingResult> {
        await recorder.stop();
        const uri = recorder.uri;
        const durationMillis = Math.round((recorder.currentTime ?? 0) * 1000);
        // Release record mode so playback behaves normally afterwards.
        await setAudioModeAsync({ allowsRecording: false });
        if (!uri) {
          throw new Error('recording produced no file');
        }
        return { uri, durationMillis };
      },
    }),
    [recorder],
  );
}
