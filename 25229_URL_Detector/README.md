# 🛡️ ENIGMA: UBAD (URL-Based Attack Detector)

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)  [![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=Streamlit&logoColor=white)](https://streamlit.io/)  

**ENIGMA-UBAD** (**U**RL **B**ased **A**ttack **D**etector) is an advanced cybersecurity tool that analyzes PCAP traffic to detect and classify **URL-based cyberattacks**. It supports **stateful detection** (including brute force tracking) and provides an **interactive dashboard** for security analysts.

---

## 🎯 Problem Statement

HTTP is one of the most exploited protocols by cyber threat actors. ENIGMA-UBAD addresses this by scanning packet captures (`.pcap`/`.pcapng`) to identify URL-based attacks using regex signatures, stateful heuristics, and anomaly detection.

---

## ✨ Features

### Attack Detection
- **SQL Injection** – Database manipulation attempts  
- **Cross-Site Scripting (XSS)** – Script injection detection  
- **Directory Traversal** – Path manipulation  
- **Command Injection** – Malicious OS commands  
- **File Inclusion (LFI/RFI)** – Local/remote file inclusion  
- **Server-Side Request Forgery (SSRF)** – Unauthorized internal access  
- **Typosquatting / URL Spoofing** – Domain typo detection via Levenshtein distance  
- **Credential Stuffing / Brute Force** – Stateful login attempt correlation  
- **HTTP Parameter Pollution** – Multiple param injection  
- **XML External Entity (XXE)** – Malicious XML payloads  
- **Web Shell Upload** – Suspicious webshell upload attempts  

### Dashboard Capabilities
- ✅ Upload `.pcap` / `.pcapng` files via web interface  
- ✅ Real-time analysis with regex & heuristics  
- ✅ Interactive **Streamlit** dashboard  
- ✅ Filter by **attack type, source IP, and status**  
- ✅ Visualizations (Altair bar charts for attack distribution)  
- ✅ Export results in **CSV** / **JSON**  
- ✅ Stateful brute-force tracking within 60s windows  

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+  
- pip (Python package manager)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/enigma-ubad.git
cd enigma-ubad

# Install dependencies
pip install -r requirements.txt
```

### Run the App
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📦 Dependencies

- streamlit >= 1.28.0  
- pandas >= 2.0.0  
- scapy >= 2.5.0  
- nest-asyncio >= 1.5.0  
- altair >= 5.0.0  

---

## 📱 Usage

### 1. Web Dashboard
1. Launch the app (`streamlit run app.py`)  
2. Upload a `.pcap` or `.pcapng` file  
3. View results in the dashboard  
4. Filter by **attack type**, **source IP**, or **status**  
5. Export findings to **CSV/JSON**  

### 2. Programmatic Usage
```python
from detector import AttackDetector

detector = AttackDetector()
results_df, packet_count = detector.analyze_pcap("network_traffic.pcap")

print(results_df.head())
print(f"Total Packets Scanned: {packet_count}")
```

---

## 📊 Example Output

| Timestamp           | SourceIP    | DestinationIP | Port | AttackType                     | Status              |
|---------------------|-------------|---------------|------|--------------------------------|---------------------|
| 2025-10-01 12:01:10 | 192.168.1.5 | 10.0.0.2      | 80   | SQL Injection                  | Attempted           |
| 2025-10-01 12:02:45 | 192.168.1.7 | 10.0.0.3      | 8080 | Credential Stuffing / Brute Force | Brute Force Detected |

---

## 📜 License
MIT License – feel free to modify and use for research or production.
