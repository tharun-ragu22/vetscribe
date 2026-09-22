import { loadConfig, ConfigError } from './env';

describe('loadConfig', () => {
  it('reads the API url and key from EXPO_PUBLIC_ env vars', () => {
    const config = loadConfig({
      EXPO_PUBLIC_VETSCRIBE_API_URL: 'http://192.168.1.50:8000',
      EXPO_PUBLIC_VETSCRIBE_API_KEY: 'secret',
    });
    expect(config.apiUrl).toBe('http://192.168.1.50:8000');
    expect(config.apiKey).toBe('secret');
  });

  it('treats a missing key as an empty (unauthenticated) key', () => {
    const config = loadConfig({ EXPO_PUBLIC_VETSCRIBE_API_URL: 'http://host:8000' });
    expect(config.apiKey).toBe('');
  });

  it('strips a trailing slash from the API url so path joins are clean', () => {
    const config = loadConfig({ EXPO_PUBLIC_VETSCRIBE_API_URL: 'http://host:8000/' });
    expect(config.apiUrl).toBe('http://host:8000');
  });

  it('throws a ConfigError when the API url is missing', () => {
    expect(() => loadConfig({})).toThrow(ConfigError);
  });
});
