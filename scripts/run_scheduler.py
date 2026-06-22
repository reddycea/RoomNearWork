from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime

JOBS = [
    ("saved_search_alerts", [sys.executable, "scripts/run_saved_search_alerts.py"], 3600),
    ("expire_listings", [sys.executable, "scripts/expire_listings.py"], 3600),
]


def main() -> None:
    last = {name: 0.0 for name, _, _ in JOBS}
    while True:
        now = time.time()
        for name, command, every in JOBS:
            if now - last[name] >= every:
                print(f"[{datetime.utcnow().isoformat()}] running {name}", flush=True)
                subprocess.run(command, check=False)
                last[name] = now
        time.sleep(30)


if __name__ == "__main__":
    main()
