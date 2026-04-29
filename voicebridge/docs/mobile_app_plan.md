# VoiceBridge Mobile App — Full Design Plan

## 1. Overview

**Goal:** A fully offline, cross-platform app (web-first for development, then Android + iOS) that runs the complete VoiceBridge clinical intake pipeline on-device. A community health worker records a patient intake in any language, Gemma 4 E4B transcribes and translates natively via its audio capability, the fine-tuned VoiceBridge model classifies triage, and the app displays a color-coded result — all without internet after initial model download.

**Framework:** Flutter (Dart) — single codebase targeting web (Chrome), Android, and iOS. Web-first development for rapid iteration on the laptop, then compile to native.

**Target devices:** Web (Chrome on laptop for dev/testing), mid-range Android phones (4-6 GB RAM), iPhone 13+.

**Kaggle context:** Gemma 4 Good Hackathon (deadline May 18). The app proves the "runs on an $80 device" claim. Judging: Innovation 30%, Impact 30%, Technical Execution 25%, Accessibility 15%.

**Build approach:** AI-assisted coding (Claude Code for heavy lifting). Plan is structured for rapid implementation — focused phases, not waterfall. Target: functional demo in 3-5 days of focused coding.

---

## 2. Design Language — "Glass Clinical"

### 2.1 Visual Identity

Glassmorphism (translucent frosted surfaces, blur, soft shadows) merged with clinical professionalism (clean hierarchy, medical color coding, no visual noise). A high-end medical device interface, not a consumer app.

### 2.2 Color Palette

| Role | Color | Hex | Usage |
|------|-------|-----|-------|
| Primary | Deep Navy | `#0D1B2A` | Headers, primary text, dark backgrounds |
| Secondary | Medical Teal | `#1B9AAA` | Accent buttons, active states, icons |
| Surface Light | Clinical White | `#F0F4F8` | Main background |
| Surface Glass | Translucent White | `rgba(255,255,255,0.72)` | Glass card backgrounds |
| Surface Glass Dark | Translucent Navy | `rgba(13,27,42,0.65)` | Dark glass overlays |
| Text Primary | Near Black | `#1A1A2E` | Body text |
| Text Secondary | Slate | `#5A6577` | Labels, hints, timestamps |
| Text on Glass | White | `#FFFFFF` | Text over dark glass |
| Success | Green | `#639922` | Positive confirmations |
| Error | Soft Red | `#E24B4A` | Errors, warnings |

### 2.3 SATS Triage Colors (authoritative)

| Level | Color | Hex | Meaning |
|-------|-------|-----|---------|
| RED | Crimson | `#E24B4A` | Immediate — life-threatening |
| ORANGE | Amber | `#EF9F27` | Very urgent — 10 minutes |
| YELLOW | Gold | `#EFD927` | Urgent — 60 minutes |
| GREEN | Green | `#639922` | Routine — 4 hours |
| BLUE | Steel Blue | `#378ADD` | Expectant — palliative |

### 2.4 Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| App title / banners | Inter | Bold (700) | 28-32px |
| Section headers | Inter | SemiBold (600) | 18-20px |
| Body text | Inter | Regular (400) | 14-16px |
| Labels / metadata | Inter | Medium (500) | 12-13px |
| Numbers / vitals | JetBrains Mono | Regular (400) | 16px |

### 2.5 Glassmorphism Tokens

```dart
BoxDecoration(
  color: Colors.white.withOpacity(0.72),
  borderRadius: BorderRadius.circular(20),
  boxShadow: [
    BoxShadow(
      color: Colors.black.withOpacity(0.06),
      blurRadius: 20,
      offset: Offset(0, 4),
    ),
  ],
  border: Border.all(
    color: Colors.white.withOpacity(0.5),
    width: 1.0,
  ),
)
```

### 2.6 Component Patterns

- **Cards:** Rounded (20px), translucent white, subtle border highlight, soft shadow
- **Buttons:** Pill-shaped (50px height), gradient fills for primary, glass outline for secondary
- **Icons:** Rounded line icons (2px stroke), teal active, slate inactive
- **Inputs:** Glass containers with bottom border accent, floating labels
- **Background:** Subtle gradient mesh — deep navy to teal, very low opacity. Animated gradient shift on home (5-second cycle)

