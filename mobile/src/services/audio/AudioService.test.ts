import { AudioService } from './AudioService';
import type { Recorder, RecordingResult, RecordingState } from './types';

/**
 * A fake native recorder so the state-machine logic can be exercised in Node with
 * no microphone, no expo-audio, no device. Mirrors the desktop app's dependency
 * injection: the real ExpoAudioRecorder is swapped in only at the app's edge.
 */
class FakeRecorder implements Recorder {
  startCalls = 0;
  stopCalls = 0;
  result: RecordingResult = { uri: 'file:///rec.m4a', durationMillis: 4200 };
  startError: Error | null = null;
  stopError: Error | null = null;

  async start(): Promise<void> {
    this.startCalls += 1;
    if (this.startError) throw this.startError;
  }

  async stop(): Promise<RecordingResult> {
    this.stopCalls += 1;
    if (this.stopError) throw this.stopError;
    return this.result;
  }
}

describe('AudioService', () => {
  let recorder: FakeRecorder;

  beforeEach(() => {
    recorder = new FakeRecorder();
  });

  it('starts idle with no elapsed time', () => {
    const service = new AudioService(recorder);
    expect(service.state).toBe<RecordingState>('idle');
    expect(service.elapsedMs).toBe(0);
    expect(service.isRecording).toBe(false);
  });

  it('start() transitions idle -> recording and drives the native recorder once', async () => {
    const service = new AudioService(recorder);
    await service.start();
    expect(service.state).toBe('recording');
    expect(service.isRecording).toBe(true);
    expect(recorder.startCalls).toBe(1);
  });

  it('refuses to start again while already recording', async () => {
    const service = new AudioService(recorder);
    await service.start();
    await expect(service.start()).rejects.toThrow(/already recording|not idle/i);
    expect(recorder.startCalls).toBe(1);
  });

  it('stop() transitions recording -> processing and returns the recording result', async () => {
    const service = new AudioService(recorder);
    await service.start();
    const result = await service.stop();
    expect(result).toEqual({ uri: 'file:///rec.m4a', durationMillis: 4200 });
    expect(service.state).toBe('processing');
    expect(recorder.stopCalls).toBe(1);
  });

  it('refuses to stop when not recording', async () => {
    const service = new AudioService(recorder);
    await expect(service.stop()).rejects.toThrow(/not recording/i);
    expect(recorder.stopCalls).toBe(0);
  });

  it('reset() returns from processing back to idle for the next exam', async () => {
    const service = new AudioService(recorder);
    await service.start();
    await service.stop();
    service.reset();
    expect(service.state).toBe('idle');
    expect(service.elapsedMs).toBe(0);
  });

  it('notifies subscribers on every state transition', async () => {
    const seen: RecordingState[] = [];
    const service = new AudioService(recorder, { onStateChange: (s) => seen.push(s) });
    await service.start();
    await service.stop();
    service.reset();
    expect(seen).toEqual(['recording', 'processing', 'idle']);
  });

  it('tracks elapsed recording time from an injected clock, frozen after stop', async () => {
    let now = 1000;
    const service = new AudioService(recorder, { now: () => now });
    await service.start();
    now = 1000 + 7500;
    expect(service.elapsedMs).toBe(7500);
    await service.stop();
    now = 1000 + 999999; // wall clock keeps moving...
    expect(service.elapsedMs).toBe(7500); // ...but the timer is frozen at stop
  });

  it('reverts to idle (not stuck in recording) if the native recorder fails to start', async () => {
    recorder.startError = new Error('microphone permission denied');
    const service = new AudioService(recorder);
    await expect(service.start()).rejects.toThrow(/permission denied/);
    expect(service.state).toBe('idle');
  });

  it('never gets stuck in processing if stopping the native recorder fails', async () => {
    // Mirrors the desktop rule: a failure escaping stop must still reset the
    // state machine so the record button is not left a silent no-op.
    recorder.stopError = new Error('encoder crashed');
    const service = new AudioService(recorder);
    await service.start();
    await expect(service.stop()).rejects.toThrow(/encoder crashed/);
    expect(service.state).toBe('idle');
  });
});
