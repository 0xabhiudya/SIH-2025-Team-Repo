import pandas as pd
import re
from datetime import datetime, timedelta
import urllib.parse
from collections import defaultdict
import math

try:
    # Use PcapReader for memory-efficient streaming of PCAP files
    from scapy.all import IP, TCP, Raw
    from scapy.utils import PcapReader
    # NOTE: You may need to install 'python-Levenshtein' for optimal Typosquatting detection.
    # The current _calculate_leven_distance is a placeholder and should be replaced 
    # with 'from Levenshtein import distance as levenshtein_distance' if possible.
except ImportError:
    print("Scapy is not installed. Please install it using: pip install scapy")
    exit()

class AttackDetector:
    """
    Stateful Attack Detector for URL-based HTTP attacks.
    """
    def __init__(self):
        # Regex rules for all 11 attack types specified in the problem statement.
        self.rules = {
            "SQL Injection": re.compile(
                r"('|\")\s*(OR|UNION|SELECT|SLEEP|BENCHMARK|CONCAT|CAST|DROP|INSERT|DELETE)\s*('|\")", re.IGNORECASE
            ),
            "Cross-Site Scripting (XSS)": re.compile(
                r"(<|%3C)script\s*(>|%3E)|javascript:|alert\(|onerror=|onload=|on\w+=|document\.cookie", re.IGNORECASE
            ),
            "Directory Traversal": re.compile(
                r"(\.\./|\.\.\\|\.\.%2f|\.\.%5c)", re.IGNORECASE
            ),
            "Command Injection": re.compile(
                r"(&&|\|\||;|%26%26|%7C%7C|%3B)\s*(cat|ls|dir|net user|whoami|uname|ipconfig|ifconfig|ps)", re.IGNORECASE
            ),
            "File Inclusion (LFI/RFI)": re.compile(
                r"(file|include|path)=.*?(\.\./|%2e%2e%2f)|http[s]?://", re.IGNORECASE
            ),
            "Typosquatting / URL Spoofing": re.compile(
                r"(goog1e|faceb00k|micros0ft|amaz0n|g00gle|twitterr|lnstagram|fav0rite|cllck)", re.IGNORECASE
            ),
            "Server-Side Request Forgery (SSRF)": re.compile(
                r"http[s]?://127\.0\.0\.1|http[s]?://localhost|http[s]?://169\.254\.169\.254|redirect=.*http[s]?://", re.IGNORECASE
            ),
            "Credential Stuffing / Brute Force": re.compile(
                r"(login|username|password).*(admin|root|test|1234|password|guest|user)", re.IGNORECASE
            ),
            "HTTP Parameter Pollution": re.compile(
                r"(\?|&).+=.+&.*=.*", re.IGNORECASE
            ),
            "XML External Entity Injection (XXE)": re.compile(
                r"<!DOCTYPE\s+[^>]+\s+\[|\&\w*;|SYSTEM\s+\"file:", re.IGNORECASE
            ),
            "Web Shell Upload": re.compile(
                r"/(cmd|backdoor|shell|webshell|upload)\.(asp|aspx|jsp|php|exe)", re.IGNORECASE
            ),
        }
        # Updated columns
        self.df_columns = [
            "Timestamp", "SourceIP", "DestinationIP", "DestinationPort", "AttackType", "Payload", "AttackStatus"
        ]
        # State tracking for Brute Force detection: {IP: [timestamp1, timestamp2, ...]}
        self.login_attempts = defaultdict(list)
        # List of well-known domains for typosquatting check
        self.known_domains = ["google.com", "facebook.com", "microsoft.com", "amazon.com", "twitter.com"]

    def _extract_http_info(self, payload: bytes) -> str:
        """Decodes the raw payload to a UTF-8 string, ignoring errors."""
        try:
            return payload.decode('utf-8', errors='ignore')
        except Exception:
            return ""

    # --- Typosquatting Helper ---
    def _calculate_leven_distance(self, s1, s2):
        """Mocks Levenshtein distance for systems without the dependency."""
        # Replace with actual Levenshtein implementation if the dependency is installed
        # return levenshtein_distance(s1, s2)
        # Placeholder logic: return 0 for identical strings, 1 otherwise
        if len(s1) == 0 or len(s2) == 0:
            return 99
        return abs(len(s1) - len(s2)) + (0 if s1 == s2 else 1)
        
    def _get_host_from_payload(self, payload_str: str) -> str:
        """Extracts the Host header from an HTTP request payload."""
        match = re.search(r"Host:\s*([^\r\n]+)", payload_str, re.IGNORECASE)
        if match:
            return match.group(1).split(':')[0]
        return ""

    # --- Enriched Success Heuristics ---
    def _is_attack_successful(self, attack_type: str, http_response: str) -> bool:
        """
        Analyzes the server's HTTP response to determine if an attack was successful,
        using content-based heuristics for critical attacks.
        """
        if not http_response: return False
        
        try:
            status_line = http_response.split('\n')[0]
        except IndexError:
            return False
        
        # 4xx or 5xx usually means failure (Attack Attempted)
        if any(code in status_line for code in ["400", "404", "403", "500"]):
            return False
            
        # Success is strongly indicated by a 200 OK
        if "200 OK" in status_line:
            # Type-specific success checks
            if attack_type == "SQL Injection":
                # Check for database error messages
                sql_error_patterns = re.compile(r"(SQL syntax error|mysql_fetch_array|query failed|unclosed quotation mark)", re.IGNORECASE)
                if sql_error_patterns.search(http_response):
                    return True
                # Check for large data response (suggests successful UNION/data leak)
                if len(http_response) > 2000: 
                    return True

            elif attack_type == "Cross-Site Scripting (XSS)":
                # Check for reflection of unencoded common XSS script tags
                if re.search(r"(<|%3C)script\s*(>|%3E)", http_response, re.IGNORECASE):
                    return True

            elif attack_type == "Command Injection":
                # Check for typical system command output reflection
                if re.search(r"(root:x:0:0|Directory of|volume serial number)", http_response, re.IGNORECASE):
                    return True
            
            # Default to success for other attacks where 200 is a good indicator
            elif attack_type in ["Directory Traversal", "File Inclusion (LFI/RFI)", "SSRF", "Web Shell Upload"]:
                return True
            
        return False # Default to not successful if no clear indicator is found.

    # --- Stateful Brute Force Checker ---
    def _check_brute_force(self, ip: str, timestamp: datetime, attack_type: str) -> str:
        """
        Tracks Credential Stuffing attempts and upgrades status if rate-limited.
        Criteria: 5 attempts within 60 seconds from the same IP.
        """
        status = "Attempted"
        
        if attack_type == "Credential Stuffing / Brute Force":
            # 1. Clean up old attempts (older than 60 seconds)
            one_minute_ago = timestamp - timedelta(seconds=60)
            self.login_attempts[ip] = [ts for ts in self.login_attempts[ip] if ts >= one_minute_ago]
            
            # 2. Add the current attempt
            self.login_attempts[ip].append(timestamp)
            
            # 3. Check for threshold breach
            if len(self.login_attempts[ip]) >= 5:
                status = "Brute Force Detected"
                # Optional: clear attempts after detection to prevent immediate re-trigger
                # self.login_attempts[ip] = [] 
                
        return status

    def analyze_pcap(self, pcap_file_path: str) -> tuple:
        """
        Analyzes a PCAP file by streaming packets, correlating requests and responses,
        and classifying attacks based on the server's response.
        """
        detected_attacks = []
        packet_count = 0
        http_requests = {} # Stores pending requests waiting for a response.

        # --- Performance Optimization: Combine all regex rules into one ---
        combined_patterns = []
        for attack_type, pattern in self.rules.items():
            # Use a clean group name for the combined regex match
            group_name = re.sub(r'[^a-zA-Z0-9]', '', attack_type)
            combined_patterns.append(f'(?P<{group_name}>{pattern.pattern})')
        
        combined_regex = re.compile('|'.join(combined_patterns), re.IGNORECASE)
        group_to_attack_type = {re.sub(r'[^a-zA-Z0-9]', '', k): k for k in self.rules.keys()}
        
        # --- Performance Optimization: Stream the file with PcapReader ---
        with PcapReader(pcap_file_path) as pcap_reader:
            for packet in pcap_reader:
                packet_count += 1
                if not packet.haslayer(TCP) or not packet.haslayer(IP) or not packet.haslayer(Raw):
                    continue

                src_ip, dst_ip = packet[IP].src, packet[IP].dst
                src_port, dst_port = packet[TCP].sport, packet[TCP].dport
                timestamp = datetime.fromtimestamp(float(packet.time))
                
                # --- Logic for HTTP Request (Client -> Server) ---
                if dst_port in [80, 8080]:
                    payload_str = self._extract_http_info(packet[Raw].load)
                    
                    # 1. Check for standard attack regex matches
                    match = combined_regex.search(payload_str)
                    
                    # 2. Check for Typosquatting (Host header analysis)
                    host = self._get_host_from_payload(payload_str)
                    typo_match = False
                    if host:
                        # Only check if the regex match wasn't already found to potentially save CPU time
                        if not match:
                            for domain in self.known_domains:
                                if self._calculate_leven_distance(host, domain) <= 2 and host != domain:
                                    typo_match = True
                                    break

                    # If an attack is found (either regex or typosquatting)
                    if match or typo_match:
                        # Determine attack type (Typosquatting if regex failed but typo check passed)
                        attack_type = group_to_attack_type.get(match.lastgroup, "Typosquatting / URL Spoofing") if match else "Typosquatting / URL Spoofing"
                        
                        # Apply Stateful Brute Force check immediately
                        attack_status = self._check_brute_force(src_ip, timestamp, attack_type)
                        
                        attack_info = {
                            "Timestamp": timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                            "SourceIP": src_ip, "DestinationIP": dst_ip, "DestinationPort": dst_port,
                            "AttackType": attack_type, "Payload": payload_str.strip().split('\n')[0],
                            "AttackStatus": attack_status
                        }
                        # Store the request, waiting for a server response.
                        http_requests[(src_ip, src_port, dst_ip, dst_port)] = attack_info

                # --- Logic for HTTP Response (Server -> Client) ---
                elif src_port in [80, 8080]:
                    request_key = (dst_ip, dst_port, src_ip, src_port)
                    if request_key in http_requests:
                        attack_info = http_requests.pop(request_key)
                        response_payload = self._extract_http_info(packet[Raw].load)
                        
                        # Only check for success if not already classified as Brute Force
                        if attack_info["AttackStatus"] != "Brute Force Detected":
                            if self._is_attack_successful(attack_info["AttackType"], response_payload):
                                attack_info["AttackStatus"] = "Successful"
                        
                        detected_attacks.append(attack_info)

        # Add any requests that did not get a response as their tracked status ("Attempted" or "Brute Force Detected").
        detected_attacks.extend(http_requests.values())
        
        return pd.DataFrame(detected_attacks, columns=self.df_columns), packet_count





