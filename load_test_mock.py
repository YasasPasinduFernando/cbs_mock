#!/usr/bin/env python3
"""Small stdlib load tester for the T24/CBS mock."""

from __future__ import annotations

import argparse
import json
import statistics
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed


DEFAULT_PATHS = [
    "/esb/DFCC_OB_NEW/v1/OB_SA_details?CIF_NO=100001",
    "/esb/DFCC_OB_NEW/v1/OB_CA_details?CIF_NO=100001",
    "/esb/DFCC_OB_NEW/v1/OB_FD_details?CIF_NO=100001",
    "/esb/DFCC_OB_NEW/v1/OB_LOAN_details?CIF_NO=100001",
    "/esb/DFCC_OB_NEW/v1/OB_CUST_view?clientId=100001",
    "/esb/transaction/v1/fundTransfer",
    "/rest/epicapi/fundTransfer",
]


def epic_fund_transfer_request():
    return {
        "object": {
            "transactionType": 1,
            "privateData": "0",
            "messageFormatVersion": "01",
            "channelType": 1,
            "applicationID": "001",
            "uniqueNumber": f"SYMF{int(time.time() * 1000)}",
            "transactionDateAndTime": time.strftime("%m%d%H%M%S"),
        },
        "fromAccount": "102006511225",
        "fromAccountName": "MOCK CUSTOMER",
        "toAccount": "12345678",
        "toAccountName": "MOCK BENEFICIARY",
        "txnAmount": "000000550000",
        "tranCode": "52",
        "merchantType": "6013",
        "creditReference": "FT Other Bank",
        "serviceCharge": "000000002500",
        "destBankCode": "6990",
        "debitReference": "FT Other Bank",
        "rrn": f"{int(time.time() * 1000) % 1000000000000:012d}",
        "captureDate": time.strftime("%m%d"),
        "settlmentDate": time.strftime("%m%d"),
    }


def percentile(values, pct):
    if not values:
        return None
    ordered = sorted(values)
    idx = (len(ordered) - 1) * pct / 100.0
    lower = int(idx)
    upper = min(lower + 1, len(ordered) - 1)
    frac = idx - lower
    return ordered[lower] * (1 - frac) + ordered[upper] * frac


def request_once(base_url, path, timeout):
    url = base_url.rstrip("/") + path
    data = None
    headers = {}
    method = "GET"
    if "epicapi/fundTransfer" in path:
        method = "POST"
        data = json.dumps(epic_fund_transfer_request()).encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Application"] = "dfcc go"
    elif "fundTransfer" in path:
        method = "POST"
        data = json.dumps({"amount": "100.00", "mock": True}).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            resp.read()
            status = resp.status
            mock_delay = resp.headers.get("X-Mock-Delay-Ms")
            mock_tps = resp.headers.get("X-Mock-Current-TPS")
            ok = 200 <= status < 400
    except urllib.error.HTTPError as exc:
        exc.read()
        status = exc.code
        mock_delay = exc.headers.get("X-Mock-Delay-Ms")
        mock_tps = exc.headers.get("X-Mock-Current-TPS")
        ok = False
    except Exception as exc:
        return {
            "ok": False,
            "status": "timeout/error",
            "error": type(exc).__name__,
            "elapsed_ms": (time.perf_counter() - started) * 1000.0,
            "mock_delay_ms": None,
            "mock_tps": None,
        }
    return {
        "ok": ok,
        "status": status,
        "error": "",
        "elapsed_ms": (time.perf_counter() - started) * 1000.0,
        "mock_delay_ms": int(mock_delay) if mock_delay else None,
        "mock_tps": int(mock_tps) if mock_tps else None,
    }


def run_load(base_url, tps, duration, timeout, workers, paths):
    interval = 1.0 / tps
    total = int(tps * duration)
    results = []
    lock = threading.Lock()

    def task(i):
        result = request_once(base_url, paths[i % len(paths)], timeout)
        with lock:
            results.append(result)
        return result

    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        next_at = started
        for i in range(total):
            now = time.perf_counter()
            if now < next_at:
                time.sleep(next_at - now)
            futures.append(executor.submit(task, i))
            next_at += interval
        for future in as_completed(futures):
            future.result()

    elapsed = time.perf_counter() - started
    return results, elapsed


def print_summary(results, elapsed):
    latencies = [r["elapsed_ms"] for r in results]
    ok_count = sum(1 for r in results if r["ok"])
    errors = len(results) - ok_count
    print(f"Sent: {len(results)}")
    print(f"Elapsed: {elapsed:.2f}s")
    print(f"Achieved TPS: {len(results) / elapsed:.2f}")
    print(f"Success: {ok_count} ({ok_count / len(results) * 100:.1f}%)")
    print(f"Errors/timeouts: {errors} ({errors / len(results) * 100:.1f}%)")
    print(f"Mean: {statistics.mean(latencies):.0f}ms")
    for pct in (50, 80, 90, 95, 99):
        print(f"P{pct}: {percentile(latencies, pct):.0f}ms")
    print(f"Max: {max(latencies):.0f}ms")
    max_mock_tps = max((r["mock_tps"] or 0 for r in results), default=0)
    print(f"Max mock-observed TPS header: {max_mock_tps}")


def main():
    parser = argparse.ArgumentParser(description="Load test the CBS/T24 mock.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8780")
    parser.add_argument("--tps", type=float, default=20)
    parser.add_argument("--duration", type=float, default=30)
    parser.add_argument("--timeout", type=float, default=15)
    parser.add_argument("--workers", type=int, default=200)
    parser.add_argument("--paths", nargs="*", default=DEFAULT_PATHS)
    args = parser.parse_args()

    results, elapsed = run_load(
        args.base_url, args.tps, args.duration, args.timeout, args.workers, args.paths
    )
    print_summary(results, elapsed)


if __name__ == "__main__":
    main()
