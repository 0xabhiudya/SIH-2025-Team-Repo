
# 🚨 SIREN: URL-Based Cyber Attack Detection System

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?logo=Streamlit&logoColor=white)](https://streamlit.io/)

**SIREN** (**S**ecurity **I**ntelligence and **R**eal-time **E**xploit **N**etwork analyzer) is an advanced cybersecurity tool designed to detect URL-based attacks from network traffic captured in PCAP files. This system identifies 11 different types of cyber attacks targeting HTTP protocols.

## 🎯 Problem Statement

Cyber security vulnerabilities in HTTP protocols are being exploited by threat actors through URL-based attacks. SIREN addresses the critical need for automated detection and analysis of these attacks using IP data records (IPDR) from network traffic.

## ✨ Features

### Attack Detection Capabilities
- **SQL Injection** - Detects database manipulation attempts
- **Cross-Site Scripting (XSS)** - Identifies script injection attacks
- **Directory Traversal** - Catches path manipulation attempts  
- **Command Injection** - Detects OS command execution attempts
- **File Inclusion (LFI/RFI)** - Identifies file inclusion vulnerabilities
- **Server-Side Request Forgery (SSRF)** - Detects internal network probing
- **Typosquatting/URL Spoofing** - Identifies domain spoofing attempts
- **Credential Stuffing/Brute Force** - Detects authentication attacks
- **HTTP Parameter Pollution** - Catches parameter manipulation
- **XML External Entity (XXE)** - Identifies XML injection attacks
- **Web Shell Upload** - Detects backdoor upload attempts

### System Capabilities  
- ✅ PCAP/PCAPNG file ingestion and analysis
- ✅ Real-time attack pattern matching using regex signatures
- ✅ Interactive Streamlit web dashboard
- ✅ Attack filtering by type and source IP
- ✅ Visual charts and attack distribution analysis
- ✅ CSV and JSON export functionality
- ✅ Comprehensive attack logging with timestamps and IP attribution

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
   git clone https://github.com/your-username/siren-attack-detector.git
   cd siren-attack-detector

2. **Install dependencies**
pip install -r requirements.txt

3. **Run the application**
streamlit run app.py

4. **Access the dashboard**
Open your browser and navigate to `http://localhost:8501`

### Dependencies
streamlit>=1.28.0
pandas>=2.0.0
scapy>=2.5.0
nest-asyncio>=1.5.0

## 📱 Usage

### Basic Workflow
1. **Upload PCAP File**: Use the web interface to upload `.pcap` or `.pcapng` files
2. **Run Analysis**: Click "Analyze" to process the network traffic
3. **View Results**: Examine detected attacks in the interactive dashboard
4. **Filter Data**: Filter results by attack type or source IP address
5. **Export Results**: Download findings in CSV or JSON format

### Example Usage
from detector import AttackDetector

Initialize the detector
detector = AttackDetector()

Analyze a PCAP file
results = detector.analyze_pcap("network_traffic.pcap")

Display results
for attack in results:
print(f"Attack: {attack['attack_type']} from {attack['src_ip']}")
