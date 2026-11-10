#!/usr/bin/env python3
"""Create private local credentials and configuration once, without overwriting."""

from pathlib import Path
import secrets

ROOT = Path(__file__).resolve().parent.parent


def main():
    env_path = ROOT / ".env"
    config_path = ROOT / "cpa/config.yaml"
    if env_path.exists() or config_path.exists():
        raise SystemExit("Configuration already exists; edit .env and cpa/config.yaml directly.")
    for name in ("cpa", "cpa/auths", "cpa/logs", "cpa/static", "cpa/plugins", "keeper"):
        (ROOT / name).mkdir(mode=0o700, parents=True, exist_ok=True)
    client_key = "sk-pimo-" + secrets.token_hex(24)
    management_key = secrets.token_hex(32)
    keeper_password = secrets.token_urlsafe(24)
    env = (
        "# Private credentials. Do not commit or share this file.\n"
        "OPENAI_BASE_URL=http://127.0.0.1:8317/v1\n"
        f"OPENAI_API_KEY={client_key}\n"
        f"CPA_MANAGEMENT_KEY={management_key}\n"
        f"KEEPER_LOGIN_PASSWORD={keeper_password}\n"
        "TZ=UTC\n"
    )
    config = f'''# Private runtime config; management-panel edits are persisted here.
config-version: 8
server:
  host: ""
  port: 8317
management:
  # Required for Keeper on the private Docker network.
  # Published host ports are restricted to 127.0.0.1 in compose.yaml.
  allow-remote: true
  secret-key: "{management_key}"
  disable-control-panel: false
  panel-github-repository: "https://github.com/router-for-me/Cli-Proxy-API-Management-Center"
access:
  api-keys:
    - "{client_key}"
oauth:
  auth-dir: "~/.cli-proxy-api"
observability:
  usage:
    usage-statistics-enabled: true
routing:
  strategy: round-robin
  retry:
    request-retry: 3
    max-retry-interval: 30
# Add your upstream providers in the management panel's AI Providers page.
'''
    for path, content in ((env_path, env), (config_path, config)):
        with path.open("x", encoding="utf-8") as handle:
            path.chmod(0o600)
            handle.write(content)
    print("Created .env and cpa/config.yaml with unique credentials.")
    print("Next: docker compose up -d")


if __name__ == "__main__":
    main()
