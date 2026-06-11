# PMIS Screens

Plain HTML/CSS/JS prototypes of the PMIS UI. These files run from the
filesystem (`file://`) — there's no build step, no framework, no node
modules. Open any `*.html` in a browser and the page loads.

The pages talk to the VM-hosted services at `http://10.1.131.199`:

| Page | Backing service |
|---|---|
| `SLA Master.html`, `Activity SLAs.html`, `Project Severity.html` | `/contracts/*` (pmis-contract-management) |
| Everything else | `/projects/*`, `/users/*`, etc. |

## Running on a fresh machine

### 1. Clone

```bash
git clone https://github.com/EY-DIGIT/PMIS_Screens.git
cd PMIS_Screens
```

### 2. Start the CORS proxy

Browsers refuse to `fetch()` `http://10.1.131.199/...` from a `file://`
origin because the VM's `CORS_ORIGINS` setting only allows
`http://localhost:3000`. `cors_proxy.py` is a tiny stdlib HTTP proxy that
sits on `localhost:9000` and forwards to the VM with the right CORS
headers attached.

Requires Python 3.10+ (no extra packages).

```bash
python cors_proxy.py
```

You should see:

```
CORS proxy listening on http://localhost:9000
  /contracts/* -> http://10.1.131.199/contracts/*
  /projects/*  -> http://10.1.131.199/projects/*
```

Leave that terminal open. Closing it kills the proxy and every fetch on
the pages will fail with `ERR_CONNECTION_REFUSED`.

### 3. Open the pages

Double-click any `.html` file, or open it with `Ctrl/Cmd+O` in the
browser. Recommended starting points:

| File | What it does |
|---|---|
| `SLA Master.html` | Onboard new SLAs, list / view / edit existing ones, upload image attachments |
| `Activity SLAs.html` | Attach SLAs to an activity, run severity evaluation |
| `Project Severity.html` | Per-project severity master + LD bands + SLA seeding |

The page header has an **API Base** input that defaults to
`http://localhost:9000/contracts` — keep it as-is unless you've changed
the proxy port.

## Quick sanity checks

If a page loads but no data appears, check the proxy and the VM:

```bash
curl http://localhost:9000/contracts/health
# expect: {"status": "ok"}

curl http://10.1.131.199/contracts/health
# expect: {"status": "ok"}
```

- Proxy returns nothing → restart `python cors_proxy.py`.
- VM returns nothing → check VPN / network reachability to 10.1.131.199.
- Both work but the page shows nothing → open DevTools, look at the
  Network tab, and grep for the failed request.

## Production access

In production the same pages are served from the VM's nginx at
`http://10.1.131.199/` and reach the services on the same host, so the
CORS proxy isn't needed there.
