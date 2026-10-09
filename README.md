# Voicebox · Corebrandings Community Preview

**0.6.0-local.1 · Apple Silicon · macOS 15+**

[Downloads](https://github.com/faintsierra86/corebrandings-voicebox/releases) · [Original project](https://github.com/jamiepine/voicebox)

An unofficial Apple Silicon maintenance build maintained by Corebrandings. Based on upstream's 0.6.0 preparation commit a00d271, plus the upstream frozen-Torch startup fix 82caf7d and the core Qwen repetition-history fix from mlx-audio PR #914. Upstream Voicebox remains the original project; this build is not an official release and does not imply endorsement.

## Requirements and installation

Apple Silicon Mac (M1 or later), macOS 15 or later. Intel Macs are not supported. MLX's bundled native libraries require macOS 15. No Python, Rust or Bun installation is needed to use the app.

Back up your Voicebox data before trying this preview. Wait for active tasks to finish and quit Voicebox. On the first switch from an existing install, restart the Mac to ensure that a retained old backend is not reused. Open the DMG and drag Voicebox Corebrandings into Applications. Keep the original application for rollback. The sidebar should show v0.6.0-local.1.

The preview shares the original bundle identifier and local data directory (~/Library/Application Support/sh.voicebox.app). Run only one version at a time. Switching versions does not undo user deletions. In this version, deleting a voice also deletes its generated recordings, as explained by the deletion dialog.

This build is ad-hoc signed and is not Apple notarized. macOS may require approval in System Settings > Privacy & Security. Do not disable system protections. SHA256SUMS.txt identifies the published artifacts.

## What is included

The merged upstream stability work includes MLX thread affinity, memory cleanup, cached offline loads, download state, runaway audio retries, database WAL/index/query fixes, macOS dictation paste, MCP language/tool-name fixes, and interface/export fixes. The Qwen sampler backport bounds repetition history to its most recent 64 tokens in both single and batch sampling.

The frontend and native Mac program are compiled from the upstream source with explicit local version, naming and minimum-OS changes. The Python application is rebuilt within the original 0.5.0 bundled runtime. Third-party dependencies are retained, except for the Qwen sampler backport. This is not an across-the-board upgrade of third-party libraries. Build scripts verify non-backend Python code and native dependency contents and record source provenance.

No personal voice profiles, reference recordings, generated audio, database or backup are included. Users create or import their own voices and download their chosen models.

## Validation and limits

108 selected upstream backend regression tests, 8 frozen-Qwen sampler tests and 6 frozen-Torch hook tests passed: 122 checks in total. Frontend type checking, production frontend/native compilation, code-signature verification, startup, a migration against a private copied database, a short real Qwen 1.7B generation and model unload were also checked.

Testing was conducted on one Apple Silicon Mac. The recording and private database used for validation are not distributed. Other Mac hardware, other undownloaded TTS engines and subjective long-form pacing have not been fully validated. This preview should be tested with a backup before production use. Report macOS version, chip, engine/model, chunk limit, steps and error text; share recordings only when you are permitted to make them public.

MCP tool names use underscores (voicebox_speak etc.) rather than dots. Update older client configurations accordingly. This preview uses manual updates from the community Releases page; it does not install upstream binaries automatically. Before adopting an official update, check whether it contains the repetition-window fix; it may replace this local patch.

## Credit, license and sources

Copyright belongs to the original Voicebox contributors and the respective dependency authors. The Voicebox and mlx-audio MIT notices are included; bundled dependencies retain their existing notices.

- Original project: https://github.com/jamiepine/voicebox
- Upstream baseline: https://github.com/jamiepine/voicebox/commit/a00d271
- Upstream stability notes: https://github.com/jamiepine/voicebox/blob/a00d271/CHANGELOG.md
- Frozen-Torch hook fix: https://github.com/jamiepine/voicebox/commit/82caf7d
- Qwen long-form pacing report: https://github.com/Blaizzy/mlx-audio/issues/910
- Qwen sampler fix: https://github.com/Blaizzy/mlx-audio/pull/914

Releases of the original project are controlled by its maintainers. This community preview is maintained separately. Source and local build scripts accompany the preview.
