/** The three states the exam-capture UI reflects: Idle, Recording, Processing. */
export type RecordingState = 'idle' | 'recording' | 'processing';

/** The artifact a finished recording produces, ready to hand to the ApiClient. */
export interface RecordingResult {
  /** Local file URI of the captured audio (e.g. file:///.../rec.m4a). */
  uri: string;
  /** How long the recording ran, in milliseconds. */
  durationMillis: number;
}

/**
 * The thin native-audio seam. AudioService owns the state machine and depends only
 * on this interface, so tests inject a fake and the real ExpoAudioRecorder (wrapping
 * expo-audio) is wired in only at the app's edge — the same dependency-injection
 * pattern the desktop app uses through build_app().
 */
export interface Recorder {
  start(): Promise<void>;
  stop(): Promise<RecordingResult>;
}
