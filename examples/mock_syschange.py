#!/usr/bin/env python3
"""Standalone mock for syschange-run to enable zero-setup local testing of sandbox-shim.

Usage:
    export SYSCHANGE_BIN="$(pwd)/examples/mock_syschange.py"
    python3 shim.py
"""

import sys

def main() -> int:
    if len(sys.argv) < 2:
        print("usage: mock_syschange.py [plan <request> | approve <run_id> --yes]")
        return 1

    action = sys.argv[1]

    if action == "plan":
        request = sys.argv[2] if len(sys.argv) > 2 else "sample plan"
        print("run id: run-mock-demo1")
        print("risk  : low")
        print(f"- [OK] s1: echo 'Simulated execution of: {request}'")
        print("- [OK] s2: echo 'Mock verification check passed'")
        print("APPROVAL REQUIRED")
        print("        pre-test: PASS — exit=0, verify=ok, files=1")
        return 0

    if action == "approve":
        run_id = sys.argv[2] if len(sys.argv) > 2 else "run-mock-demo1"
        print(f"Applied {run_id} successfully in mock mode.")
        return 0

    print(f"mock_syschange: unknown action {action!r}")
    return 1

if __name__ == "__main__":
    sys.exit(main())
