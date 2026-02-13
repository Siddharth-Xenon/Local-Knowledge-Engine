import requests
import time
import subprocess
import sys
import os


def verify_ui():
    try:
        ports = [8000, 8003]
        active_port = None

        for port in ports:
            try:
                print(f"Checking UI endpoint on port {port}...")
                response = requests.get(f"http://localhost:{port}/ui")
                if response.status_code == 200 and "<html" in response.text:
                    print(f"[PASS] UI is accessible at http://localhost:{port}/ui")
                    active_port = port
                    # Simple check if highlighting logic is present
                    if "formattedAnswer" in response.text:
                        print(f"[PASS] Inline highlighting logic found in response.")
                    else:
                        print(
                            f"[WARN] Inline highlighting logic NOT found in response."
                        )
                    break
            except requests.exceptions.ConnectionError:
                print(f"[INFO] Port {port} not active.")
            except Exception as e:
                print(f"[FAIL] Error checking port {port}: {e}")

        if active_port:
            # Check Mock Data on active port
            try:
                print(f"Checking Mock Data on port {active_port}...")
                response = requests.get(
                    f"http://localhost:{active_port}/static/mock_response.json"
                )
                if response.status_code == 200 and "answer" in response.json():
                    print("[PASS] Mock Data is accessible")
                else:
                    print(
                        f"[FAIL] Mock Data check failed: Status {response.status_code}"
                    )
            except Exception as e:
                print(f"[FAIL] Mock Data check failed with exception: {e}")
        else:
            print("[FAIL] Could not connect to UI on ports 8003 or 8000.")

    finally:
        print("Stopping server...")


if __name__ == "__main__":
    verify_ui()
