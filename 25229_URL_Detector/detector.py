import pandas as pd
import re
from datetime import datetime, timedelta
from collections import defaultdict

try:
    from scapy.all import IP, TCP, Raw
    from scapy.utils import PcapReader
except ImportError:
    print("Scapy is not installed. Please install it using: pip install scapy")
    exit()

class AttackDetector:
    """
    Stateful Attack Detector for the ENIGMA project.
    Includes advanced heuristics and stateful brute-force detection.
    """
    def __init__(self):
        self.rules = {
            "SQL Injection": re.compile(r"('|\")\s*(OR|UNION|SELECT|SLEEP|BENCHMARK|CONCAT|CAST|DROP|INSERT|DELETE)\s*('|\")", re.IGNORECASE),
            "Cross-Site Scripting (XSS)": re.compile(r"(<|%3C)script\s*(>|%3E)|javascript:|alert\(|onerror=|onload=|on\w+=|document\.cookie", re.IGNORECASE),
            "Directory Traversal": re.compile(r"(\.\./|\.\.\\|\.\.%2f|\.\.%5c)", re.IGNORECASE),
            "Command Injection": re.compile(r"(&&|\|\||;|%26%26|%7C%7C|%3B)\s*(cat|ls|dir|net user|whoami|uname|ipconfig|ifconfig|ps)", re.IGNORECASE),
            "File Inclusion (LFI/RFI)": re.compile(r"(file|include|path)=.*?(\.\./|%2e%2e%2f)|http[s]?://", re.IGNORECASE),
            "Server-Side Request Forgery (SSRF)": re.compile(r"http[s]?://127\.0\.0\.1|http[s]?://localhost|http[s]?://169\.254\.169\.254|redirect=.*http[s]?://", re.IGNORECASE),
            "Credential Stuffing / Brute Force": re.compile(r"(login|username|password).*(admin|root|test|1234|password|guest|user)", re.IGNORECASE),
            "HTTP Parameter Pollution": re.compile(r"(\?|&).+=.+&.*=.*", re.IGNORECASE),
            "XML External Entity Injection (XXE)": re.compile(r"<!DOCTYPE\s+[^>]+\s+\[|\&\w*;|SYSTEM\s+\"file:", re.IGNORECASE),
            "Web Shell Upload": re.compile(r"/(cmd|backdoor|shell|webshell|upload)\.(asp|aspx|jsp|php|exe)", re.IGNORECASE),
        }
        self.df_columns = ["Timestamp", "SourceIP", "DestinationIP", "DestinationPort", "AttackType", "Payload", "AttackStatus"]
        self.login_attempts = defaultdict(list)
        self.known_domains = ["google.com", "facebook.com", "microsoft.com", "amazon.com", "twitter.com"]

    def _extract_http_info(self, payload: bytes) -> str:
        try: return payload.decode('utf-8', errors='ignore')
        except Exception: return ""

    def _calculate_levenshtein_distance(self, s1, s2):
        # This is a simple placeholder. For production, `pip install python-Levenshtein` is recommended.
        if len(s1) < len(s2): return self._calculate_levenshtein_distance(s2, s1)
        if len(s2) == 0: return len(s1)
        previous_row = range(len(s2) + 1)
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        return previous_row[-1]
        
    def _get_host_from_payload(self, payload_str: str) -> str:
        match = re.search(r"Host:\s*([^\r\n]+)", payload_str, re.IGNORECASE)
        return match.group(1).split(':')[0] if match else ""

    def _is_attack_successful(self, attack_type: str, http_response: str) -> bool:
        if not http_response: return False
        try: status_line = http_response.split('\n')[0]
        except IndexError: return False
        if any(code in status_line for code in ["400", "404", "403", "500"]): return False
        if "200 OK" in status_line:
            if attack_type == "SQL Injection":
                sql_error_patterns = re.compile(r"(SQL syntax|mysql_fetch|query failed|unclosed quotation)", re.IGNORECASE)
                return sql_error_patterns.search(http_response) or len(http_response) > 2000
            elif attack_type == "Cross-Site Scripting (XSS)":
                return bool(re.search(r"<script.*?>", http_response, re.IGNORECASE))
            elif attack_type == "Command Injection":
                return bool(re.search(r"(root:x:0:0|Directory of|volume serial number)", http_response, re.IGNORECASE))
            elif attack_type in ["Directory Traversal", "File Inclusion (LFI/RFI)", "SSRF", "Web Shell Upload"]:
                return True
        return False

    def _check_brute_force(self, ip: str, timestamp: datetime, attack_type: str) -> str:
        if attack_type == "Credential Stuffing / Brute Force":
            one_minute_ago = timestamp - timedelta(seconds=60)
            self.login_attempts[ip] = [ts for ts in self.login_attempts[ip] if ts >= one_minute_ago]
            self.login_attempts[ip].append(timestamp)
            if len(self.login_attempts[ip]) >= 5:
                return "Brute Force Detected"
        return "Attempted"

    def analyze_pcap(self, pcap_file_path: str) -> tuple:
        detected_attacks = []
        packet_count = 0
        http_requests = {}
        combined_patterns = [f'(?P<{re.sub(r"[^a-zA-Z0-9]", "", k)}>{v.pattern})' for k, v in self.rules.items()]
        combined_regex = re.compile('|'.join(combined_patterns), re.IGNORECASE)
        group_to_attack_type = {re.sub(r'[^a-zA-Z0-9]', '', k): k for k in self.rules.keys()}
        
        with PcapReader(pcap_file_path) as pcap_reader:
            for packet in pcap_reader:
                packet_count += 1
                if not packet.haslayer(TCP) or not packet.haslayer(IP) or not packet.haslayer(Raw): continue
                src_ip, dst_ip, src_port, dst_port = packet[IP].src, packet[IP].dst, packet[TCP].sport, packet[TCP].dport
                timestamp = datetime.fromtimestamp(float(packet.time))
                
                if dst_port in [80, 8080]:
                    payload_str = self._extract_http_info(packet[Raw].load)
                    match = combined_regex.search(payload_str)
                    host = self._get_host_from_payload(payload_str)
                    typo_match = False
                    if host:
                        for domain in self.known_domains:
                            if self._calculate_levenshtein_distance(host, domain) in [1, 2]:
                                typo_match = True; break
                    
                    if match or typo_match:
                        attack_type = group_to_attack_type.get(match.lastgroup) if match else "Typosquatting / URL Spoofing"
                        attack_status = self._check_brute_force(src_ip, timestamp, attack_type)
                        attack_info = {
                            "Timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'), "SourceIP": src_ip, 
                            "DestinationIP": dst_ip, "DestinationPort": dst_port, "AttackType": attack_type, 
                            "Payload": payload_str.strip().split('\n')[0], "AttackStatus": attack_status
                        }
                        http_requests[(src_ip, src_port, dst_ip, dst_port)] = attack_info
                
                elif src_port in [80, 8080]:
                    request_key = (dst_ip, dst_port, src_ip, src_port)
                    if request_key in http_requests:
                        attack_info = http_requests.pop(request_key)
                        response_payload = self._extract_http_info(packet[Raw].load)
                        if attack_info["AttackStatus"] != "Brute Force Detected" and self._is_attack_successful(attack_info["AttackType"], response_payload):
                            attack_info["AttackStatus"] = "Successful"
                        detected_attacks.append(attack_info)

        detected_attacks.extend(http_requests.values())
        return pd.DataFrame(detected_attacks, columns=self.df_columns), packet_count