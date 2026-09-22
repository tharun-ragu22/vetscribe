/**
 * Jest is our TDD runner: it executes in Node (no simulator/device needed), so the
 * red->green loop is sub-second. The `jest-expo` preset transforms TypeScript via
 * babel-preset-expo and knows how to transform the Expo/React Native ES modules that
 * would otherwise choke Node's CommonJS require.
 *
 * The pure-logic services (AudioService, ApiClient) are written against injectable
 * interfaces so their tests import no native module at all — they run anywhere.
 * Component tests pull in the RN renderer through this same preset.
 */
module.exports = {
  preset: 'jest-expo',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  transformIgnorePatterns: [
    'node_modules/(?!((jest-)?react-native|@react-native(-community)?|expo(nent)?|@expo(nent)?/.*|@expo-google-fonts/.*|react-navigation|@react-navigation/.*|@unimodules/.*|unimodules|sentry-expo|native-base|react-clone-referenced-element))',
  ],
  collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/**/*.d.ts'],
  testTimeout: 30000,
};
