# detector.py
import pandas as pd
import re
from datetime import datetime, timedelta
from collections import defaultdict

# --- External Library Check ---
try:
    from scapy.all import IP, TCP, Raw
    from scapy.utils import PcapReader
except ImportError:
    print("Scapy is not installed. Please install it using: pip install scapy")
    exit()


class AttackDetector:
    """
    Stateful Attack Detector:
      - Collects multiple matches per HTTP request
      - Emits one row per matched attack (Option A)
      - Uses lenient success heuristics (per user request)
      - Tracks brute-force attempts client-side
    """

    def __init__(self):
        # Priority order (most specific -> least specific)
        self.priority_order = [
            "Command Injection",
            "Directory Traversal",
            "File Inclusion (LFI/RFI)",
            "SQL Injection",
            "Server-side Request Forgery (SSRF)",
            "Web Shell Upload",
            "XML External Entity Injection (XXE)",
            "Cross-Site Scripting (XSS)",
            "HTTP Parameter Pollution",
            "Credential Stuffing / Brute Force",
            "Typosquatting / URL Spoofing"
        ]

        # Regex rules for detection
        self.rules = {
            "Command Injection": re.compile(
                r"(\b(cmd|bash|sh|powershell|exec|system)\b|\b(&&|\|\||;)\b).*", re.IGNORECASE
            ),
            "Directory Traversal": re.compile(
                r"(\.\./|\.\.\\|%2e%2e%2f|%2e%2e%5c|etc/passwd|windows\\system32|boot.ini)", re.IGNORECASE
            ),
            "File Inclusion (LFI/RFI)": re.compile(
                r"(file|include|page|template|load|document)=.*?(?:\.\./|%2e%2e%2f|http[s]?://|ftp://|php://|data:)", re.IGNORECASE
            ),
            "SQL Injection": re.compile(
                r"(\bUNION\b|\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|\bDROP\b|--|#|/\*|\bOR\b\s+\d+=\d+|\bSLEEP\(|\bBENCHMARK\()", re.IGNORECASE
            ),
            "Server-side Request Forgery (SSRF)": re.compile(
                r"http[s]?://(127\.0\.0\.1|localhost|169\.254\.169\.254|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})|file://|gopher://|dict://", re.IGNORECASE
            ),
            "Web Shell Upload": re.compile(
                r"\b(?:r57|c99|webshell|shell)\b|\.(php|asp|aspx|jsp|exe)\b.*(upload|shell|backdoor|cmd)", re.IGNORECASE
            ),
            "XML External Entity Injection (XXE)": re.compile(
                r"<!DOCTYPE\s+[^>]+\[|<!ENTITY\s+.+SYSTEM\s+\"|SYSTEM\s+\"file:", re.IGNORECASE | re.DOTALL
            ),
            "Cross-Site Scripting (XSS)": re.compile(
                r"((<|%3C)\s*script\b|script|javascript:|on\w+\s*=|alert\(|confirm\(|prompt\(|document\.cookie|<img\s+src=)", re.IGNORECASE
            ),
            "HTTP Parameter Pollution": re.compile(
                r"([?&])([a-zA-Z0-9_\-]+)=[^&]*&\2=", re.IGNORECASE
            ),
            "Credential Stuffing / Brute Force": re.compile(
                r"(?:user(name)?|login|usr|pass|password|pwd)=([^&\s]{1,60})", re.IGNORECASE
            ),
            "Typosquatting / URL Spoofing": re.compile(
                r"(g00gle|micros0ft|faceb00k|twitt3r|twitterr|amaz0n|lnstagram|app1e|fav0rite|cllck|go0gle)", re.IGNORECASE
            ),
        }

        # State/configuration
        self.df_columns = [
            "Timestamp", "SourceIP", "DestinationIP", "DestinationPort", "AttackType", "Payload", "AttackStatus"
        ]
        self.login_attempts = defaultdict(list)
        self.known_domains = ["google.com", "facebook.com", "microsoft.com",
                              "amazon.com", "twitter.com", "apple.com", "linkedin.com"]

    # -------- helpers ----------
    def _extract_http_info(self, payload: bytes) -> str:
        try:
            return payload.decode('utf-8', errors='ignore')
        except Exception:
            return ""

    def _get_host_from_payload(self, payload_str: str) -> str:
        match = re.search(r"Host:\s*([^\r\n]+)", payload_str, re.IGNORECASE)
        if match:
            return match.group(1).split(':')[0].strip()
        return ""

    def _calculate_leven_distance(self, s1: str, s2: str) -> int:
        if not s1 or not s2:
            return 99
        s1, s2 = s1.lower(), s2.lower()
        if s1 == s2:
            return 0
        if len(s1) == len(s2):
            return sum(1 for a, b in zip(s1, s2) if a != b)
        return abs(len(s1) - len(s2)) + 1

    def _get_response_status_and_body(self, http_response: str) -> tuple:
        if not http_response:
            return "", "", ""
        try:
            parts = http_response.split('\r\n\r\n', 1)
            headers = parts[0]
            body = parts[1] if len(parts) > 1 else ""
            status_line = headers.split('\n')[0].strip()
            status_match = re.search(r'HTTP/\d\.\d\s+(\d{3})', status_line)
            status_code = status_match.group(1) if status_match else ""
            return status_line, status_code, body
        except Exception:
            return "", "", ""

    # -------- lenient success checks ----------
    def _check_sqli_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        err = re.compile(r"(SQL syntax|Query failed|You have an error in your SQL syntax|Unclosed quotation mark after the character string|ORA-009|ODBC SQL Server Driver|PostgreSQL query failed|mysql_fetch_array|ODBC error|Unclosed quotation mark|Warning: mysql_|SQLiteError|SQLSTATE)", re.IGNORECASE)
        if err.search(body):
            return True
        if status_code in ["500", "200"] and len(body) > 500:
            return True
        return False

    def _check_command_injection_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"uid=\d+|gid=\d+|Directory of [A-Za-z]:|Ping statistics for|bytes=|Windows IP Configuration|www-data|nt authority\system|drwxr-xr-x|Volume Serial Number is", body, re.IGNORECASE):
            return True
        if status_code == "200" and len(body) > 700:
            return True
        return False

    def _check_webshell_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"(r57|c99|webshell|backdoor|cmdshell|shell)", body, re.IGNORECASE):
            return True
        if status_code in ["200", "201"] and re.search(r"upload\s+complete|file\s+saved|successfully uploaded", body, re.IGNORECASE):
            return True
        return False

    def _check_file_inclusion_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"(root:x:0:0|php\.ini|r57shell|c99shell|IndoXploit|B374K|java.io.FileNotFoundException|javax.servlet.ServletException: File not found|allow_url_include|Warning: require_once()|Warning: include|No such file or directory|java\.io\.File|Fatal error:)", body, re.IGNORECASE):
            return True
        if status_code == "200" and len(body) > 600:
            return True
        return False

    def _check_xxe_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"ENTITY|DOCTYPE|XML parser error|SAXParseException|ENTITY is not defined|ENTITY is not defined|<!ENTITY|file:/etc/passwd|SYSTEM identifier|SYSTEM", body, re.IGNORECASE):
            return True
        if status_code == "200" and len(body) > 600:
            return True
        return False

    def _check_ssrf_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"169\.254\.169\.254|instance-id|ami-id|ec2metadatatoken|computeMetadata|Connection refused|Could not resolve host|metadata", body, re.IGNORECASE):
            return True
        if status_code in ["200", "302", "301"] and len(body) > 500:
            return True
        return False

    def _check_directory_traversal_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"root:x:0:0:|daemon:x:1:1|/etc/passwd|/etc/shadow|win.ini|display_errors =|[boot loader]|/bin/bash|/etc/shadow|boot loader|NT AUTHORITY|Windows .+ Version", body, re.IGNORECASE):
            return True
        if status_code == "200" and len(body) > 800:
            return True
        return False

    def _check_xss_success(self, http_response: str, injected_snippet: str = "") -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"|onload=|onerror=|(<script>|<|%3C)\s*script\b|<script>alert(1)</script>|javascript:|on\w+\s*=|alert\(|document.cookie|document\.cookie", body, re.IGNORECASE):
            return True
        if injected_snippet and injected_snippet in body:
            return True
        return False

    def _check_brute_force(self, ip: str, timestamp: datetime, attack_type: str) -> str:
        status = "Attempted"
        if attack_type == "Credential Stuffing / Brute Force":
            one_minute_ago = timestamp - timedelta(seconds=60)
            self.login_attempts[ip] = [
                ts for ts in self.login_attempts[ip] if ts >= one_minute_ago]
            self.login_attempts[ip].append(timestamp)
            if len(self.login_attempts[ip]) >= 5:
                status = "Brute Force Detected"
        return status

    def _check_typosquatting_success(self, http_response: str, requested_host: str = "") -> bool:
        status_line, status_code, body = self._get_response_status_and_body(
            http_response)
        if status_code in ["301", "302", "307", "308"]:
            return True
        if status_code == "200" and re.search(r"(google|facebook|microsoft|amazon|twitter|instagram|apple|linkedin)", body, re.IGNORECASE):
            return True
        if requested_host and any(self._calculate_leven_distance(requested_host, d) <= 2 for d in self.known_domains):
            if status_code == "200":
                return True
        return False

    def _check_hpp_success(self, http_response: str) -> bool:
        _, status_code, body = self._get_response_status_and_body(
            http_response)
        if re.search(r"([a-zA-Z0-9_\-]+)=.*[,&].*\1=", body):
            return True
        if status_code == "200" and len(body) > 500:
            return True
        return False

    def _verify_attack_success(self, attack_type: str, http_response: str, extra: dict = None) -> bool:
        extra = extra or {}
        check_map = {
            "SQL Injection": lambda r: self._check_sqli_success(r),
            "Cross-Site Scripting (XSS)": lambda r: self._check_xss_success(r, extra.get("injected_snippet", "")),
            "Directory Traversal": lambda r: self._check_directory_traversal_success(r),
            "Command Injection": lambda r: self._check_command_injection_success(r),
            "File Inclusion (LFI/RFI)": lambda r: self._check_file_inclusion_success(r),
            "Server-side Request Forgery (SSRF)": lambda r: self._check_ssrf_success(r),
            "Web Shell Upload": lambda r: self._check_webshell_success(r),
            "XML External Entity Injection (XXE)": lambda r: self._check_xxe_success(r),
            "HTTP Parameter Pollution": lambda r: self._check_hpp_success(r),
            "Typosquatting / URL Spoofing": lambda r: self._check_typosquatting_success(r, extra.get("requested_host", "")),
            # brute-force determined client-side
            "Credential Stuffing / Brute Force": lambda r: False,
        }
        checker = check_map.get(attack_type)
        return checker(http_response) if checker else False

    # choose best by priority (not strictly needed now but kept for reference)
    def _select_best_attack(self, matched_attacks):
        if not matched_attacks:
            return None
        for pref in self.priority_order:
            if pref in matched_attacks:
                return pref
        return matched_attacks[0]

    # ---------- Main analysis ----------
    def analyze_pcap(self, pcap_file_path: str) -> tuple:
        """
        Analyze pcap/pcapng file and return (DataFrame, packet_count).
        Each matched attack for a single request becomes its own row.
        """
        all_detected_attacks = []
        packet_count = 0
        # map request_key -> [attack_info, ...] (a list since multiple matches per request)
        http_requests = {}

        try:
            with PcapReader(pcap_file_path) as pcap_reader:
                for packet in pcap_reader:
                    packet_count += 1

                    # ensure needed layers exist
                    if not (packet.haslayer(IP) and packet.haslayer(TCP) and packet.haslayer(Raw)):
                        continue

                    src_ip, dst_ip = packet[IP].src, packet[IP].dst
                    src_port, dst_port = packet[TCP].sport, packet[TCP].dport
                    timestamp = datetime.fromtimestamp(float(packet.time))
                    payload_bytes = bytes(packet[Raw].load)
                    payload_str = self._extract_http_info(payload_bytes)

                    # HTTP Request (client -> server)
                    if dst_port in [80, 8080] and payload_str.startswith(("GET ", "POST ", "PUT ", "DELETE ", "HEAD ")):
                        requested_host = self._get_host_from_payload(
                            payload_str)
                        matched_attacks = []
                        injected_snippet = ""

                        # gather matches (do NOT break early)
                        for attack_name, regex in self.rules.items():
                            is_match = False
                            if attack_name == "Typosquatting / URL Spoofing":
                                host = requested_host
                                if host and len(host) > 4:
                                    for domain in self.known_domains:
                                        if self._calculate_leven_distance(host, domain) <= 2 and host != domain:
                                            is_match = True
                                            break
                                    if not is_match and regex.search(host or ""):
                                        is_match = True
                            elif attack_name == "Cross-Site Scripting (XSS)":
                                m = regex.search(payload_str)
                                if m:
                                    is_match = True
                                    injected_snippet = (m.group(0) or "")[:120]
                            else:
                                if regex.search(payload_str):
                                    is_match = True

                            if is_match:
                                matched_attacks.append(attack_name)

                        # Create one attack_info per matched attack (Option A)
                        if matched_attacks:
                            req_key = (src_ip, src_port, dst_ip, dst_port)
                            http_requests.setdefault(req_key, [])
                            for attack in matched_attacks:
                                status = "Attempted"
                                if attack == "Credential Stuffing / Brute Force":
                                    status = self._check_brute_force(
                                        src_ip, timestamp, attack)

                                attack_info = {
                                    "Timestamp": timestamp,  # keep datetime for formatting later
                                    "SourceIP": src_ip,
                                    "DestinationIP": dst_ip,
                                    "DestinationPort": dst_port,
                                    "AttackType": attack,
                                    "Payload": payload_str.strip().split('\n')[0][:1000],
                                    "AttackStatus": status,
                                    "_context": {
                                        "injected_snippet": injected_snippet,
                                        "requested_host": requested_host,
                                        "matched_attacks": matched_attacks
                                    }
                                }
                                http_requests[req_key].append(attack_info)

                    # HTTP Response (server -> client)
                    elif src_port in [80, 8080] and payload_str:
                        req_key = (dst_ip, dst_port, src_ip, src_port)
                        if req_key in http_requests:
                            pending_list = http_requests.pop(req_key)
                            response_payload = payload_str

                            for attack_info in pending_list:
                                # If brute force was detected previously, keep that status
                                if attack_info["AttackStatus"] != "Brute Force Detected":
                                    extra = attack_info.get("_context", {})
                                    if self._verify_attack_success(attack_info["AttackType"], response_payload, extra):
                                        attack_info["AttackStatus"] = "Successful"

                                # format timestamp
                                ts = attack_info["Timestamp"]
                                if isinstance(ts, datetime):
                                    attack_info["Timestamp"] = ts.strftime(
                                        '%Y-%m-%d %H:%M:%S')
                                attack_info.pop("_context", None)
                                all_detected_attacks.append(attack_info)

        except Exception as e:
            print(f"Error processing PCAP file: {e}")
            return pd.DataFrame([], columns=self.df_columns), 0

        # Any requests left pending (no response) get appended as Attempted/Brute Force Detected
        for pending_list in http_requests.values():
            for attack_info in pending_list:
                ts = attack_info["Timestamp"]
                if isinstance(ts, datetime):
                    attack_info["Timestamp"] = ts.strftime('%Y-%m-%d %H:%M:%S')
                attack_info.pop("_context", None)
                all_detected_attacks.append(attack_info)

        return pd.DataFrame(all_detected_attacks, columns=self.df_columns), packet_count