---

## 3. App Architecture

### 3.1 Tech Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Framework | Flutter 3.27+ | Web + Android + iOS |
| Language | Dart 3.6+ | |
| State management | Riverpod 2.6+ | AsyncNotifier for pipeline |
| Navigation | go_router 14+ | Deep linking support |
| Local database | drift (SQLite ORM) | Mobile: SQLite. Web: in-memory store |
| Audio recording | record_plus | Web: MediaRecorder API. Mobile: native |
| Audio processing | WebAudio API (web) / FFI (mobile) | Resample, normalize, trim silence |
| ML inference (web) | HTTP to FastAPI localhost:8000 | Dev mode — RTX 5090 |
| ML inference (mobile) | llama.cpp via Dart FFI | On-device, offline |
| PDF generation | pdf package | On demand, shareable |
| File storage | path_provider | |

### 3.2 Platform Strategy

**Primary dev target: Flutter Web (Chrome on laptop).**
- Instant hot reload, zero device setup
- Two web modes:
  - **Dev mode (default):** App calls local FastAPI (`localhost:8000`) for inference. Tests full pipeline with real models on RTX 5090.
  - **WASM mode (demo):** llama.cpp WebAssembly runs inference in-browser. Limited by browser memory but proves the concept.
- Record audio in Chrome → send to FastAPI → get triage result → display. Full pipeline testable from day one.

**Secondary target: Android (native APK).**
- llama.cpp via FFI (native ARM, no WASM overhead)
- Full offline capability
- Production build for Kaggle demo

**Tertiary target: iOS.**
- Same codebase, compile when needed

### 3.3 Project Structure

```
voicebridge_app/
├── web/                              # Web build (dev target)
├── android/                          # Android native project
├── ios/                              # iOS native project
├── assets/
│   ├── models/
│   │   └── (models downloaded at runtime, not bundled)
│   ├── icons/
│   ├── fonts/
│   │   └── Inter/
│   └── images/
├── lib/
│   ├── main.dart                     # Entry point, platform detection
│   ├── app.dart                      # MaterialApp, router, theme
│   │
│   ├── core/
│   │   ├── theme/
│   │   │   ├── app_theme.dart        # Light + dark themes
│   │   │   ├── colors.dart           # Color palette
│   │   │   ├── typography.dart       # Text styles
│   │   │   └── glass.dart            # Glassmorphism widgets
│   │   ├── constants.dart
│   │   └── utils/
│   │       ├── date_formatter.dart
│   │       └── triage_level_utils.dart
│   │
│   ├── data/
│   │   ├── database/
│   │   │   ├── app_database.dart     # Drift database
│   │   │   ├── daos.dart
│   │   │   └── schemas.dart
│   │   ├── models/
│   │   │   ├── triage_output.dart    # TriageOutput data class
│   │   │   └── app_record.dart
│   │   └── api/
│   │       └── voicebridge_api.dart  # HTTP client for web dev mode
│   │
│   ├── domain/
│   │   ├── pipeline/
│   │   │   ├── voicebridge_pipeline.dart  # Orchestrator (abstract)
│   │   │   ├── pipeline_web.dart           # Web impl (HTTP to FastAPI)
│   │   │   ├── pipeline_mobile.dart        # Mobile impl (llama.cpp FFI)
│   │   │   ├── audio_processor.dart
│   │   │   └── pdf_generator.dart
│   │   └── inference/
│   │       ├── llama_bridge.dart     # FFI bindings (mobile)
│   │       └── model_manager.dart    # Sequential model loading
│   │
│   ├── features/
│   │   ├── splash/
│   │   │   └── splash_screen.dart
│   │   ├── home/
│   │   │   ├── home_screen.dart
│   │   │   └── widgets/
│   │   │       ├── quick_action_card.dart
│   │   │       ├── recent_cases_list.dart
│   │   │       └── stats_row.dart
│   │   ├── recording/
│   │   │   ├── recording_screen.dart
│   │   │   └── widgets/
│   │   │       ├── waveform_visualizer.dart
│   │   │       ├── record_button.dart
│   │   │       └── timer_display.dart
│   │   ├── processing/
│   │   │   ├── processing_screen.dart
│   │   │   └── widgets/
│   │   │       └── pipeline_progress.dart
│   │   ├── results/
│   │   │   ├── results_screen.dart
│   │   │   └── widgets/
│   │   │       ├── triage_banner.dart
│   │   │       ├── detail_card.dart
│   │   │       ├── red_flags_card.dart
│   │   │       └── action_card.dart
│   │   ├── history/
│   │   │   ├── history_screen.dart
│   │   │   └── widgets/
│   │   │       ├── case_card.dart
│   │   │       └── filter_chips.dart
│   │   └── settings/
│   │       └── settings_screen.dart
│   │
│   └── providers/
│       ├── pipeline_provider.dart
│       ├── database_provider.dart
│       ├── recording_provider.dart
│       └── settings_provider.dart
│
├── llms/                             # Native FFI bindings (mobile only)
│   └── android/src/main/jni/
│       ├── CMakeLists.txt
│       └── bindings.cpp
│
├── pubspec.yaml
└── test/
    ├── pipeline_test.dart
    └── triage_classifier_test.dart
```

