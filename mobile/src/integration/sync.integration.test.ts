import { ApiClient } from '../services/api/ApiClient';
import { FakeBackend } from './fakeBackend';

/**
 * Cross-device sync: two ApiClient instances (a phone and, say, another phone or the
 * desktop) talk to the same backend, so a note created or edited on one is visible on
 * the other. The backend is the single source of truth; clients keep no local copy.
 */
describe('cross-device sync (integration)', () => {
  function twoDevices() {
    const backend = new FakeBackend();
    const deviceA = new ApiClient({ baseUrl: 'http://clinic:8000', fetch: backend.fetch });
    const deviceB = new ApiClient({ baseUrl: 'http://clinic:8000', fetch: backend.fetch });
    return { backend, deviceA, deviceB };
  }

  it('an exam uploaded on one device shows up in history on another', async () => {
    const { deviceA, deviceB } = twoDevices();

    const created = await deviceA.generateNote(new Uint8Array([1, 2, 3]), 'audio/m4a');

    const history = await deviceB.fetchHistory();
    expect(history.map((e) => e.id)).toContain(created.id);
    const synced = history.find((e) => e.id === created.id)!;
    expect(synced.assessment).toBe(created.assessment);
    expect(synced.transcript).toBe(created.transcript);
  });

  it('an edit saved on one device is visible when the other re-fetches', async () => {
    const { deviceA, deviceB } = twoDevices();
    const created = await deviceA.generateNote(new Uint8Array([9]), 'audio/m4a');

    await deviceA.updateExam(created.id, {
      subjective: created.subjective,
      objective: created.objective,
      assessment: 'Kennel cough',
      plan: 'Doxycycline 5mg/kg BID x10d',
      transcript: created.transcript,
    });

    const seenByB = await deviceB.getExam(created.id);
    expect(seenByB.assessment).toBe('Kennel cough');
    expect(seenByB.plan).toBe('Doxycycline 5mg/kg BID x10d');
  });

  it('history is newest-first across uploads', async () => {
    const { deviceA, deviceB } = twoDevices();
    const first = await deviceA.generateNote(new Uint8Array([1]), 'audio/m4a');
    const second = await deviceA.generateNote(new Uint8Array([2]), 'audio/m4a');

    const history = await deviceB.fetchHistory();
    expect(history[0].id).toBe(second.id);
    expect(history[1].id).toBe(first.id);
  });

  it('enforces bearer auth when the backend is configured with a key', async () => {
    const backend = new FakeBackend({ apiKey: 'clinic-secret' });
    const authed = new ApiClient({
      baseUrl: 'http://clinic:8000',
      apiKey: 'clinic-secret',
      fetch: backend.fetch,
    });
    const unauthed = new ApiClient({ baseUrl: 'http://clinic:8000', fetch: backend.fetch });

    await expect(authed.fetchHistory()).resolves.toEqual([]);
    await expect(unauthed.fetchHistory()).rejects.toThrow(/401/);
  });
});
