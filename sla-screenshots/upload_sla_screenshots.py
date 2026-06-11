"""Upload one screenshot per PMU SLA via the contract-management API.

Walks every ``PMU-SLA0NN_*.png`` file in this directory and POSTs it to
``/contracts/api/v3/sla-masters/{id}/attachments`` with an RFP-anchored
caption. Re-runs are idempotent: an SLA that already has an attachment
with the same filename is skipped.

Requirements
------------
    pip install pymupdf   # only if you need to re-render screenshots
    python cors_proxy.py  # in the repo root, in a separate terminal

Usage
-----
    python sla-screenshots/upload_sla_screenshots.py

The proxy URL is hardcoded to ``http://localhost:9000/contracts``. Change
``CONTRACT_BASE`` below if you've remapped the port.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path


CONTRACT_BASE = "http://localhost:9000/contracts/api/v3"

# RFP section anchors for the upload caption — keeps every image
# traceable back to the contract document the table came from.
CAPTIONS = {
    "PMU-SLA001": "RFP §5.28.2.b — SLA 001: Non-submission of deliverable",
    "PMU-SLA002": "RFP §5.28.2.c — SLA 002: Defects not rectified",
    "PMU-SLA003": "RFP §5.28.2.d — SLA 003: Query resolution delay",
    "PMU-SLA004": "RFP §5.28.2.e — SLA 004: Incorrect recommendation",
    "PMU-SLA005": "RFP §5.28.3.c — SLA 005: Resource Replacements per quarter",
    "PMU-SLA006": "RFP §5.28.3.d — SLA 006: KT overlap",
    "PMU-SLA007": "RFP §5.28.3.e — SLA 007: Resource availability",
    "PMU-SLA008": "RFP §5.28.3.f — SLA 008: Onboarding variance from K",
    "PMU-SLA009": "RFP §5.28.3.g — SLA 009: Replacement onboarding delay",
    "PMU-SLA010": "RFP §5.28.4.a — SLA 010: Governance tool deployment",
    "PMU-SLA011": "RFP §5.28.4.b — SLA 011: Governance tool uptime",
}

# ---------------------------------------------------------------------------
# HTTP helpers (stdlib only)
# ---------------------------------------------------------------------------

def _get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=15) as r:
        return json.loads(r.read())


def _post_multipart(url: str, *, file_path: Path, caption: str) -> dict:
    boundary = "----PyB" + uuid.uuid4().hex
    sep = f"--{boundary}".encode()
    end = f"--{boundary}--".encode()
    with open(file_path, "rb") as fh:
        content = fh.read()
    body = b"\r\n".join([
        sep,
        b'Content-Disposition: form-data; name="caption"',
        b"",
        caption.encode(),
        sep,
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"'.encode(),
        b"Content-Type: image/png",
        b"",
        content,
        end,
    ])
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    here = Path(__file__).resolve().parent
    pngs = sorted(here.glob("PMU-SLA*.png"))
    if not pngs:
        print("No PMU-SLA*.png files in", here, file=sys.stderr)
        return 1

    # Fetch all PMU SLAs once.
    list_body = _get_json(f"{CONTRACT_BASE}/sla-masters?contract_type=PMU&pageSize=50")
    sla_by_ref: dict[str, str] = {}
    for el in list_body["data"]["_embedded"]["elements"]:
        sid = el["_links"]["self"]["href"].rsplit("/", 1)[-1]
        d = el.get("data", el)
        ref = d.get("sla_ref")
        if ref:
            sla_by_ref[ref] = sid

    summary = []
    for png in pngs:
        # Filenames look like PMU-SLA001_p105.png — the SLA ref is everything
        # before the first underscore.
        sla_ref = png.stem.split("_", 1)[0]
        sla_id = sla_by_ref.get(sla_ref)
        if not sla_id:
            summary.append((png.name, f"skip: no SLA found for {sla_ref}"))
            continue

        # Idempotency: skip if the SLA already carries an attachment with
        # this filename.
        try:
            existing = _get_json(f"{CONTRACT_BASE}/sla-masters/{sla_id}/attachments")
            already = any(
                (el.get("data", el).get("original_filename") == png.name)
                for el in existing["data"]["_embedded"]["elements"]
            )
            if already:
                summary.append((png.name, f"skip: already attached to {sla_ref}"))
                continue
        except urllib.error.HTTPError as exc:
            summary.append((png.name, f"warn: list-attachments returned {exc.code}"))

        # Upload.
        try:
            body = _post_multipart(
                f"{CONTRACT_BASE}/sla-masters/{sla_id}/attachments",
                file_path=png,
                caption=CAPTIONS.get(sla_ref, f"RFP screenshot for {sla_ref}"),
            )
            inner = body.get("data") or {}
            inner = inner.get("data", inner)
            summary.append((png.name, f"OK -> {sla_ref} attachment_id={inner.get('id')}"))
        except urllib.error.HTTPError as exc:
            summary.append((png.name, f"ERR {exc.code}: {exc.read().decode()[:120]}"))
        except Exception as exc:  # noqa: BLE001
            summary.append((png.name, f"ERR {exc}"))

    print()
    for name, result in summary:
        print(f"  {name:30}  {result}")
    failed = [r for r in summary if r[1].startswith("ERR")]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