### 3.4 State Management: Riverpod

Pipeline state machine via AsyncNotifier:

```dart
enum PipelineStatus { idle, recording, transcribing, triaging, done, error }

class PipelineState {
  final PipelineStatus status;
  final String? message;
  final TriageOutput? result;
  final Duration elapsed;
}

class PipelineNotifier extends AsyncNotifier<PipelineState> {
  // Web: delegates to FastAPI HTTP call
  // Mobile: delegates to llama.cpp FFI with sequential model loading
  Future<void> runPipeline(AudioFile file) async { /* platform-specific */ }
}
```

---

## 4. Screens and Page Flow

### 4.1 Screen Inventory

| # | Screen | Route | Purpose |
|---|--------|-------|---------|
| 1 | Splash | `/` | Loading screen, model/API readiness check |
| 2 | Home | `/home` | Dashboard, quick actions, recent cases |
| 3 | Recording | `/record` | Audio capture with waveform visualization |
| 4 | Processing | `/processing` | Pipeline progress with step-by-step animation |
| 5 | Results | `/results/:id` | Full triage result display |
| 6 | History | `/history` | Past cases list with search and filters |
| 7 | Case Detail | `/case/:id` | Individual case review |
| 8 | Settings | `/settings` | Model management, language, app config |

### 4.2 Navigation

Bottom navigation bar (Home, History, Settings) on main shell. Recording is a floating action button on Home.

```
Splash → Home (bottom nav: Home | History | Settings)
         │
         ├── FAB → /record → /processing → /results/:id
         │
         ├── /history → /case/:id → /results/:id
         │
         └── /settings
```

### 4.3 Detailed Screen Designs

---

#### Screen 1: Splash

Full-screen gradient (navy to teal). Centered: VoiceBridge logo, app name, tagline. Bottom: pulsing dot + status text.

**Behavior:** Check model/API readiness. Web mode: ping `localhost:8000/health`. Mobile: check GGUF files exist. If not ready: show setup prompt. Timeout 30s.

---

#### Screen 2: Home

1. **Header** (glass, 60px) — "VoiceBridge" title, settings icon
2. **Quick stats row** (glass cards, horizontal scroll) — cases today, RED/Orange count, avg processing time
3. **Primary action card** (large glass, 180px) — "New Patient Intake", Record + Upload buttons, animated gradient background
4. **Recent cases** (scrollable) — glass cards with triage color dot, timestamp, complaint, confidence. Max 5, then "View All"
5. **FAB** — teal gradient circle, mic icon, bottom-right → Recording

---

#### Screen 3: Recording

1. **Header** (glass, 56px) — back arrow, "Record Intake", language hint selector
2. **Language chips** (horizontal scroll) — Auto-detect (default), English, Swahili, French, Arabic, Hindi, Spanish, Portuguese, "More..."
3. **Waveform visualization** (center, 300px) — real-time audio waveform in teal. Idle: breathing animation. Recording: live amplitude. Dark glass background.
4. **Record button** (80px circle) — teal/white when idle, red/white with pulsing ring when recording
5. **Timer** — monospace "00:42", teal when recording
6. **Bottom bar** (glass, 60px) — upload file icon (left), "Stop & Process" (right, enabled when recording)

