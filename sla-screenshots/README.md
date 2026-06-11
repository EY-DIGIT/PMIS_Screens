# PMU SLA Screenshots

One PNG per RFP SLA table, extracted from
`PMIS-devops/notes/UIDIA_PMU for MSP 2.pdf` (the source of truth). Each
file is the full PDF page that carries the named SLA's table.

| File | RFP section | SLA | PDF page |
|---|---|---|---|
| `PMU-SLA001_p105.png` | §5.28.2.b | Non-submission of deliverable | 105 |
| `PMU-SLA002_p105.png` | §5.28.2.c | Defects not rectified | 105 |
| `PMU-SLA003_p105.png` | §5.28.2.d | Query resolution delay | 105 |
| `PMU-SLA004_p106.png` | §5.28.2.e | Incorrect recommendation | 106 |
| `PMU-SLA005_p107.png` | §5.28.3.c | Resource Replacements per quarter | 107 |
| `PMU-SLA006_p108.png` | §5.28.3.d | KT overlap | 108 |
| `PMU-SLA007_p109.png` | §5.28.3.e | Resource availability | 109 |
| `PMU-SLA008_p110.png` | §5.28.3.f | Onboarding additional resources (variance from K) | 110 |
| `PMU-SLA009_p111.png` | §5.28.3.g | Replacement onboarding delay | 111 |
| `PMU-SLA010_p111.png` | §5.28.4.a | Governance tool deployment (T₀+6 months) | 111 |
| `PMU-SLA011_p112.png` | §5.28.4.b | Governance tool uptime / failures | 112 |

## Uploading to the SLA attachments API

The script `upload_sla_screenshots.py` (sibling file) walks this folder
and POSTs each PNG to the corresponding SLA. Run from the repo root:

```bash
python sla-screenshots/upload_sla_screenshots.py
```

The script reads from `localhost:9000/contracts/...` (the CORS proxy)
so it requires `cors_proxy.py` to be running.

The first attempt is a no-op when the SLA already has an attachment
with the same filename — the script checks the live list before
uploading so re-runs are idempotent.

Re-render the screenshots (if the PDF changes) with the snippet at the
bottom of `upload_sla_screenshots.py` — it uses PyMuPDF (`pip install
pymupdf`) and writes here.
