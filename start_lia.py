"""
LIA Windows Launcher — Start LIA Process
Runs LIA process independently of VS Code IDE.
"""
import sys
import json
from process_manager import get_process_manager

if __name__ == "__main__":
    pm = get_process_manager()
    res = pm.start()
    print(json.dumps(res, indent=2))
    sys.exit(0 if res.get("success") else 1)