Auto-stop at 5 minutes max.

---

#### Screen 4: Processing

1. **Header** (glass, 56px) — "Processing", no back button
2. **Progress stepper** (vertical, center) — 5 steps with icons:
   - Preparing audio (waveform icon)
   - Detecting language (globe icon) → shows detected language
   - Transcribing (document icon) → shows live word count
   - Analyzing triage (brain icon) → "Running model..."
   - Generating report (clipboard icon)
   Active: teal glow. Done: checkmark + teal. Future: slate.
3. **Elapsed time** — monospace below stepper
4. **Audio preview** (bottom, glass card) — small waveform + duration

Auto-navigate to Results on completion after 1s delay.

---

#### Screen 5: Results

1. **Triage banner** (full width, 100px, solid SATS color — not glass, needs authority) — level + wait time
2. **Primary complaint** (glass card) — stethoscope icon, one-sentence diagnosis
3. **Symptoms** (glass card) — chip-style tags, teal background, scrollable
4. **Vital signs** (glass card) — grid of key-value pairs, monospace values
5. **Duration** (glass card, compact)
6. **Relevant history** (glass card, compact)
7. **Red flags** (glass card, red-tinted if any) — bullet list with warning icons
8. **Recommended action** (glass card, triage-color left border) — prominent
9. **Referral + confidence** (glass card, two columns) — YES/No + circular progress
10. **Source language** (glass card, compact)
11. **Action bar** (glass, fixed bottom, 70px) — Share (PDF), New Intake (teal), Save

---

#### Screen 6: History

1. **Header** (glass) — "Case History", search icon
2. **Search bar** (glass, appears on tap)
3. **Filter chips** (horizontal scroll) — All, RED, ORANGE, YELLOW, GREEN, BLUE
4. **Date group headers** — "Today", "Yesterday", "Apr 26"
5. **Case cards** (vertical list) — glass, 4px triage color bar, complaint, timestamp, language, confidence
6. **Empty state** — clipboard icon, "No cases yet"

Swipe to delete (with confirmation). Pull to refresh.

---

#### Screen 7: Case Detail

Same as Results but read-only. Header includes case ID + delete. Action bar: Share PDF + Delete only.

---

#### Screen 8: Settings

Sections (each glass card):
1. **Model Management** — model status badges, sizes, download/update buttons, total storage
2. **Language** — app language, default intake hint
3. **Audio** — max recording duration, quality
4. **Privacy** — "All data stored on-device" badge, clear all data
5. **Appearance** — Light/Dark/System theme
6. **About** — version, model info, credits, links

---

## 5. On-Device ML Pipeline

### 5.1 Model Strategy

**No Whisper.** Gemma 4 E4B handles audio natively — transcription, translation, and language detection in a single model pass.

| Component | Model | Format | Size | Role |
|-----------|-------|--------|------|------|
| Transcription | Gemma 4 E4B | GGUF Q4_K_M | ~2.6 GB | Audio → text + translation + language ID |
| Triage | voicebridge-merged-v2 | GGUF Q4_K_M | ~2.8 GB | English text → structured triage JSON |

**Why Gemma 4 native audio:**
- Single model: transcription + translation + language detection in one pass
- No separate Whisper model to load, quantize, or maintain
- Audio encoder trained on same data as language model — better coherence
- Existing server pipeline already uses this approach (`models/transcription.py`)
- Simpler memory management on mobile

### 5.2 Memory Management

Mid-range device: 4-6 GB RAM, ~3-4 GB available to app.

```
Strategy: Sequential loading — one model at a time.
  1. Load Gemma 4 E4B (~2.6 GB) → transcribe → unload
  2. Load VoiceBridge (~2.8 GB) → triage → keep loaded
  Peak usage: ~3.2 GB → fits in 4+ GB devices

Web dev mode: No model loading in browser.
  Inference runs on RTX 5090 via FastAPI.
  Browser memory: ~100 MB (Flutter web + audio buffer).
```

