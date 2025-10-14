# SIREN — URL-Based Attack Detector

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE) [![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/) [![Streamlit](https://img.shields.io/badge/streamlit-ui-orange.svg)](https://streamlit.io/)

**SIREN** is an advanced, standalone security tool that analyzes network traffic to detect URL-based attacks. It processes `.pcap` and `.pcapng` captures and highlights suspicious URL activity using a multi-layered detection engine. The frontend is implemented with **Streamlit**, providing an interactive dashboard for visualization, investigation, and exporting results.

---

## Table of Contents

1. Overview
2. Key Features
3. Architecture & Detection Workflow
4. Supported Attack Types
5. Installation
6. Quick Start
7. Usage & UI Guide
8. Configuration & Tuning
9. Exporting & Reporting
10. Examples (sample pcap & walkthrough)
11. CI: GitHub Actions Example
12. Screenshots / GIF placeholder
13. Contributing
14. License

---

## 1. Overview

SIREN focuses on identifying URL-based threats in captured network traffic. By combining signature, structural, and stateful analysis with application profiling and dynamic risk scoring, SIREN reduces false positives while prioritizing truly dangerous events.

Designed for analysts, incident responders, and security-focused developers, SIREN helps find subtle payloads (time-based blind SQLi, obfuscated XSS) that simple regex-based scanners often miss.

---

## 2. Key Features

* **Multi-layered detection engine** combining signature, syntactic (HTML/SQL parsing), and semantic checks.
* **Stateful analysis** — correlates requests with server responses to classify events as *Attempted* or *Successful* and detect time-based blind SQLi.
* **Application profiling** — checks URL parameter types and lengths against expected rules to flag anomalies.
* **Dynamic risk scoring** (0–100) that factors attack type, success evidence, and contextual severity.
* **Interactive Streamlit dashboard** with filters, charts, and a sortable "Top 5 High-Risk Events" panel.
* **Advanced filtering** by Attack Type, Status (Attempted / Successful), Source IP (supports CIDR and hyphenated ranges), time windows, and more.
* **Export** filtered results to CSV or JSON for external analysis and reporting.

---

## 3. Architecture & Detection Workflow

1. **Input:** Load `.pcap` / `.pcapng` captures via the Streamlit uploader.
2. **Extraction:** Parse HTTP requests and responses from packets using `scapy` and extract URLs, headers, and payloads.
3. **Signature Layer:** Run enhanced regex-based signatures to catch known patterns.
4. **Structural Layer:** Parse HTML (BeautifulSoup) and SQL (sqlparse) to understand grammar and find evasive payloads.
5. **Application Profiling:** Validate parameter types and lengths against expected rules.
6. **Stateful Correlation:** Match requests to server responses and apply heuristics for success detection.
7. **Scoring:** Compute risk score and classify events for display.
8. **UI & Export:** Visualize results in Streamlit and allow export to CSV/JSON.

---

## 4. Supported Attack Types

SIREN detects a broad set of URL-based attacks, including (but not limited to):

* SQL Injection (SQLi), including time-based blind SQLi
* Cross-Site Scripting (XSS)
* Command Injection
* Directory Traversal
* Local & Remote File Inclusion (LFI/RFI)
* Server-Side Request Forgery (SSRF)
* Brute Force & Credential Stuffing
* Suspicious redirections and open-redirect patterns
* Unusual parameter tampering or malformed inputs

---

## 5. Installation

**Clone the repository:**

```bash
git clone <your-repo-url>
cd siren-ubad
```

**Create and activate a virtual environment (recommended):**

```bash
python -m venv .venv
source .venv/bin/activate    # Linux / macOS
# On Windows: .venv/Scripts/activate
```

**Install dependencies:**

```bash
pip install -r requirements.txt
```

**Requirements (example `requirements.txt`):**

```
streamlit
scapy
pandas
nest_asyncio
altair
beautifulsoup4
lxml
sqlparse
matplotlib
```

> Note: Use Python 3.8+ for best compatibility.

---

## 6. Quick Start

**Run the Streamlit app:**

```bash
streamlit run app.py
```

Your default browser should open the SIREN interface. If it doesn't, open the URL printed in the terminal (usually `http://localhost:8501`).

**Load a capture:** Use the file uploader to choose a `.pcap` or `.pcapng` file. Processing time depends on capture size and machine resources.

---

## 7. Usage & UI Guide

**Main Page**

* At-a-glance metrics: total requests, detected events, and average risk.
* Top 5 High-Risk Events: quick access to the most critical detections.

**Sidebar Filters**

* Filter by Attack Type, Status (Attempted / Successful), Source IP (supports CIDR and hyphen-ranges), time range, and minimum risk score.

**Detailed Logs Tab**

* Inspect raw HTTP requests/responses, extracted parameters, parsed HTML/SQL fragments, and notes about why the event was flagged.
* High-risk events are highlighted for easier triage.

**Export**

* Export current filtered view to CSV or JSON via the download buttons in the Detailed Logs tab.

---

## 8. Configuration & Tuning

* **Signatures:** Add or tune regex patterns in the `signatures/` folder (or equivalent). Keep structured ordering: high-confidence signatures first.
* **Application profiles:** Configure expected parameter schemas (name, type, max length) for web apps you routinely monitor — this reduces false positives.
* **Risk scoring:** Adjust weights used to compute risk (e.g., success evidence weight, attack-type base weight) inside the scoring module.

---

## 9. Exporting & Reporting

SIREN's CSV/JSON exports include:

* Timestamp
* Source IP
* URL and parameters
* Attack Type
* Risk Score (0–100)
* Status (Attempted / Successful)
* Extracted evidence (e.g., matched pattern, parsed payload)

These exports can be imported into external SIEMs, spreadsheets, or incident trackers.

---

## 10. Contributing

Contributions are welcome!

* Open an issue for bug reports and feature requests.
* For code contributions: fork the repo, branch from `main`, and send a pull request.
* Include tests for detection modules where possible and keep signatures documented.

---

## 11. License

SIREN is released under the **MIT License**. See `LICENSE` for details.

---

*Built for security-minded teams — use responsibly, and verify detections manually before taking automated action.*

Contributions are welcome!

* Open an issue for bug reports and feature requests.
* For code contributions: fork the repo, branch from `main`, and send a pull request.
* Include tests for detection modules where possible and keep signatures documented.

---

## 14. License

SIREN is released under the **MIT License**. See `LICENSE` for details.

---

*Built for security-minded teams — use responsibly, and verify detections manually before taking automated action.*
