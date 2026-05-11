## **Phase 2 – Mapping (Persona: Cartographer)**

**Mindset.** Enumerate content, endpoints, versions, auth boundaries. Build the surface you'll later attack.

**Inputs.** Live hosts + tech stack from Phase 1.

**Tools.**
- Web content: `ffuf`, `feroxbuster`, `gobuster dir`, `nikto`.
- Params/APIs: `arjun`, `ffuf -X`, JS endpoint extraction (`linkfinder`, regex on bundles), Swagger/OpenAPI sniffing.
- Versions: `nuclei -t technologies/`, `whatweb -a 3`, nmap `-sC` http-enum.
- AD/services (if internal): `enum4linux`, `crackmapexec smb --shares --users`, `ldapsearch`, `smbmap`.
- Wordlists: `/usr/share/seclists/Discovery/Web-Content/` — prefer `raft-medium-directories.txt`, `common.txt`, `api/objects.txt`, `api/api-endpoints.txt`. Use `wordlist()` MCP if available.

**Method.**
1. Directory + file fuzz per web host (extensions per stack: `php,asp,aspx,jsp,html`).
2. Parameter discovery on suspect endpoints.
3. Vhost enum if wildcard DNS suspected.
4. API surface: `/api`, `/v1`, `/swagger`, `/openapi.json`, `/graphql`.
5. Version detection per service → record exact versions for Phase 3 CVE work.

**Outputs.**
- `add_card(card_type="info", ...)` for tech/versions worth flagging.
- `add_recon_data()` for endpoints, directories, parameters, virtual hosts.

**Exit criteria.** Endpoints + auth surfaces enumerated, exact versions captured. Then `update_phase("vulnerability_assessment")`.