```dart
class ModelManager {
  llama_context? _ctx;
  String? _currentModel;

  Future<void> _loadModel(String path) async {
    if (_currentModel == path && _ctx != null) return;
    await _unload();
    _ctx = await _loadGGUF(path);
    _currentModel = path;
  }

  Future<void> _unload() async {
    if (_ctx != null) { llama_free(_ctx!); _ctx = null; _currentModel = null; }
  }

  Future<TriageOutput> runPipeline(AudioFile file) async {
    // Step 1: Transcribe with Gemma 4 E4B
    state = PipelineStatus.transcribing;
    await _loadModel(_e4bPath);
    final transcript = await _transcribeWithAudio(file);
    await _unload();  // Free 2.6 GB

    // Step 2: Triage with VoiceBridge
    state = PipelineStatus.triaging;
    await _loadModel(_vbPath);
    final result = await _triage(transcript.englishText);
    return result;
  }
}
```

### 5.3 Pipeline Steps

**Web dev mode (laptop, default during coding):**
```
Flutter web (Chrome)
  → Record audio (MediaRecorder API)
  → HTTP POST to FastAPI localhost:8000/intake
  → RTX 5090 runs full pipeline (Gemma E4B transcribe → VoiceBridge triage)
  → JSON response → App displays results
```
Zero model loading in browser. Tests the exact API contract. ~3-8 seconds end-to-end on RTX 5090.

**Mobile production mode (on-device inference):**
```
Step 1: Audio Capture
  └─ Record via microphone, 16 kHz mono float32, max 5 min

Step 2: Audio Preprocessing
  └─ Normalize amplitude, trim silence (>500ms), ensure 16 kHz mono

Step 3: Load Gemma 4 E4B
  └─ llama_load_model_from_file('gemma4-e4b-q4km.gguf')
  └─ ~2-3 seconds

Step 4: Transcribe (Gemma 4 native audio)
  └─ Feed audio tokens + prompt to Gemma 4 E4B
  └─ Prompt: "Transcribe and respond with JSON: {schema}"
  └─ Output: {original_text, english_text, detected_language}
  └─ Single pass: transcription + translation + language ID
  └─ ~3-8 seconds for 10-second clip
  └─ Unload Gemma 4 E4B (free memory)

Step 5: Load VoiceBridge
  └─ llama_load_model_from_file('voicebridge-q4km.gguf')
  └─ ~2-3 seconds

Step 6: Triage Classification
  └─ Build prompt from triage_system.txt
  └─ llama.cpp inference, temp=0.1, repeat_penalty=1.3, max_tokens=1024
  └─ Parse JSON → TriageOutput
  └─ ~5-12 seconds

Step 7: Persist
  └─ Save to SQLite (drift), generate PDF on demand
```

**Total time (mobile):** ~15-28 seconds including model loads. Faster on subsequent runs if VoiceBridge stays loaded.
**Total time (web dev):** ~3-8 seconds (RTX 5090, no model loading).

### 5.4 Triage Prompt (Mobile)

Same as server pipeline, primed for JSON output:

```
<start_of_turn>system
You are a clinical triage assistant (SATS 2023 / WHO ETAT). Language: {lang_name}.
Output ONLY a JSON object with exact fields:
  triage_level, primary_complaint, red_flag_indicators,
  recommended_action, confidence_score
All values in English.
[end_of_turn]
<start_of_turn>user
{transcript}
[end_of_turn]
<start_of_turn>model
{
```

### 5.5 FFI Bindings (Mobile)

llama.cpp via Dart FFI:
- Android: CMake build in `android/src/main/jni/`
- iOS: Precompiled xcframework
- Key bindings: `llama_backend_init`, `llama_load_model_from_file`, `llama_new_context`, `llama_decode`, `llama_sample_token`
- Audio: Gemma 4 processor encodes audio → multimodal tokens → feed to model

**Web mode:** No FFI. HTTP calls to FastAPI via `http` package. For WASM demo: llama.cpp WebAssembly via `package:js` interop.

```cmake
# android/src/main/jni/CMakeLists.txt
cmake_minimum_required(VERSION 3.18)
project(voicebridge_llms)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/llama.cpp llama_build)
add_library(voicebridge_llms SHARED bindings.cpp)
target_link_libraries(voicebridge_llms llama)
```

