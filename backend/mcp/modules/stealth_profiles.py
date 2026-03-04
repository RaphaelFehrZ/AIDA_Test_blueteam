"""
Stealth Profile Engine — preset profiles + flag builders for evasion-aware scanning.

Profiles: ghost, careful, normal, aggressive
Each profile defines defaults for nmap timing, web fuzzer threads/delays,
fragmentation, decoys, and user-agent. Assessment-level overrides take precedence.
"""
from typing import Any, Dict, Optional

# Realistic browser user-agent for blending in
_CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ── Preset profiles ──────────────────────────────────────────────────────────

STEALTH_PROFILES: Dict[str, Dict[str, Any]] = {
    "ghost": {
        "nmap_timing": "T0",
        "max_rate": 5,
        "web_threads": 1,
        "scan_delay": "5-15s",
        "fragmentation": True,
        "decoy_ips": "RND:10",
        "custom_user_agent": _CHROME_UA,
        "randomize_hosts": True,
        "data_length": 40,  # pad packets to avoid signature matching
    },
    "careful": {
        "nmap_timing": "T2",
        "max_rate": 50,
        "web_threads": 3,
        "scan_delay": "0.5-2s",
        "fragmentation": False,
        "decoy_ips": None,
        "custom_user_agent": _CHROME_UA,
        "randomize_hosts": False,
        "data_length": None,
    },
    "normal": {
        "nmap_timing": "T4",
        "max_rate": None,
        "web_threads": 10,
        "scan_delay": None,
        "fragmentation": False,
        "decoy_ips": None,
        "custom_user_agent": None,
        "randomize_hosts": False,
        "data_length": None,
    },
    "aggressive": {
        "nmap_timing": "T5",
        "max_rate": None,
        "web_threads": 50,
        "scan_delay": None,
        "fragmentation": False,
        "decoy_ips": None,
        "custom_user_agent": None,
        "randomize_hosts": False,
        "data_length": None,
    },
}


# ── Config resolver ──────────────────────────────────────────────────────────

def resolve_stealth_config(assessment_data: Dict[str, Any]) -> Dict[str, Any]:
    """Merge profile defaults with assessment-level overrides.

    Assessment fields override profile defaults when they are not None / empty.
    """
    profile_name = (assessment_data.get("stealth_profile") or "normal").lower()
    profile = STEALTH_PROFILES.get(profile_name, STEALTH_PROFILES["normal"]).copy()

    # Assessment-level overrides (non-None values win)
    override_map = {
        "nmap_timing": "nmap_timing",
        "max_rate": "max_rate",
        "scan_delay": "scan_delay",
        "fragmentation": "fragmentation",
        "decoy_ips": "decoy_ips",
        "custom_user_agent": "custom_user_agent",
        "randomize_hosts": "randomize_hosts",
        "proxy_config": "proxy_config",
        "source_port": "source_port",
        "extra_nmap_evasion": "extra_nmap_evasion",
        "nikto_evasion": "nikto_evasion",
        "nikto_tuning": "nikto_tuning",
    }

    for assess_key, config_key in override_map.items():
        value = assessment_data.get(assess_key)
        if value is not None and value != "":
            profile[config_key] = value

    # Ensure proxy_config, source_port, extra_nmap_evasion exist even if not overridden
    for key in ("proxy_config", "source_port", "extra_nmap_evasion", "nikto_evasion", "nikto_tuning"):
        profile.setdefault(key, None)

    profile["profile_name"] = profile_name
    return profile


# ── Nmap flag builder ────────────────────────────────────────────────────────

def build_nmap_stealth_flags(config: Dict[str, Any]) -> str:
    """Build nmap evasion flags from resolved stealth config.

    Returns a string of flags to inject into nmap commands.
    """
    parts: list[str] = []

    # Timing template
    timing = config.get("nmap_timing")
    if timing:
        # Ensure format is -T<n>
        t = timing.upper().strip()
        if not t.startswith("-"):
            t = f"-{t}"
        parts.append(t)

    # Max rate
    max_rate = config.get("max_rate")
    if max_rate:
        parts.append(f"--max-rate {max_rate}")

    # Scan delay
    delay = config.get("scan_delay")
    if delay:
        # nmap uses --scan-delay with ms/s suffix
        # Handle range like "5-15s" -> use the lower bound for --scan-delay
        # and upper bound for --max-scan-delay
        if "-" in delay and delay[-1] in "sm":
            unit = delay[-1]
            bounds = delay[:-1].split("-")
            if len(bounds) == 2:
                parts.append(f"--scan-delay {bounds[0]}{unit}")
                parts.append(f"--max-scan-delay {bounds[1]}{unit}")
            else:
                parts.append(f"--scan-delay {delay}")
        else:
            parts.append(f"--scan-delay {delay}")

    # Fragmentation
    if config.get("fragmentation"):
        parts.append("-f")

    # Decoys
    decoys = config.get("decoy_ips")
    if decoys:
        parts.append(f"-D {decoys}")

    # Source port
    source_port = config.get("source_port")
    if source_port:
        parts.append(f"--source-port {source_port}")

    # Data length (pad packets)
    data_length = config.get("data_length")
    if data_length:
        parts.append(f"--data-length {data_length}")

    # Randomize hosts
    if config.get("randomize_hosts"):
        parts.append("--randomize-hosts")

    # Proxy
    proxy = config.get("proxy_config")
    if proxy:
        parts.append(f"--proxies {proxy}")

    # Extra nmap evasion flags (user-supplied raw flags)
    extra = config.get("extra_nmap_evasion")
    if extra:
        parts.append(extra.strip())

    return " ".join(parts)


