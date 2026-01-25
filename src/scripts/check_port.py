import socket
import argparse
import sys

def check_port(host, port, timeout=2):
    """
    Safely checks if a TCP port is open.
    Returns 0 if open, 1 if closed/timeout, 2 if error.
    """
    try:
        print(f"[INFO] Checking {host}:{port}...", end=" ")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(timeout)
            result = s.connect_ex((host, port))
            if result == 0:
                print(f"✅ OPEN")
                return 0
            else:
                print(f"❌ CLOSED (Code: {result})")
                return 1
    except Exception as e:
        print(f"\n[ERROR] Check failed: {e}")
        return 2

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Safely check if a TCP port is open (Native Python).")
    parser.add_argument("--host", default="localhost", help="Target host (default: localhost)")
    parser.add_argument("--port", type=int, required=True, help="Target port")
    parser.add_argument("--timeout", type=float, default=3.0, help="Timeout in seconds")
    
    args = parser.parse_args()
    sys.exit(check_port(args.host, args.port, args.timeout))
