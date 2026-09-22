import { File } from 'expo-file-system';

import type { AudioBody } from '../api/types';

/**
 * Reads a finished recording off disk into the raw bytes the ApiClient POSTs to the
 * backend. This is the untested native edge (expo-file-system): the decision logic
 * lives in AudioService/ApiClient, and only meaningful on a device with a real file.
 */
export async function readRecording(uri: string): Promise<AudioBody> {
  return new File(uri).arrayBuffer();
}
