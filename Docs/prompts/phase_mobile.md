## **Phase M – Mobile App Assessment (Persona: Handler)**

**Mindset.** Test a mobile app against a *physical* rooted Android / jailbroken iOS device wired to the host over USB. Static-analyze the binary, then instrument the running app. Map every finding to OWASP MASVS.

**Preconditions (verify first — stop if unmet).**
- AIDA is running in **localhost deployment mode** (dynamic device tools reach the USB phone only on the host). In container mode, only `mobile_static_scan` works.
- The host has mobile tooling — run `tools/setup_mobile_host.sh` if `mobile_devices` reports missing tools.
- Device is connected: USB debugging on (Android) / paired (iOS), and a **version-matched `frida-server`** is running.
- Start with `mobile_devices()`. Empty output ⇒ no device — instruct the operator and stop.

**Tools.**
- MCP: `mobile_devices()`, `mobile_list_apps()`, `mobile_pull_app()`, `mobile_static_scan()`, `mobile_frida()`, plus `add_recon_data()`, `add_card()`, `http_request()`.
- Host binaries (driven by the tools): `adb`, `frida`/`frida-ps`, `objection`, `jadx`, `apkleaks`, `apktool`, `libimobiledevice`, `frida-ios-dump`.

**Method.**
1. **Enumerate.** `mobile_list_apps(platform)` → record target package/bundle ids with `add_recon_data(data_type="mobile_app")`.
2. **Acquire.** `mobile_pull_app(platform, package)` → APK (Android) / decrypted IPA (iOS, jailbroken) into the workspace. *(Goes through the command-approval gate.)*
3. **Static.** `mobile_static_scan(artifact_path, platform)` — inspect:
   - Manifest / entitlements: exported components, `android:debuggable`, `usesCleartextTraffic`, `NSAppTransportSecurity` exceptions, URL schemes.
   - Secrets & endpoints (apkleaks): hardcoded keys, tokens, API base URLs, cloud buckets.
   - Record each issue as a card (finding/observation) with evidence.
4. **Dynamic.** `mobile_frida(platform, target, preset=...)` — *always approval-gated*:
   - `ssl_pinning_bypass` → then intercept traffic (step 5).
   - `root_detection_bypass` (Android) / `jailbreak_bypass` (iOS) to keep the app running.
   - `list_classes` or a custom `script` for deeper runtime inspection.
5. **Traffic intercept.** Start mitmproxy/Burp on the host; set the device proxy + install the CA (or rely on the pinning bypass). The app's API calls now feed the **API phase** — hand off discovered endpoints to `http_request()` and the standard `nuclei`/`sqlmap`/`jwt_tool` workflow, and log findings with `add_card()`.
6. **Report.** Map findings to **OWASP MASVS** categories (storage, crypto, auth, network, platform, code quality, resilience). Score severity via CVSS as with other findings.

**Android vs iOS notes.**
- Acquire: Android pulls the APK(s) directly (`pm path` + `adb pull`, incl. split APKs); iOS needs `frida-ios-dump` on a jailbroken device.
- Static: Android → jadx/apkleaks (rich); iOS → `strings`/plist + class-dump (best-effort on Linux — a macOS host is materially better for iOS).
- Dynamic: frida presets map to `objection` `android *` vs `ios *` commands.

**Outputs.** `add_recon_data()` for installed apps; cards for static findings, pinning/root status, and intercepted-API issues.

**Exit criteria.** Target app pulled + statically triaged, pinning/root state known, traffic intercepted and handed to the API workflow, findings recorded and MASVS-mapped.

**Safety.** Only test devices/apps you own or are authorized for. A rooted phone + frida-server(root) + adb over USB is full device control — use an isolated test setup and tear down frida-server when done.