### 5.6 Model Download (First Launch, Mobile Only)

Web dev mode: no download needed (uses FastAPI on localhost).

Mobile: download GGUF files on first launch.
- Gemma 4 E4B Q4_K_M: ~2.6 GB from HuggingFace
- VoiceBridge Q4_K_M: ~2.8 GB from HuggingFace
- Show progress with estimated time
- Allow background download, retry with backoff

For Kaggle demo: bundle both models in direct APK (no Play Store size limit).

---

## 6. Database Schema (drift)

```dart
class TriageRecords extends Table {
  TextColumn id() => text().nullable()();  // UUID
  TextColumn primaryComplaint() => text()();
  TextColumn symptoms() => text()();  // JSON array string
  TextColumn vitalSigns() => text()();  // JSON object string
  TextColumn duration() => text()();
  TextColumn relevantHistory() => text().nullable()();
  TextColumn redFlags() => text()();  // JSON array string
  TextColumn recommendedAction() => text()();
  BoolColumn referralNeeded() => boolean()();
  RealColumn confidenceScore() => real()();
  TextColumn triageLevel() => text()();
  TextColumn sourceLanguage() => text()();
  TextColumn rawTranscript() => text()();
  DateTimeColumn createdAt() => dateTime()();
  TextColumn audioFilePath() => text().nullable()();
}

// Indexes
Index('idx_triage_level', {TriageRecords.triageLevel});
Index('idx_created_at', {TriageRecords.createdAt});
```

Web mode: in-memory drift database (no persistence needed during dev).

---

## 7. PDF Generation

Same output as server pipeline, using `pdf` package. Generated on demand when user taps "Share" — not auto-saved.

Color-coded A4 PDF: triage banner (SATS color), clinical summary table, red flags, recommended action, referral + confidence, disclaimer footer.

---

## 8. Build and Distribution

### 8.1 Web (Dev Target)

```bash
flutter run -d chrome
# or
flutter build web --web-renderer canvaskit
```

- Opens in Chrome at `http://localhost:XXXX`
- Connects to FastAPI at `localhost:8000`
- Full pipeline testable immediately

### 8.2 Android

```yaml
# android/app/build.gradle
minSdkVersion 26          # Android 8.0+ (FFI support)
targetSdkVersion 34
multiDexEnabled true
ndkVersion '26.1.10909125'
```

**APK sizes:**
- Without models: ~30 MB (Flutter engine + app)
- With both models bundled: ~5.4 GB (direct APK, demo only)
- Recommendation: ship lean APK, download models on first launch

### 8.3 Kaggle Demo Build

Direct APK with both models bundled. Install on mid-range Android device (Samsung A54, 6 GB RAM). Record full pipeline demo video.

---

## 9. Development Phases (AI-Coded, 3-5 Days)

### Phase 1: Scaffold + UI (Day 1)
- [ ] Create Flutter project with web + Android targets
- [ ] Set up Riverpod, go_router, drift
- [ ] Implement theme system (colors, typography, glassmorphism widgets)
- [ ] Build all 8 screen shells (layout only, no logic)
- [ ] Wire up navigation graph
- [ ] Bottom nav + FAB
- [ ] **Deliverable:** Navigable app with glass UI, no pipeline logic

### Phase 2: Web Pipeline Integration (Day 2)
- [ ] Implement `voicebridge_api.dart` (HTTP client for FastAPI)
- [ ] Wire Recording screen → audio capture → HTTP POST to `/intake`
- [ ] Parse TriageOutput from response
- [ ] Wire Processing screen with real progress states
- [ ] Wire Results screen with real data
- [ ] Wire History screen with FastAPI `/records` endpoint
- [ ] **Deliverable:** Full working pipeline on web via FastAPI. Testable on laptop.

### Phase 3: Results Polish + History (Day 3)
- [ ] Complete Results screen with all detail cards
- [ ] PDF generation and sharing
- [ ] History with filters, search, date grouping
- [ ] Case detail screen
- [ ] Database persistence (drift, mobile SQLite + web in-memory)
- [ ] Settings screen skeleton
- [ ] **Deliverable:** Feature-complete web app

