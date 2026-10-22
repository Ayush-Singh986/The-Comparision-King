"""Run a bounded storefront API load test without synthetic customer events."""

from __future__ import annotations

import argparse
import http.client
import http.cookiejar
import json
import math
import statistics
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from typing import Any

MAX_USERS = 10
MAX_DURATION_SECONDS = 180
REQUEST_TIMEOUT_SECONDS = 10
RECOMMENDATION_INTERVAL_SECONDS = 8


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, file_pointer, code, message, headers, new_url):
        return None


def validate_target(
    base_url: str,
    confirmed_host: str,
    users: int,
    duration_seconds: int,
    think_time_seconds: float,
) -> str:
    parsed = urllib.parse.urlparse(base_url)
    if parsed.scheme not in ("https", "http") or not parsed.hostname:
        raise ValueError("Target must be an absolute HTTP(S) URL.")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("Target URL must contain only the scheme and host.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials must not be embedded in the target URL.")
    host = parsed.hostname.lower()
    if confirmed_host.lower() != host:
        raise ValueError("--confirm-target must exactly match the target hostname.")
    local_hosts = {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and host in local_hosts):
        raise ValueError("HTTPS is required except for localhost development.")
    if not 1 <= users <= MAX_USERS:
        raise ValueError(f"Users must be between 1 and {MAX_USERS}.")
    if not 1 <= duration_seconds <= MAX_DURATION_SECONDS:
        raise ValueError(f"Duration must be between 1 and {MAX_DURATION_SECONDS} seconds.")
    if not 0.25 <= think_time_seconds <= 30:
        raise ValueError("Think time must be between 0.25 and 30 seconds.")
    return base_url.rstrip("/")


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return round(ordered[index], 2)


def summarize_results(
    records: list[dict[str, Any]], elapsed_seconds: float, users: int
) -> dict[str, Any]:
    latencies = [record["latency_ms"] for record in records]
    statuses = Counter(
        str(record["status"]) if record["status"] is not None else "network_error"
        for record in records
    )
    failures = sum(
        record["status"] is None or not 200 <= record["status"] < 300
        for record in records
    )
    count = len(records)
    return {
        "virtual_users": users,
        "elapsed_seconds": round(elapsed_seconds, 2),
        "requests": count,
        "successful_requests": count - failures,
        "failed_requests": failures,
        "error_rate_percent": round(100 * failures / count, 2) if count else 0,
        "requests_per_second": round(count / elapsed_seconds, 2) if elapsed_seconds else 0,
        "latency_ms": {
            "mean": round(statistics.fmean(latencies), 2) if latencies else 0,
            "p50": percentile(latencies, 0.50),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "max": round(max(latencies), 2) if latencies else 0,
        },
        "status_codes": dict(sorted(statuses.items())),
    }


def record_request(
    opener: urllib.request.OpenerDirector,
    url: str,
    method: str,
    records: list[dict[str, Any]],
    lock: threading.Lock,
) -> int | None:
    started = time.perf_counter()
    status_code: int | None = None
    try:
        request = urllib.request.Request(
            url,
            data=b"" if method == "POST" else None,
            method=method,
            headers={"User-Agent": "Northstar-BoundedLoadTest/1.0"},
        )
        with opener.open(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            status_code = response.status
            response.read()
    except urllib.error.HTTPError as error:
        status_code = error.code
        error.close()
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError):
        status_code = None
    record = {
        "status": status_code,
        "latency_ms": (time.perf_counter() - started) * 1000,
    }
    with lock:
        records.append(record)
    return status_code


def run_virtual_user(
    base_url: str,
    deadline: float,
    think_time_seconds: float,
    records: list[dict[str, Any]],
    lock: threading.Lock,
) -> None:
    cookie_jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookie_jar),
        NoRedirectHandler(),
    )
    session_status = record_request(
        opener, f"{base_url}/api/store/session", "POST", records, lock
    )
    if session_status is None or not 200 <= session_status < 300:
        return

    next_recommendation = time.monotonic()
    request_index = 0
    paths = ("/api/health", "/api/store/catalog")
    while time.monotonic() < deadline:
        now = time.monotonic()
        if now >= next_recommendation:
            path = "/api/store/recommendations"
            next_recommendation = now + RECOMMENDATION_INTERVAL_SECONDS
        else:
            path = paths[request_index % len(paths)]
            request_index += 1
        record_request(opener, f"{base_url}{path}", "GET", records, lock)
        time.sleep(think_time_seconds)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bounded synthetic load test for the Northstar storefront API."
    )
    parser.add_argument("--base-url", required=True, help="HTTPS origin, with no path.")
    parser.add_argument(
        "--confirm-target",
        required=True,
        help="Must exactly match the target hostname to prevent accidental runs.",
    )
    parser.add_argument("--users", type=int, default=4, help=f"Virtual users (max {MAX_USERS}).")
    parser.add_argument(
        "--duration-seconds",
        type=int,
        default=60,
        help=f"Run duration (max {MAX_DURATION_SECONDS}).",
    )
    parser.add_argument(
        "--think-time-seconds",
        type=float,
        default=1,
        help="Pause between requests for each virtual user (0.25-30 seconds).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        base_url = validate_target(
            args.base_url,
            args.confirm_target,
            args.users,
            args.duration_seconds,
            args.think_time_seconds,
        )
    except ValueError as error:
        raise SystemExit(str(error)) from error

    records: list[dict[str, Any]] = []
    records_lock = threading.Lock()
    started = time.monotonic()
    deadline = started + args.duration_seconds
    with ThreadPoolExecutor(max_workers=args.users) as executor:
        futures = [
            executor.submit(
                run_virtual_user,
                base_url,
                deadline,
                args.think_time_seconds,
                records,
                records_lock,
            )
            for _ in range(args.users)
        ]
        for future in futures:
            future.result()
    elapsed = time.monotonic() - started
    report = summarize_results(records, elapsed, args.users)
    report["target_host"] = urllib.parse.urlparse(base_url).hostname
    report["traffic_note"] = (
        "Synthetic API traffic only. No browser impressions, clicks, or orders are generated. "
        "Recommendation requests use empty-history sessions and should not invoke Bedrock."
    )
    print(json.dumps(report, indent=2))
    return 1 if report["failed_requests"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
