#!/usr/bin/env python3
"""Daily crawler for the latest cases on China Judgments Online (wenshu.court.gov.cn).

Notes:
- The site uses anti-scraping protections; you may need to provide cookies, tokens,
  or adjust headers/params based on your access.
- Configure the request in the generated JSON config before running in production.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

DEFAULT_CONFIG: Dict[str, Any] = {
    "api_url": "https://wenshu.court.gov.cn/website/parse/rest.q4w",
    "method": "POST",
    "headers": {
        "User-Agent": "Mozilla/5.0 (compatible; WenshuDailyCrawler/1.0)",
        "Accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    },
    "params": {},
    "payload": {
        "s": "",
        "sortFields": "s50:desc",
        "pageId": "",
        "pageNum": "1",
        "pageSize": "20",
        "queryCondition": "",
    },
    "result_path": ["data", "list"],
    "output_dir": "data",
    "timeout_seconds": 20,
}


def load_config(path: Path) -> Dict[str, Any]:
    if not path.exists():
        path.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=2))
        print(
            f"Config file created at {path}. Please update it with valid parameters.",
            file=sys.stderr,
        )
        return DEFAULT_CONFIG
    return json.loads(path.read_text(encoding="utf-8"))


def extract_result(payload: Any, path: Iterable[str]) -> Any:
    current = payload
    for key in path:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return None
    return current


def fetch_latest_cases(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    method = config.get("method", "POST").upper()
    url = config["api_url"]
    headers = config.get("headers", {})
    params = config.get("params", {})
    payload = config.get("payload", {})
    timeout = config.get("timeout_seconds", 20)

    if method == "GET":
        response = requests.get(url, headers=headers, params=params, timeout=timeout)
    else:
        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=payload,
            timeout=timeout,
        )

    response.raise_for_status()
    data = response.json()
    result_path = config.get("result_path", [])
    cases = extract_result(data, result_path) if result_path else data

    if cases is None:
        raise ValueError(
            "Unable to find case list using result_path. "
            "Please update result_path in config."
        )
    if isinstance(cases, dict):
        return [cases]
    if not isinstance(cases, list):
        raise ValueError("Unexpected case list type in response payload.")
    return cases


def write_cases(cases: List[Dict[str, Any]], output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    output_path = output_dir / f"cases-{today}.json"
    payload = {
        "date": today,
        "count": len(cases),
        "cases": cases,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    return output_path


def update_state(state_path: Path, count: int) -> None:
    state = {
        "last_run": dt.datetime.now(dt.timezone.utc).isoformat(),
        "last_count": count,
    }
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2))


def run_once(config_path: Path) -> None:
    config = load_config(config_path)
    cases = fetch_latest_cases(config)
    output_dir = Path(config.get("output_dir", "data"))
    output_path = write_cases(cases, output_dir)
    update_state(output_dir / "state.json", len(cases))
    print(f"Saved {len(cases)} cases to {output_path}")


def sleep_until(target_time: dt.time) -> None:
    now = dt.datetime.now()
    next_run = dt.datetime.combine(now.date(), target_time)
    if next_run <= now:
        next_run += dt.timedelta(days=1)
    seconds = (next_run - now).total_seconds()
    print(f"Next run at {next_run.isoformat()} (sleeping {int(seconds)}s)")
    time.sleep(seconds)


def parse_time(value: str) -> dt.time:
    try:
        hour, minute = value.split(":", 1)
        return dt.time(hour=int(hour), minute=int(minute))
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Time must be in HH:MM format") from exc


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Daily crawler for China Judgments Online (Wenshu)."
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("crawler_config.json"),
        help="Path to crawler configuration JSON.",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit.",
    )
    parser.add_argument(
        "--time",
        type=parse_time,
        default=dt.time(hour=2, minute=0),
        help="Daily run time in HH:MM (24h) format.",
    )
    args = parser.parse_args()

    if args.once:
        run_once(args.config)
        return 0

    print("Starting daily crawler loop. Press Ctrl+C to stop.")
    while True:
        sleep_until(args.time)
        try:
            run_once(args.config)
        except Exception as exc:  # pylint: disable=broad-except
            print(f"Run failed: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
