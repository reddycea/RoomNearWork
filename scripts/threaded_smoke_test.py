from __future__ import annotations

import argparse
import concurrent.futures
import urllib.request


def hit(url: str) -> int:
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', default='http://localhost:5000')
    parser.add_argument('--path', default='/health')
    parser.add_argument('--threads', type=int, default=20)
    parser.add_argument('--requests', type=int, default=100)
    args = parser.parse_args()
    target = args.url.rstrip('/') + args.path
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.threads) as pool:
        statuses = list(pool.map(hit, [target] * args.requests))
    ok = sum(1 for s in statuses if 200 <= s < 300)
    print(f'{ok}/{len(statuses)} successful responses')
    raise SystemExit(0 if ok == len(statuses) else 1)


if __name__ == '__main__':
    main()
