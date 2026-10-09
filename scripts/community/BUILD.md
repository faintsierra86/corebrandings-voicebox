# Building the Corebrandings community preview

Baseline: jamiepine/voicebox commit a00d271. The verified runtime input is the original Voicebox 0.5.0 Apple Silicon server. The builder checks its SHA256 and refuses other inputs.

1. Check out the community repository's corebrandings-preview branch. Alternatively, extract upstream-source.tar.gz from the source attachment and apply community-changes.patch.
2. Use Python 3.12 to run scripts/community/build_backend.py. Set --repo to the repository root, --output to the output server path, and --original to the unmodified official 0.5.0 voicebox-server. The default input is /Applications/Voicebox.app/Contents/MacOS/voicebox-server. Optional --runtime extracts a runtime for validation.
3. Install frontend dependencies with Bun 1.3.8 using the frozen lockfile; build the tauri frontend. Build the native program with Rust, cargo --locked, and the custom-protocol feature. Set MACOSX_DEPLOYMENT_TARGET=15.0. Place the rebuilt server and original MCP shim in tauri/src-tauri/binaries with the aarch64-apple-darwin suffix.
4. With full Xcode, use the upstream icon workflow. Without full Xcode, VOICEBOX_PREBUILT_ICON_DIR can point to the original application's Contents/Resources to reuse its three compiled icon resources. This build used the locally available MacOSX26.5.sdk via SDKROOT without changing the system default SDK.
5. Package the app as Voicebox Corebrandings.app with the configured version and macOS 15 minimum. Sign the final bundle and verify it before creating the DMG. Record binary hashes after signing. This preview uses an ad-hoc signature and has not been Apple notarized.

The backend builder preserves the outer Mach-O size and rebuilds the complete Python backend, entry point and NumPy compatibility hook. It compares non-backend Python modules and native dependency content against the original input. Recompression changes encoding only. The Qwen sampler is the sole third-party code backport: repetition penalties use the most recent 64 tokens in both sampling paths.

The tests exercise the packaged sampler and actual frozen Torch compatibility hook. Selected upstream tests cover backend behavior. Users do not need Python, Rust or Bun to install the packaged application. Community updates are downloaded manually from the Releases page.

See FIXES.md and the public validation summary for the included fixes and limits. Upstream authors retain credit and their licenses.
