# Voicebox Corebrandings 0.6.0-local.1: included fixes

Reviewed on 2026-10-09. The latest official public installer was 0.5.0 (2026-04-25). This unofficial preview is based on the upstream 0.6.0 preparation commit a00d271, plus the frozen Torch startup fix 82caf7d and the Qwen sampler backport from mlx-audio PR 914.

The upstream 0.6.0 stability batch is included. Later unreleased engines, cloud services, external LLM integrations and export features are outside this selected baseline. Unknown or unresolved bugs are not considered fixed by this preview.

## Apple Silicon and shared application fixes

| Problem | Upstream source | Included behavior |
|---|---|---|
| Qwen long-form speech progressively accelerates | [mlx-audio 914](https://github.com/Blaizzy/mlx-audio/pull/914) | Use the most recent 64 audio tokens for repetition penalties in single and batch samplers |
| MLX load/inference across threads can crash with Stream(gpu, 1) | [1154](https://github.com/jamiepine/voicebox/pull/1154) | One MLX worker for TTS, Whisper and Qwen LLM; submit loading and inference together |
| GPU memory remains after model unload | [1161](https://github.com/jamiepine/voicebox/pull/1161) | Clear prompt caches and MLX allocations; handle failed inference references and unload during inference |
| Repeated generations grow memory usage | [1149](https://github.com/jamiepine/voicebox/pull/1149) | Cleanup after normal and streaming generations; cleanup failures do not invalidate successful results |
| Qwen runaway output and noisy tails | [964](https://github.com/jamiepine/voicebox/pull/964) | Detect unusually long output, split and retry; trim when no further split is possible |
| Complete cached models keep retrying online while offline | [1130](https://github.com/jamiepine/voicebox/pull/1130) | Scoped offline loads for complete caches; missing essential files remain downloadable |
| Qwen LLM sets the entire process offline | [924](https://github.com/jamiepine/voicebox/pull/924) | Remove global offline-state pollution |
| Failed downloads still appear active | [926](https://github.com/jamiepine/voicebox/pull/926), [1133](https://github.com/jamiepine/voicebox/pull/1133) | Filter errored tasks and detect stale incomplete downloads |
| Broken log pipes break backend requests after frontend exit | [1141](https://github.com/jamiepine/voicebox/pull/1141) | Pipe-safe logging |
| SQLite locks during concurrent work | [1136](https://github.com/jamiepine/voicebox/pull/1136) | WAL and a five-second busy timeout |
| Slow history and story queries | [1139](https://github.com/jamiepine/voicebox/pull/1139), [1143](https://github.com/jamiepine/voicebox/pull/1143), [663](https://github.com/jamiepine/voicebox/pull/663) | Indexes and batched queries |
| Partial profile deletion and orphaned records | [1148](https://github.com/jamiepine/voicebox/pull/1148) | Atomic commit and file-lock handling; deleting a profile also removes its generations, with a UI warning |
| Model load/unload always acts on Qwen | [1138](https://github.com/jamiepine/voicebox/pull/1138) | Honor the requested model |
| Default engine ignores profile configuration | [1140](https://github.com/jamiepine/voicebox/pull/1140) | Use the profile's configured engine |
| Failed-generation audio returns a server error | [893](https://github.com/jamiepine/voicebox/pull/893) | Return not found |
| Avatar uploads without filenames fail | [954](https://github.com/jamiepine/voicebox/pull/954) | Validate filenames |
| Dictation requires an LLM with refinement disabled | [1147](https://github.com/jamiepine/voicebox/pull/1147) | Require the LLM only when refinement is enabled |
| Uploaded WebM recordings fail transcription | [957](https://github.com/jamiepine/voicebox/pull/957), [903](https://github.com/jamiepine/voicebox/pull/903) | Preserve extensions and transcode to WAV |
| Dictation fails to paste into some Electron applications | [952](https://github.com/jamiepine/voicebox/pull/952) | Correct macOS Command modifier flags |
| fn cannot be used as a dictation hotkey | [950](https://github.com/jamiepine/voicebox/pull/950) | Support fn |
| speak/MCP defaults a Chinese profile to English | [1137](https://github.com/jamiepine/voicebox/pull/1137) | Use the profile's language |
| MCP clients reject tool names containing periods | [1135](https://github.com/jamiepine/voicebox/pull/1135) | Use underscore names such as voicebox_speak; older configurations need updating |
| Kokoro short scripts have silence/noise at the edges | [1150](https://github.com/jamiepine/voicebox/pull/1150) | Trim only the edges and preserve internal pauses |
| Four male Mandarin Kokoro voices are missing | [788](https://github.com/jamiepine/voicebox/pull/788) | Add the missing entries |
| Chatterbox Multilingual uses a slow CPU path on Apple Silicon | [1162](https://github.com/jamiepine/voicebox/pull/1162) | MLX path, cache checks and runaway-output retries |
| Long errors are truncated | [1134](https://github.com/jamiepine/voicebox/pull/1134) | Show a summary and allow copying the original error |
| Generation model/language menus are clipped | [936](https://github.com/jamiepine/voicebox/pull/936) | Open menus upward |
| Repeated text produces duplicate export filenames | [956](https://github.com/jamiepine/voicebox/pull/956) | Include generation IDs |
| Incorrect time display | [953](https://github.com/jamiepine/voicebox/pull/953), [1146](https://github.com/jamiepine/voicebox/pull/1146) | Consistent UTC handling |
| Older frontend seroval version | [1132](https://github.com/jamiepine/voicebox/pull/1132) | Use upstream's locked seroval 1.5.3 |

The [82caf7d startup fix](https://github.com/jamiepine/voicebox/commit/82caf7d) waits until Torch has finished importing before wrapping from_numpy and corrects the NumPy fallback variable reference.

## Validation boundaries

The selected source also contains fixes for Windows, Linux, Docker, ROCm, PyTorch long-audio transcription and TADA. This installer targets Apple Silicon macOS only; those paths were not tested on this machine.

The frontend and native Mac program are compiled from source. The full Python backend is rebuilt on the original 0.5.0 Python 3.12 runtime. Other third-party dependencies are retained, except for the Qwen sampler backport. Non-backend Python modules and native dependency contents are compared against the verified original. Icons reuse the original compiled resources.

This is not a blanket upgrade of third-party libraries. The validation summary records the selected checks that actually passed. Other undownloaded models have not been tested with real synthesis. Subjective long-form pacing and multiple Mac models still need validation.

Sources: [upstream 0.6.0 changelog](https://github.com/jamiepine/voicebox/blob/a00d271/CHANGELOG.md), [baseline source comparison](https://github.com/jamiepine/voicebox/compare/v0.5.0...a00d271), [official releases](https://github.com/jamiepine/voicebox/releases).
