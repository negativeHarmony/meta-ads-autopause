# meta-ads-autopause

Automatically pause Meta (Facebook/Instagram) ads that spend money without getting link clicks.
Run it from the command line, or as an **MCP server** so AI agents (Claude, Hermes or any MCP client)
can check your ads and explain their decisions.

> **Safety first:** dry-run is **on** by default, so the tool only *logs* what it would pause.
> It only ever **pauses** ads. It never resumes ads or changes budgets, bids or targeting.

## How it works

Each check:

1. Fetches the active ads in scope, with their spend and link clicks over the last `window_hours`
   (built from Meta's hourly breakdowns in the ad account's time zone).
2. Marks an ad for pausing when **all** of these are true:
   - it is at least `min_ad_age_hours` old
   - it got **fewer** than `min_link_clicks` link clicks in the window
   - it spent **more** than `spend_threshold` in the window
3. Passes those decisions through a gatekeeper that enforces dry-run, the campaign allowlist
   and a maximum number of pauses per run.
4. Logs every decision, including ads it kept, to `decisions.jsonl`.

## Requirements

- Python 3.10+
- A Meta ad account, a Meta developer app and a system user access token (see below)

## 1. Meta setup

1. **Business portfolio:** create one at [business.facebook.com](https://business.facebook.com).
2. **Ad account:** in Business settings → Accounts → Ad accounts, create one and note its ID
   (`act_...`). Choose the time zone and currency carefully, because they can't be changed later.
3. **Developer app:** at [developers.facebook.com](https://developers.facebook.com) → My Apps →
   Create app, choose the use case *Create & manage ads with Marketing API* and connect it to your
   business portfolio. Leave it in **Development** mode. Under Permissions and features,
   `ads_management`, `ads_read` and `business_management` should show *Ready for testing*
   (no app review is needed for your own ad account).
4. **System user:** Business settings → Users → System users → Add (role: Admin). Then:
   - assign the **ad account** with *Manage ad account* (full control)
   - assign the **app**: Accounts → Apps → your app → Assign people → the system user → *Manage app*
5. **Token:** select the system user → Generate token → your app, expiry **Never**, and tick
   `ads_management`, `ads_read` and `business_management`. Copy it straight away, because Meta
   only shows it once.

**Troubleshooting:** `API access blocked` (code 200) usually means Meta wants you to confirm your
developer account. Open developers.facebook.com while switched to your *personal* profile
(not a Page) and follow the confirmation steps.

## 2. Install

```bash
git clone https://github.com/<your-username>/meta-ads-autopause.git
cd meta-ads-autopause
python3 -m venv .venv
source .venv/bin/activate
pip install .
```

This installs two commands into `.venv/bin/`: `meta-ads-autopause` (CLI) and
`meta-ads-autopause-mcp` (MCP server).

## 3. Configure

```bash
cp .env.example .env              # then fill in your token and ad account ID
cp rules.example.yaml rules.yaml  # optional, to change the defaults
```

| Variable | Required | Meaning |
|---|---|---|
| `META_ACCESS_TOKEN` | yes | System user token |
| `META_AD_ACCOUNT_ID` | yes | Ad account ID (`act_` prefix optional) |
| `ALLOWED_CAMPAIGN_IDS` | yes | Comma-separated campaign IDs, or `ALL` |
| `DRY_RUN` | no | Only exactly `false` turns dry-run off. Default: on |
| `RULES_FILE` | no | Path to a rules YAML. Default: built-in rules |
| `LOG_DIR` | no | Where `decisions.jsonl` goes. Default: `~/.meta-ads-autopause/logs` |

Settings already present in the environment override `.env`.

## 4. Command line

```bash
meta-ads-autopause --dry-run   # --dry-run forces dry-run even if .env says false
```

Run it on a schedule (cron, launchd or systemd) to check every hour.

## 5. Use as an MCP server

| Tool | What it does | Can change ads? |
|---|---|---|
| `run_check` | Full check: judge every ad, pause failures (or log only in dry-run) | Only when `DRY_RUN=false` |
| `preview_decisions` | What the rule would do to each ad right now, with reasons | No |
| `get_ad_performance` | Spend and link clicks per active ad | No |
| `get_decision_log` | Most recent decisions and their reasons | No |
| `get_settings` | Dry-run state, scope and rule (never the token) | No |

No tool can turn dry-run off or pause an arbitrary ad. Those stay under your control.

The server uses the **stdio** transport: your agent starts it as a subprocess. Use **absolute paths**.

### Claude Code

```bash
claude mcp add meta-ads-autopause \
  --env META_ACCESS_TOKEN=your-token \
  --env META_AD_ACCOUNT_ID=act_1234567890 \
  --env ALLOWED_CAMPAIGN_IDS=ALL \
  --env DRY_RUN=true \
  -- /absolute/path/to/meta-ads-autopause/.venv/bin/meta-ads-autopause-mcp
```

### Claude Desktop

Add to `claude_desktop_config.json` (Settings → Developer → Edit Config), then restart Claude:

```json
{
  "mcpServers": {
    "meta-ads-autopause": {
      "command": "/absolute/path/to/meta-ads-autopause/.venv/bin/meta-ads-autopause-mcp",
      "env": {
        "META_ACCESS_TOKEN": "your-token",
        "META_AD_ACCOUNT_ID": "act_1234567890",
        "ALLOWED_CAMPAIGN_IDS": "ALL",
        "DRY_RUN": "true"
      }
    }
  }
}
```

### Other agents (e.g. Hermes)

Any MCP client that supports stdio servers works: set the command to the absolute path of
`meta-ads-autopause-mcp` and pass the variables above as environment variables.
For hourly checks, schedule a prompt such as: *"Call run_check and tell me if anything was paused."*

## Development

```bash
pip install -e ".[dev]"
python -m pytest -v
```

## License

MIT
