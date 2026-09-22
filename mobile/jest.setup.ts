import { configure } from '@testing-library/react-native';

// The first component test in a run pays React Native's one-time cold-start cost,
// which can push an async render past RNTL's default 1s waitFor window (more so on
// slower CI runners). Give async assertions more headroom so a warm-up cost never
// masquerades as a real failure.
configure({ asyncUtilTimeout: 8000 });