# ── Web fuzzer flag builder ──────────────────────────────────────────────────

def build_web_fuzzer_stealth_flags(config: Dict[str, Any], tool: str) -> str:
    """Build web fuzzer evasion flags for gobuster/ffuf/dirb.

    Returns a string of flags to inject into the command.
    """
    parts: list[str] = []
    ua = config.get("custom_user_agent")
    proxy = config.get("proxy_config")
    delay = config.get("scan_delay")

    if tool == "gobuster":
        if ua:
            parts.append(f'-a "{ua}"')
        if proxy:
            parts.append(f"--proxy {proxy}")
        if delay:
            # gobuster uses --delay with Go duration format
            # Convert "0.5-2s" -> use lower bound "500ms"
            gobuster_delay = _convert_delay_for_web(delay)
            if gobuster_delay:
                parts.append(f"--delay {gobuster_delay}")

    elif tool == "ffuf":
        if ua:
            parts.append(f'-H "User-Agent: {ua}"')
        if proxy:
            parts.append(f"-x {proxy}")
        if delay:
            # ffuf uses -p with seconds (float), supports range like "0.5-2.0"
            ffuf_delay = _convert_delay_for_ffuf(delay)
            if ffuf_delay:
                parts.append(f"-p {ffuf_delay}")

    elif tool == "dirb":
        if ua:
            parts.append(f'-a "{ua}"')
        if proxy:
            parts.append(f"-p {proxy}")
        if delay:
            # dirb uses -z with milliseconds
            dirb_delay = _convert_delay_ms(delay)
            if dirb_delay:
                parts.append(f"-z {dirb_delay}")

    return " ".join(parts)


# ── Nikto flag builder ───────────────────────────────────────────────────────

def build_nikto_stealth_flags(config: Dict[str, Any]) -> str:
    """Build nikto evasion flags from resolved stealth config."""
    parts: list[str] = []

    evasion = config.get("nikto_evasion")
    if evasion:
        parts.append(f"-evasion {evasion}")

    tuning = config.get("nikto_tuning")
    if tuning:
        parts.append(f"-Tuning {tuning}")

    ua = config.get("custom_user_agent")
    if ua:
        parts.append(f'-useragent "{ua}"')

    proxy = config.get("proxy_config")
    if proxy:
        parts.append(f"-useproxy {proxy}")

    return " ".join(parts)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _convert_delay_for_web(delay: str) -> Optional[str]:
    """Convert scan_delay (e.g. '0.5-2s', '500ms', '5s') to gobuster format."""
    if not delay:
        return None
    delay = delay.strip()
    # Range like "0.5-2s" -> use lower bound
    if "-" in delay and delay[-1] in "sm":
        unit = delay[-1]
        lower = delay.split("-")[0]
        if unit == "s":
            return f"{lower}s"
        return f"{lower}ms"
    return delay


def _convert_delay_for_ffuf(delay: str) -> Optional[str]:
    """Convert scan_delay to ffuf -p format (seconds, supports range)."""
    if not delay:
        return None
    delay = delay.strip()
    # Range like "0.5-2s" -> ffuf supports "0.5-2.0"
    if "-" in delay and delay[-1] in "sm":
        unit = delay[-1]
        bounds = delay[:-1].split("-")
        if len(bounds) == 2:
            if unit == "s":
                return f"{bounds[0]}-{bounds[1]}"
            else:
                # ms -> convert to seconds
                return f"{float(bounds[0])/1000}-{float(bounds[1])/1000}"
    # Single value
    if delay.endswith("s"):
        return delay[:-1]
    if delay.endswith("ms"):
        return str(float(delay[:-2]) / 1000)
    return delay


def _convert_delay_ms(delay: str) -> Optional[str]:
    """Convert scan_delay to milliseconds (for dirb -z)."""
    if not delay:
        return None
    delay = delay.strip()
    # Range -> use lower bound
    if "-" in delay and delay[-1] in "sm":
        unit = delay[-1]
        lower = delay.split("-")[0]
        if unit == "s":
            return str(int(float(lower) * 1000))
        return lower
    if delay.endswith("s"):
        return str(int(float(delay[:-1]) * 1000))
    if delay.endswith("ms"):
        return delay[:-2]
    return delay


def get_stealth_threads(config: Dict[str, Any], default_threads: int = 10) -> int:
    """Get the web thread count from stealth config."""
    return config.get("web_threads", default_threads)


def format_stealth_summary(config: Dict[str, Any]) -> str:
    """Format a human-readable summary of active stealth settings."""
    profile = config.get("profile_name", "normal")
    lines = [f"Stealth Profile: **{profile.upper()}**"]

    if config.get("nmap_timing"):
        lines.append(f"  Nmap Timing: {config['nmap_timing']}")
    if config.get("max_rate"):
        lines.append(f"  Max Rate: {config['max_rate']}/s")
    if config.get("scan_delay"):
        lines.append(f"  Scan Delay: {config['scan_delay']}")
    if config.get("web_threads"):
        lines.append(f"  Web Threads: {config['web_threads']}")
    if config.get("fragmentation"):
        lines.append("  Fragmentation: enabled")
    if config.get("decoy_ips"):
        lines.append(f"  Decoys: {config['decoy_ips']}")
    if config.get("custom_user_agent"):
        lines.append(f"  User-Agent: {config['custom_user_agent'][:50]}...")
    if config.get("proxy_config"):
        lines.append(f"  Proxy: {config['proxy_config']}")
    if config.get("source_port"):
        lines.append(f"  Source Port: {config['source_port']}")
    if config.get("randomize_hosts"):
        lines.append("  Randomize Hosts: enabled")

    return "\n".join(lines)
