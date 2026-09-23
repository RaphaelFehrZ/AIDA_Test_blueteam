# Setting up an Android phone for AIDA mobile testing

This guide connects a **physical rooted Android device** (over USB) to AIDA so the
`mobile_*` tools can enumerate, pull, statically analyze, and instrument apps with
Frida. iOS is covered separately.

> **How it works.** The phone is USB-connected to the **host**. AIDA reaches it in
> **localhost deployment mode**, where commands run on the host (via the host-agent)
> instead of inside the pentest container — so `adb`/`frida` see the USB device.

> **Authorization.** Only test devices and apps you own or are explicitly authorized
> to test. A rooted phone + `frida-server` (root) + adb over USB is full device control.

---

## Prerequisites

- A **rooted** Android phone (Magisk or equivalent) + a USB data cable.
- AIDA checked out and runnable on a Linux host (Debian/Ubuntu assumed).
- Sudo on the host (for installing `adb`, Java, etc.).

---

## Step 1 — Install host tooling

From the AIDA project root:

```bash
./tools/setup_mobile_host.sh
```

This installs `adb`, `frida-tools` (pinned — note the version it prints), `objection`,
`apkleaks`, `jadx`, `apktool`, and iOS helpers. Re-run any time; it's idempotent.

Check what's present without installing:

```bash
./tools/setup_mobile_host.sh --check
```

**Note the Frida version it pins** (e.g. `16.5.9`) — the `frida-server` you put on the
phone in Step 4 **must match** it (major.minor).

---

## Step 2 — Enable USB debugging on the phone

1. **Settings → About phone** → tap **Build number** 7 times to unlock Developer options.
2. **Settings → System → Developer options** → enable **USB debugging**.
3. (Recommended) enable **Rooted debugging** / grant root to the shell if your ROM offers it.

---

## Step 3 — Connect and authorize adb

Plug the phone in, then on the host:

```bash
adb devices
```

The phone shows an **"Allow USB debugging?"** prompt — tick *Always allow* and accept.
Re-run `adb devices`; you should see:

```
List of devices attached
<SERIAL>    device
```

- `unauthorized` → you didn't accept the prompt (re-plug, watch the phone).
- `no permissions` → add yourself to the `plugdev` group / udev rules, or re-plug.

---

## Step 4 — Install and run frida-server (version-matched)

1. Find the phone's CPU ABI:
   ```bash
   adb shell getprop ro.product.cpu.abi        # e.g. arm64-v8a
   ```
2. Download the matching `frida-server` for the **pinned Frida version** from
   <https://github.com/frida/frida/releases> (file like
   `frida-server-16.5.9-android-arm64`), decompress it, then:
   ```bash
   adb push frida-server-16.5.9-android-arm64 /data/local/tmp/frida-server
   adb shell "su -c 'chmod 755 /data/local/tmp/frida-server'"
   adb shell "su -c '/data/local/tmp/frida-server &'"
   ```
3. Verify from the host — this lists installed apps and proves frida is reachable:
   ```bash
   frida-ps -Uai
   ```

> `frida-server` stops on reboot — re-run the `su -c '.../frida-server &'` line after each reboot.

---

## Step 5 — Start AIDA in localhost deployment mode

Dynamic device tools only work in **localhost** mode (USB is on the host):

```bash
./start.sh --localhost
```

Open the web UI at **http://localhost:31337** (or your chosen mode's URL). The mode is
persisted in `.aida/deployment-mode`, so subsequent `./start.sh` runs stay in localhost
mode until you switch back with `./start.sh --container`.

---

## Step 6 — Verify from inside AIDA

In an assessment, have the agent call the MCP tool (or trigger it through your workflow):

- **`mobile_devices`** → should list your device and the `frida-ps` app list.
  Empty output means the phone isn't seen — recheck Steps 3–4.

Optionally pin the device on the assessment (only needed if **more than one** device is
attached) by setting its **`mobile_device`** field to the adb serial from Step 3.

---

## Step 7 — Typical workflow

Follow `Docs/prompts/phase_mobile.md`. In short:

1. **List apps** — `mobile_list_apps(platform="android")` → save target package ids.
2. **Pull the APK** — `mobile_pull_app(platform="android", package="com.target.app")`
   *(approval-gated)*.
3. **Static scan** — `mobile_static_scan(artifact_path="/workspace/base.apk", platform="android")`
   → manifest, exported components, cleartext-traffic flags, hardcoded secrets/endpoints.
4. **Instrument** — `mobile_frida(platform="android", target="com.target.app", preset="ssl_pinning_bypass")`
   *(always requires approval — it injects into the live app)*. Other presets:
   `root_detection_bypass`, `list_classes`, or a custom `script`.
5. **Intercept traffic** — start mitmproxy/Burp on the host, set the phone's proxy +
   install the CA (or rely on the pinning bypass); the app's API calls then feed AIDA's
   normal API tooling (`http_request`, `nuclei`, `sqlmap`, `jwt_tool`).

---

## Troubleshooting

| Symptom | Fix |
|--------|-----|
| `adb devices` shows nothing | Bad cable / no USB debugging / not authorized. Try another cable + port, re-accept the prompt. |
| `frida-ps -Uai` errors with a version message | `frida-server` on the phone ≠ host `frida-tools` version. Re-download the matching server. |
| `frida-ps` says "unable to connect" | `frida-server` isn't running (restart it as root) or wrong ABI binary. |
| `mobile_*` says *"requires localhost deployment mode"* | You're in container mode — restart with `./start.sh --localhost`. |
| `mobile_*` says a tool is *"not installed"* | Re-run `./tools/setup_mobile_host.sh` on the host. |
| `su -c` fails | Root isn't granted to the shell — approve the Magisk prompt or enable shell root. |

---

## Teardown

```bash
adb shell "su -c 'pkill frida-server'"   # stop the on-device agent
./stop.sh                                # stops AIDA + the host-agent
```

Then unplug the device. Revoke USB-debugging authorizations in Developer options if this
was a shared/loaner phone.
