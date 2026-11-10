# Pimo Proxy — CLIProxyAPI + Keeper

Local Docker deployment of [CLIProxyAPI](https://github.com/router-for-me/CLIProxyAPI)
and [CPA Usage Keeper](https://github.com/Willxup/cpa-usage-keeper).

## Addresses and credentials

| Purpose | Address | Credential in `.env` |
| --- | --- | --- |
| OpenAI-compatible API base URL | http://127.0.0.1:8317/v1 | `OPENAI_API_KEY` |
| Provider and client-key management | http://127.0.0.1:8317/management.html | `CPA_MANAGEMENT_KEY` |
| Keeper usage dashboard | http://127.0.0.1:8080 | `KEEPER_LOGIN_PASSWORD` |

Open `.env` in your editor to retrieve the generated credentials. The three secrets
have different purposes. Client keys authenticate your apps to this proxy;
upstream provider keys authenticate the proxy to your existing API services.

## First setup

Requires Docker with Docker Compose and Python 3:

```sh
python3 scripts/setup.py
docker compose up -d
```

Setup runs once and refuses to overwrite existing configuration. Services restart
automatically while Docker is running. All published ports are local to this Mac.

## Connect your existing APIs

1. Open the management page above. Use server URL `http://127.0.0.1:8317`
   and the original `CPA_MANAGEMENT_KEY` from `.env` to sign in.
2. Open **AI Providers** and add the providers you already use:
   - **Gemini**: your Google AI Studio/Gemini API key.
   - **Claude**: your Anthropic API key; set a custom base URL if applicable.
   - **OpenAI Compatibility**: OpenAI, OpenRouter, DeepSeek, or your own
     OpenAI-compatible endpoint. Enter the provider name, upstream base URL,
     API key, and model IDs/aliases you want to expose.
     Common upstream URLs: `https://api.openai.com/v1`,
     `https://openrouter.ai/api/v1`, `https://api.deepseek.com/v1`.
   - **Codex**: an upstream using the Responses/Codex protocol.
3. Save. Use **API Keys** to create/revoke client keys for your apps.
4. For supported subscription accounts, use **OAuth** in the management panel
   and complete the provider's browser login flow.
5. Open Keeper and sign in with `KEEPER_LOGIN_PASSWORD`.

Models and usage depend on the upstream credentials you add. Keeper collects new
requests and persists history; make an actual model request to populate charts.

## Use the proxy

From this directory, load the generated client credentials:

```sh
set -a
source .env
set +a

curl "$OPENAI_BASE_URL/models" \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

Copy a model ID from that response, then:

```sh
curl "$OPENAI_BASE_URL/chat/completions" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"YOUR_MODEL_ID","messages":[{"role":"user","content":"Say hello"}]}'
```

In any OpenAI-compatible application, enter the base URL and `OPENAI_API_KEY`
above. Applications running in another Docker container need a reachable host URL
such as `http://host.docker.internal:8317/v1` (subject to Docker host networking).
These localhost URLs are for this Mac; a public URL requires deployment to a
reachable server/domain with HTTPS.

## Operations and storage

### Dokploy deployment

Use **`compose.dokploy.yaml`** as the Compose path in Dokploy instead of
`compose.yaml`. It initializes the config automatically in a named Docker volume;
no files need to exist in the server's Git checkout.

Set these variables in Dokploy's Environment settings before deployment:

```env
CPA_MANAGEMENT_KEY=replace-with-a-long-random-management-secret
CLIENT_API_KEY=replace-with-a-long-random-client-key
KEEPER_LOGIN_PASSWORD=replace-with-a-private-dashboard-password
CPA_PUBLIC_URL=https://api.your-domain.com
TZ=UTC
```

Configure HTTPS domains in Dokploy for `cli-proxy-api` port `8317` and
`cpa-usage-keeper` port `8080`. Management is at `/management.html` on the API
domain. Keeper is at the root of its domain. The app base URL is the API domain
plus `/v1`. Attach both services to the network required by Dokploy's domain
routing if your Dokploy installation does not do so automatically.

The initializer only creates config on first deployment. Later redeployments
preserve panel edits, provider credentials, and client keys. Changing
`CPA_MANAGEMENT_KEY` or `CLIENT_API_KEY` in Dokploy Environment alone does not
change an already-initialized config. Update the persisted config too when
rotating the management secret; manage client keys through the panel.
Do not remove the named volumes unless you intend to erase their data.

### Local commands

```sh
docker compose ps
docker compose logs --tail=100 -f
docker compose restart
docker compose down
```

Versions are pinned in `compose.yaml`. To upgrade, change the image tags and run
`docker compose pull && docker compose up -d`.

- `.env`: original management secret, Keeper password, initial client key.
- `cpa/config.yaml`: active configuration, provider keys, client keys. The proxy
  hashes the management secret on startup; continue using the original from `.env`.
  Client-key changes in the panel do not update `.env` automatically.
- `cpa/auths/`: OAuth sessions and proxy state.
- `keeper/`: SQLite history and scheduled backups.

These paths are excluded from Git. To make a consistent backup, stop the services
and copy `.env`, `cpa/`, and `keeper/` together, then start services again.
