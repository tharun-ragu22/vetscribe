import type { Recorder, RecordingResult, RecordingState } from './types';

export interface AudioServiceOptions {
  /** Injectable clock (ms) so elapsed-time tracking is deterministic in tests. */
  now?: () => number;
  /** Fired on every state transition — the UI uses it to flip Idle/Recording/Processing. */
  onStateChange?: (state: RecordingState) => void;
}

/**
 * The exam-capture state machine: IDLE -> RECORDING -> PROCESSING -> IDLE.
 *
 * It mirrors the desktop Pipeline's hard rule (CLAUDE.md): a failure must never
 * leave the machine stuck. If the native recorder fails to start we fall back to
 * IDLE; if it fails to stop we still reset to IDLE rather than stranding the app in
 * PROCESSING, which would turn the record button into a silent no-op.
 *
 * The service owns only the state and timing; the actual microphone work lives
 * behind the injected Recorder, and uploading is the ApiClient's job.
 */
export class AudioService {
  private _state: RecordingState = 'idle';
  private _startedAt = 0;
  private _frozenElapsedMs = 0;
  private readonly now: () => number;
  private readonly onStateChange?: (state: RecordingState) => void;

  constructor(private readonly recorder: Recorder, options: AudioServiceOptions = {}) {
    this.now = options.now ?? Date.now;
    this.onStateChange = options.onStateChange;
  }

  get state(): RecordingState {
    return this._state;
  }

  get isRecording(): boolean {
    return this._state === 'recording';
  }

  /** Milliseconds elapsed: live while recording, frozen once stopped, 0 when idle. */
  get elapsedMs(): number {
    if (this._state === 'recording') {
      return this.now() - this._startedAt;
    }
    return this._frozenElapsedMs;
  }

  async start(): Promise<void> {
    if (this._state !== 'idle') {
      throw new Error(`cannot start: not idle (already ${this._state})`);
    }
    this._startedAt = this.now();
    this._frozenElapsedMs = 0;
    try {
      await this.recorder.start();
    } catch (error) {
      // Never advance the machine on a failed start (e.g. permission denied).
      this._startedAt = 0;
      throw error;
    }
    this.transition('recording');
  }

  async stop(): Promise<RecordingResult> {
    if (this._state !== 'recording') {
      throw new Error(`cannot stop: not recording (currently ${this._state})`);
    }
    // Freeze the timer at the moment of stop so the UI shows the final duration.
    this._frozenElapsedMs = this.now() - this._startedAt;
    this.transition('processing');
    try {
      return await this.recorder.stop();
    } catch (error) {
      // A failure escaping stop must still reset the machine, or the record
      // button becomes a silent no-op (mirrors the desktop PROCESSING rule).
      this.reset();
      throw error;
    }
  }

  /** Return to idle for the next exam (call after the upload completes or fails). */
  reset(): void {
    this._startedAt = 0;
    this._frozenElapsedMs = 0;
    this.transition('idle');
  }

  private transition(next: RecordingState): void {
    if (this._state === next) return;
    this._state = next;
    this.onStateChange?.(next);
  }
}
