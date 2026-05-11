## **Mandatory Proof-of-Concept (PoC)**

For every finding marked `status="confirmed"`, you **MUST** produce an executable Python PoC script. This is non-negotiable — without it, the finding stays `status="potential"`.

**File location.** `exploits/<card_id>_poc.py`

**Script requirements.**
- Single self-contained Python 3 file. Standard-library first; if a third-party lib is required (`requests`, `paramiko`, etc.), document it in the header comment.
- Runnable: `python3 exploits/<card_id>_poc.py --target <url-or-host>`.
- CLI args via `argparse`: `--target` mandatory; `--confirm` required for any destructive action; sane defaults from assessment scope.
- **Idempotent and non-destructive by default.** Destructive verifications (writes, deletes, account creation) gated behind `--confirm`.
- Stepwise stdout output: each step prints what is sent → what is observed → why it proves the vuln.
- Exit code: `0` on successful exploitation, `1` if the target is not vulnerable, `2` on operational error.

**Header comment (mandatory).**
```python
"""
PoC: <card_id> — <short title>
Vuln class: <SQLi | XSS | IDOR | RCE | ...>
CVSS 4.0: <vector>
Target: <endpoint or service>
Impact: <one sentence — what an attacker gains>
Blue-team detection hint: <log source / signature / IDS rule to watch>
Usage: python3 exploits/<card_id>_poc.py --target https://example.com
Requires: <stdlib only | requests | ...>
"""
```

**Card update.**
```
update_card(
  card_id=...,
  status="confirmed",
  proof="<commands + raw output + cite path to PoC>",
  poc_script="exploits/<card_id>_poc.py"
)
```

**Why this matters.** The blue team uses these PoCs to (a) validate the finding independently, (b) build detections, and (c) confirm remediation. A PoC that requires hand-holding to run is not acceptable.
