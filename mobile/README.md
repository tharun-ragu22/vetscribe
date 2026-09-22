# VetScribe Mobile

A cross-platform (iOS + Android) companion app for the VetScribe ecosystem: a portable
exam-room microphone, recorder, note reviewer, and remote AVImark injection trigger. It
talks to the same backend (`backend/`) the Windows tray app uses.

## Framework decision brief

**Chosen: Expo (React Native) + TypeScript, tested with Jest.**

The brief called for a single shared iOS/Android codebase, fast TDD, and robust native
audio recording — and, specifically, the ability to test on a **physical iPhone 13 Pro Max**.
That last constraint is decisive.

| Criterion | Expo / React Native | Flutter | Kotlin Multiplatform |
|---|---|---|---|
| Single shared iOS+Android codebase | ✅ | ✅ | ⚠️ shared logic; UI still per-platform (Compose MP maturing) |
| Test on a physical iPhone **without a Mac/Xcode** | ✅ Expo Go / dev client — scan a QR code, runs over Wi-Fi | ❌ needs Xcode + provisioning on macOS | ❌ needs Xcode on macOS |
| TDD loop speed | ✅ Jest in Node, sub-second, no simulator | ✅ `flutter test` fast | ⚠️ JVM tests fast; iOS tests need a Mac |
| Native audio recording | ✅ `expo-audio` (AAC/M4A, permissions) | ✅ `record` package | ⚠️ expect/actual bindings, more plumbing |
| Local `.env` config, no host env vars | ✅ built-in `.env` + `EXPO_PUBLIC_*` | ⚠️ `--dart-define` / extra pkg | ⚠️ Gradle/plist plumbing |
| Shares mental model with existing code | ✅ TypeScript, same DI-through-constructors style as the tray app | ❌ Dart | ❌ Kotlin |

Expo wins on the hard requirement (iPhone testing with no Mac in the loop here) while also
giving the fastest red→green cycle: the decision logic is plain TypeScript run under Jest in
Node — no emulator, no device — so a test file executes in well under a second.

### Architecture (mirrors the desktop app's dependency injection)

The tray app wires collaborators through `build_app()` and injects fakes in tests. We do the
same here. Each service owns its logic behind a small injectable interface; the native module
sits at the very edge and is the only untested part:

- `AudioService` owns the capture state machine (`idle → recording → processing → idle`) and
  depends only on a `Recorder` interface. Tests inject a `FakeRecorder`; the real
  `useExpoAudioRecorder` (wrapping `expo-audio`) is wired in only inside a screen. It follows
  the desktop's hard rule: a failure must **never** strand the machine — a failed start falls
  back to idle, a failed stop still resets to idle rather than getting stuck in processing.

## Getting started

```bash
cd mobile
npm install
cp .env.example .env        # then edit values for your clinic backend
npm test                    # Jest — the TDD suite (runs in Node, no device needed)
npm run typecheck           # tsc --noEmit
npm start                   # Expo dev server (QR code)
```

### Running on a physical iPhone 13 Pro Max

1. Install **Expo Go** from the App Store on the phone.
2. `npm start` on your dev machine, with the phone on the **same Wi-Fi**.
3. Scan the QR code with the Camera app → it opens in Expo Go.

Microphone recording works in Expo Go. If you later add native modules Expo Go doesn't bundle,
switch to a dev client: `npx expo run:ios` (needs a Mac) or an EAS build.

## Configuration (local `.env`, no host env vars)

Expo loads a local `.env` automatically. Only variables prefixed `EXPO_PUBLIC_` are exposed to
the app bundle. Copy `.env.example` → `.env` and fill in:

| Variable | Purpose |
|---|---|
| `EXPO_PUBLIC_VETSCRIBE_API_URL` | Base URL of the backend, e.g. `http://192.168.1.50:8000` |
| `EXPO_PUBLIC_VETSCRIBE_API_KEY` | Shared bearer secret (matches the backend's `VETSCRIBE_BACKEND_API_KEY`); leave blank if the backend is unauthenticated |

`.env` is git-ignored; `.env.example` is committed as the template.

## Testing

```bash
npm test               # run once
npm run test:watch     # TDD watch mode
```

Jest uses the `jest-expo` preset (transforms TypeScript and the Expo/RN ES modules). Pure-logic
services import no native module, so their suites run anywhere.

### Local dev note (this repo's WSL checkout)

`/workspace` here is a 9p/drvfs mount whose concurrent `rename` semantics break npm's installer.
`node_modules` is therefore installed on the native ext4 filesystem and symlinked in. This is a
dev-machine quirk only — CI and a normal clone just run `npm install` directly.