### Phase 4: Mobile Inference (Day 4)
- [ ] Set up llama.cpp FFI bindings for Android
- [ ] Implement `pipeline_mobile.dart` with sequential model loading
- [ ] Model download flow
- [ ] Test on Android device/emulator
- [ ] Memory management verification
- [ ] **Deliverable:** On-device inference working on Android

### Phase 5: Polish + Demo (Day 5)
- [ ] Error handling and retry flows
- [ ] Dark mode
- [ ] Animations (page transitions, waveform, button feedback)
- [ ] Loading skeletons and empty states
- [ ] Accessibility (text scaling, screen reader labels)
- [ ] Settings screen complete
- [ ] Benchmark: measure latency, memory on target device
- [ ] Record demo video
- [ ] **Deliverable:** Demo-ready app

---

## 10. Performance Targets

| Metric | Web (dev) | Mobile (target) |
|--------|-----------|-----------------|
| App launch | < 1s | < 3s |
| Model load (E4B) | N/A (server) | < 5s |
| Model load (VoiceBridge) | N/A (server) | < 5s |
| Transcription (10s audio) | < 3s | < 8s |
| Triage inference | < 3s | < 12s |
| Full pipeline | < 8s | < 28s |
| Peak RAM | ~100 MB | < 4 GB |
| APK size (no models) | N/A | < 50 MB |

---

## 11. Risk Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Both models too large for 4 GB RAM | Crash | Sequential loading. Graceful "insufficient memory" message. |
| llama.cpp FFI issues on Android | No mobile inference | Web mode works independently. Test FFI early. |
| Gemma 4 audio accuracy in low-resource languages | Wrong transcription | Language hint selector. Show transcript for review (future). |
| Triage JSON parsing failures | Broken results | Robust regex JSON extraction. Show raw output on failure. |
| First launch download fails | App unusable (mobile) | Retry with backoff. Manual download link. Cache partial downloads. |
| Web audio recording issues | Can't test on laptop | Test in Chrome (best MediaRecorder support). Fallback to file upload. |

---

## 12. Files to Create

### New Flutter project
```
voicebridge_app/                    # New Flutter project (web + Android + iOS)
├── lib/                            # All Dart source (see 3.3)
├── web/                            # Web build
├── android/                        # Android with llama.cpp FFI
├── ios/                            # iOS (compile when needed)
├── assets/                         # Fonts, icons, images
└── test/                           # Unit tests
```

### Files to modify in existing repo
```
voicebridge/docs/mobile_app_plan.md  # This file
voicebridge/README.md                 # Add mobile app section
```

### GGUF model preparation (one-time, on MAXIM-12700K)
```bash
# Quantize fine-tuned model to Q4_K_M for mobile
cd ~/llama.cpp
./llama-quantize \
  C:/Users/Maxim/.openclaw/workspace/Gemma4Kaggle/voicebridge/models/voicebridge-merged-v2/model.safetensors \
  voicebridge-q4km.gguf \
  Q4_K_M

# Gemma 4 E4B Q4_K_M: obtain from HuggingFace or quantize similarly
```

---

## 13. Summary

**What we're building:** Flutter app (web-first, then Android/iOS) running the full VoiceBridge pipeline on-device. Gemma 4 E4B handles audio natively — no Whisper needed.

**Key decisions:**
- Flutter over React Native (FFI, rendering, hot reload on web)
- Gemma 4 E4B native audio for transcription (single model, no Whisper)
- voicebridge-merged-v2 Q4_K_M for triage (fine-tuned, 89% accuracy)
- Sequential model loading for mid-range device memory
- Web dev mode: HTTP to FastAPI on localhost — test full pipeline from day one
- Mobile: llama.cpp FFI, fully offline
- Glass clinical design (translucent cards, SATS colors, professional)

**8 screens:** Splash → Home → Recording → Processing → Results → History → Case Detail → Settings

**5 phases, 3-5 days** of AI-assisted coding. Web-first for rapid iteration, then Android for production demo.

**Kaggle deadline:** May 18, 2026.

---

*Plan created: 2026-04-28*
*VoiceBridge Mobile App — Gemma 4 Good Hackathon 2026*
