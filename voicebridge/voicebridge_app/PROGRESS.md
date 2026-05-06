# VoiceBridge Progress — 2026-04-30

## Phase 0 — Cleanup ✅
- Deleted `pipeline_mobile.dart` (empty placeholder)
- Removed PDF button from `results_screen.dart` (already clean)
- Removed broken `postIntake(audioBytes)` from `voicebridge_api.dart`
- Updated `pipeline_web.dart` to throw `UnimplementedError` for audio (temporarily)
- Fixed imports in `pipeline_provider.dart` (removed MobilePipeline)
- Flutter analyze: clean (only pre-existing deprecation warnings)
- Backend text input confirmed working

## Phase 1 — Backend ✅
- Replaced `llama-cli` subprocess calls with `llama-cpp-python` chat API
- Model loads once via `_get_model()`, reuses across requests
- `/intake/text` returns correct JSON: `triage_level`, `primary_complaint`, `red_flag_indicators`, `recommended_action`, `confidence_score`, `latency_s`, `lang`
- `/intake/audio` endpoint added (uses `llama-mtmd-cli` subprocess for multimodal)
- CORS middleware already configured
- Backend runs in WSL (Ubuntu-24.04) on port 8000
- Test: cardiac arrest case → `triage_level: red`, `confidence: 1.0`, latency 8.65s

## Phase 2 — Flutter Backend Connection ✅
- Added `postIntake()` for audio upload with lang parameter
- Updated `postText()` and `postInteractive()` to pass lang
- Updated `VoicebridgePipeline` interface with lang parameter
- `WebPipeline` implements all methods with lang support
- `PipelineNotifier` reads lang from settings and passes through
- Fixed unused imports
- Flutter analyze: clean (no errors/warnings)

## Phase 3 — Polish ✅
- Added language selector (English, Swahili, Hausa, Bengali, Tagalog) to home screen
- Added offline banner: "Running offline — no data leaves your device"
- Updated triage colors:
  - RED: `0xFFD32F2F`
  - ORANGE: `0xFFE65100`
  - YELLOW: `0xFFF9A825`
  - GREEN: `0xFF2E7D32`
  - BLUE: `0xFF1565C0`
- `flutter build web --release` succeeded (23.8s)

## Phase 4 — Android ❌
- Failed: No Android SDK found on MAXIM-12700K
- Requires Android Studio installation or ANDROID_HOME setup
- Skipping Phase 4 entirely

## Final Checks
- Backend health: ✅ Running on WSL port 8000
- Text intake test: ✅ Returns correct JSON with `triage_level: red`
- Web build: ✅ `build/web` directory created

## What Needs Manual Attention
1. **Android SDK** — Install Android Studio or set ANDROID_HOME for Phase 4
2. **Screenshots** — Take screenshots of Home, Recording, Results (RED/GREEN), Interactive screens for Kaggle Media Gallery
3. **Audio endpoint testing** — `/intake/audio` needs WAV file test (llama-mtmd-cli dependency)
4. **Backend process** — Currently running in WSL background; needs proper service management for production

## Key Files Changed
- `api/main.py` — Added `/intake/audio`, updated `/intake/text` to use llama-cpp-python
- `pipeline/llama_infer.py` — Replaced subprocess with llama-cpp-python chat API
- `voicebridge_app/lib/data/api/voicebridge_api.dart` — Added lang parameter, restored `postIntake()`
- `voicebridge_app/lib/domain/pipeline/voicebridge_pipeline.dart` — Added lang parameter
- `voicebridge_app/lib/domain/pipeline/pipeline_web.dart` — Implemented lang support
- `voicebridge_app/lib/providers/pipeline_provider.dart` — Lang passthrough from settings
- `voicebridge_app/lib/features/home/home_screen.dart` — Language selector, offline banner
- `voicebridge_app/lib/core/theme/colors.dart` — Updated triage colors
