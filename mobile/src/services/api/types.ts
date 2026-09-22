/** The four SOAP sections plus the raw transcript — the editable body of a note. */
export interface SoapNote {
  subjective: string;
  objective: string;
  assessment: string;
  plan: string;
  transcript: string;
}

/** A persisted exam as the backend stores and syncs it across devices. */
export interface Exam extends SoapNote {
  id: string;
  createdAt: string;
  patientName?: string;
}

/** Raw audio payload accepted by generateNote (sent as the request body). */
export type AudioBody = ArrayBuffer | Uint8Array | Blob;
