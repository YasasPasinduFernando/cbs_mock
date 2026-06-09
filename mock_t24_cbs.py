#!/usr/bin/env python3
"""T24/CBS capacity and latency mock server.

The mock simulates a backend with a fixed TPS capacity. Once incoming request
rate rises above the configured capacity, response latency increases up to a
configured maximum instead of failing immediately.
"""

from __future__ import annotations

import argparse
import json
import random
import signal
import sys
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


DEFAULT_CONFIG = {
    "host": "127.0.0.1",
    "port": 8780,
    "capacity_tps": 35,
    "normal_latency_ms": 1000,
    "max_latency_ms": 10000,
    "jitter_ms": 120,
    "overload_exponent": 1.35,
    "error_rate_over_capacity": 0.0,
    "default_status": 200,
    "replay_file": "",
    "profiles": [],
}


class CapacityState:
    def __init__(self, config):
        self.config = config
        self.lock = threading.Lock()
        self.recent = deque()
        self.total_requests = 0
        self.completed_requests = 0
        self.error_requests = 0
        self.inflight = 0
        self.max_observed_tps = 0
        self.started_at = time.time()

    def begin_request(self):
        now = time.time()
        with self.lock:
            while self.recent and self.recent[0] < now - 1.0:
                self.recent.popleft()
            self.recent.append(now)
            current_tps = len(self.recent)
            self.max_observed_tps = max(self.max_observed_tps, current_tps)
            self.total_requests += 1
            self.inflight += 1
            total = self.total_requests
        return total, current_tps

    def finish_request(self, is_error=False):
        with self.lock:
            self.inflight = max(0, self.inflight - 1)
            self.completed_requests += 1
            if is_error:
                self.error_requests += 1

    def snapshot(self):
        now = time.time()
        with self.lock:
            while self.recent and self.recent[0] < now - 1.0:
                self.recent.popleft()
            return {
                "uptime_s": round(now - self.started_at, 3),
                "capacity_tps": self.config["capacity_tps"],
                "current_tps": len(self.recent),
                "max_observed_tps": self.max_observed_tps,
                "inflight": self.inflight,
                "total_requests": self.total_requests,
                "completed_requests": self.completed_requests,
                "error_requests": self.error_requests,
            }

    def reset(self):
        with self.lock:
            self.recent.clear()
            self.total_requests = 0
            self.completed_requests = 0
            self.error_requests = 0
            self.inflight = 0
            self.max_observed_tps = 0
            self.started_at = time.time()


def coerce_config_value(key, value):
    if key in {
        "port",
        "capacity_tps",
        "normal_latency_ms",
        "max_latency_ms",
        "jitter_ms",
        "default_status",
    }:
        return int(float(value))
    if key in {"overload_exponent", "error_rate_over_capacity"}:
        return float(value)
    return value


def apply_runtime_config(config, updates):
    allowed_top_level = {
        "capacity_tps",
        "normal_latency_ms",
        "max_latency_ms",
        "jitter_ms",
        "overload_exponent",
        "error_rate_over_capacity",
        "default_status",
    }
    for key in allowed_top_level:
        if key in updates:
            config[key] = coerce_config_value(key, updates[key])

    if "profiles" in updates:
        existing = {profile.get("name"): profile for profile in config.get("profiles", [])}
        new_profiles = []
        for incoming in updates.get("profiles", []):
            name = incoming.get("name")
            if not name:
                continue
            profile = dict(existing.get(name, {}))
            profile["name"] = name
            if "match" in incoming:
                profile["match"] = incoming["match"]
            for key in ("normal_latency_ms", "max_latency_ms"):
                if key in incoming:
                    profile[key] = coerce_config_value(key, incoming[key])
            new_profiles.append(profile)
        if new_profiles:
            config["profiles"] = new_profiles


UI_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>T24/CBS Mock Control</title>
  <style>
    :root {
      color-scheme: light;
      font-family: "Segoe UI", Arial, sans-serif;
      color: #15202b;
      background: #f5f7fa;
    }
    body {
      margin: 0;
      padding: 24px;
    }
    main {
      max-width: 1160px;
      margin: 0 auto;
    }
    h1 {
      margin: 0 0 6px;
      font-size: 26px;
    }
    h2 {
      margin: 0 0 14px;
      font-size: 17px;
    }
    p {
      margin: 0 0 14px;
      color: #51606f;
    }
    section {
      background: #fff;
      border: 1px solid #d9e1ea;
      border-radius: 8px;
      margin: 16px 0;
      padding: 18px;
      box-shadow: 0 1px 2px rgba(15, 23, 42, 0.05);
    }
    .grid {
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    }
    label {
      display: block;
      font-size: 12px;
      font-weight: 700;
      color: #334155;
      margin-bottom: 5px;
    }
    input {
      box-sizing: border-box;
      width: 100%;
      border: 1px solid #c7d2de;
      border-radius: 6px;
      padding: 9px 10px;
      font-size: 14px;
    }
    input:focus {
      border-color: #2563eb;
      outline: 2px solid rgba(37, 99, 235, 0.15);
    }
    button {
      border: 0;
      border-radius: 6px;
      background: #155eef;
      color: white;
      cursor: pointer;
      font-weight: 700;
      padding: 10px 14px;
    }
    button.secondary {
      background: #e2e8f0;
      color: #172033;
    }
    button.danger {
      background: #dc2626;
    }
    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }
    .profiles {
      display: grid;
      gap: 12px;
    }
    .profile {
      border: 1px solid #e0e7ef;
      border-radius: 8px;
      padding: 14px;
    }
    .profile-title {
      font-weight: 800;
      margin-bottom: 8px;
    }
    .matches {
      color: #64748b;
      font-family: Consolas, "Courier New", monospace;
      font-size: 11px;
      margin-bottom: 10px;
      word-break: break-word;
    }
    .stats {
      display: grid;
      gap: 10px;
      grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    }
    .stat {
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 12px;
    }
    .stat span {
      color: #64748b;
      display: block;
      font-size: 12px;
      font-weight: 700;
    }
    .stat strong {
      display: block;
      font-size: 22px;
      margin-top: 4px;
    }
    .status {
      min-height: 20px;
      margin-top: 10px;
      color: #166534;
      font-weight: 700;
    }
    .sample {
      background: #0f172a;
      border-radius: 8px;
      color: #dbeafe;
      font-family: Consolas, "Courier New", monospace;
      font-size: 12px;
      overflow-x: auto;
      padding: 12px;
      white-space: pre;
    }
  </style>
</head>
<body>
<main>
  <h1>T24/CBS Mock Control</h1>
  <p>Change TPS capacity and latency values. New requests use the saved values immediately.</p>

  <section>
    <h2>Live Stats</h2>
    <div class="stats" id="stats"></div>
    <div class="actions">
      <button class="secondary" onclick="loadAll()">Refresh</button>
      <button class="danger" onclick="resetStats()">Reset Stats</button>
      <button onclick="sendTest('/esb/DFCC_OB_NEW/v1/OB_LOAN_details?CIF_NO=100001')">Test CBS Loan</button>
      <button onclick="sendTest('/esb/DFCC_OB_NEW/v1/OB_SA_details?CIF_NO=100001')">Test CBS Savings</button>
      <button onclick="sendTest('/esb/transaction/v1/fundTransfer', 'POST')">Test Fund Transfer</button>
    </div>
  </section>

  <section>
    <h2>Global Behavior</h2>
    <div class="grid">
      <div><label>Capacity TPS</label><input id="capacity_tps" type="number" min="1"></div>
      <div><label>Default Normal Latency ms</label><input id="normal_latency_ms" type="number" min="0"></div>
      <div><label>Default Max Latency ms</label><input id="max_latency_ms" type="number" min="0"></div>
      <div><label>Jitter ms</label><input id="jitter_ms" type="number" min="0"></div>
      <div><label>Overload Exponent</label><input id="overload_exponent" type="number" min="0.1" step="0.05"></div>
      <div><label>Error Rate Over Capacity</label><input id="error_rate_over_capacity" type="number" min="0" max="1" step="0.01"></div>
    </div>
  </section>

  <section>
    <h2>Endpoint Profiles</h2>
    <div class="profiles" id="profiles"></div>
  </section>

  <section>
    <h2>Quick Test URLs</h2>
    <div class="sample">curl "http://127.0.0.1:8780/esb/DFCC_OB_NEW/v1/OB_LOAN_details?CIF_NO=100001"
curl -X POST "http://127.0.0.1:8780/esb/transaction/v1/fundTransfer" -H "Content-Type: application/json" -d "{\"amount\":\"100.00\"}"
python cbs_mock\load_test_mock.py --tps 50 --duration 30 --timeout 20</div>
  </section>

  <div class="actions">
    <button onclick="saveConfig()">Save Runtime Config</button>
    <button class="secondary" onclick="loadAll()">Reload From Server</button>
  </div>
  <div class="status" id="status"></div>
</main>

<script>
let config = null;

function setStatus(text, isError = false) {
  const el = document.getElementById("status");
  el.textContent = text;
  el.style.color = isError ? "#b91c1c" : "#166534";
}

async function getJson(url, options) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return await res.json();
}

function renderStats(stats) {
  const keys = [
    ["capacity_tps", "Capacity TPS"],
    ["current_tps", "Current TPS"],
    ["max_observed_tps", "Max Observed TPS"],
    ["inflight", "In Flight"],
    ["total_requests", "Total Requests"],
    ["error_requests", "Errors"]
  ];
  document.getElementById("stats").innerHTML = keys.map(([key, label]) =>
    `<div class="stat"><span>${label}</span><strong>${stats[key]}</strong></div>`
  ).join("");
}

function renderConfig() {
  for (const key of ["capacity_tps", "normal_latency_ms", "max_latency_ms", "jitter_ms", "overload_exponent", "error_rate_over_capacity"]) {
    document.getElementById(key).value = config[key];
  }
  document.getElementById("profiles").innerHTML = config.profiles.map((profile, index) => `
    <div class="profile">
      <div class="profile-title">${profile.name}</div>
      <div class="matches">${(profile.match || []).join("<br>")}</div>
      <div class="grid">
        <div>
          <label>Normal Latency ms</label>
          <input data-profile="${index}" data-key="normal_latency_ms" type="number" min="0" value="${profile.normal_latency_ms ?? config.normal_latency_ms}">
        </div>
        <div>
          <label>Max Latency ms</label>
          <input data-profile="${index}" data-key="max_latency_ms" type="number" min="0" value="${profile.max_latency_ms ?? config.max_latency_ms}">
        </div>
      </div>
    </div>
  `).join("");
}

async function loadAll() {
  try {
    const [stats, cfg] = await Promise.all([
      getJson("/__mock/stats"),
      getJson("/__mock/config")
    ]);
    config = cfg;
    renderStats(stats);
    renderConfig();
    setStatus("Loaded");
  } catch (err) {
    setStatus(`Load failed: ${err.message}`, true);
  }
}

function collectConfig() {
  const next = {
    capacity_tps: Number(document.getElementById("capacity_tps").value),
    normal_latency_ms: Number(document.getElementById("normal_latency_ms").value),
    max_latency_ms: Number(document.getElementById("max_latency_ms").value),
    jitter_ms: Number(document.getElementById("jitter_ms").value),
    overload_exponent: Number(document.getElementById("overload_exponent").value),
    error_rate_over_capacity: Number(document.getElementById("error_rate_over_capacity").value),
    profiles: config.profiles.map(profile => ({...profile}))
  };
  for (const input of document.querySelectorAll("[data-profile]")) {
    const index = Number(input.dataset.profile);
    next.profiles[index][input.dataset.key] = Number(input.value);
  }
  return next;
}

async function saveConfig() {
  try {
    const payload = collectConfig();
    config = await getJson("/__mock/config", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(payload)
    });
    renderConfig();
    await loadAll();
    setStatus("Saved. New requests will use this config.");
  } catch (err) {
    setStatus(`Save failed: ${err.message}`, true);
  }
}

async function resetStats() {
  try {
    await getJson("/__mock/reset");
    await loadAll();
    setStatus("Stats reset");
  } catch (err) {
    setStatus(`Reset failed: ${err.message}`, true);
  }
}

async function sendTest(path, method = "GET") {
  try {
    const started = performance.now();
    const options = {method};
    if (method !== "GET") {
      options.headers = {"Content-Type": "application/json"};
      options.body = JSON.stringify({amount: "100.00", mock: true});
    }
    const res = await fetch(path, options);
    await res.text();
    const elapsed = Math.round(performance.now() - started);
    const delay = res.headers.get("X-Mock-Delay-Ms");
    const tps = res.headers.get("X-Mock-Current-TPS");
    await loadAll();
    setStatus(`Test OK: HTTP ${res.status}, elapsed ${elapsed}ms, mock delay ${delay}ms, TPS ${tps}`);
  } catch (err) {
    setStatus(`Test failed: ${err.message}`, true);
  }
}

loadAll();
setInterval(async () => {
  try {
    renderStats(await getJson("/__mock/stats"));
  } catch (_) {}
}, 1500);
</script>
</body>
</html>
"""


def load_config(path):
    config = dict(DEFAULT_CONFIG)
    if path:
        with open(path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        config.update(loaded)
    return config


def load_replay_responses(config_path, config):
    replay_file = config.get("replay_file")
    if not replay_file:
        return []

    replay_path = Path(replay_file)
    if not replay_path.is_absolute():
        base = Path(config_path).resolve().parent if config_path else Path(__file__).resolve().parent
        replay_path = base / replay_path

    if not replay_path.exists():
        print(f"Replay file not found, using synthetic responses only: {replay_path}")
        return []

    with open(replay_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    responses = loaded.get("responses", [])
    print(f"Loaded {len(responses)} replay responses from {replay_path}")
    return responses


def profile_for_path(config, path):
    for profile in config.get("profiles", []):
        for token in profile.get("match", []):
            if token and token in path:
                merged = dict(config)
                merged.update(profile)
                return profile.get("name", "matched"), merged
    return "default", config


def compute_delay_ms(config, current_tps):
    capacity = max(1.0, float(config["capacity_tps"]))
    normal = float(config["normal_latency_ms"])
    max_latency = max(normal, float(config["max_latency_ms"]))
    jitter = float(config.get("jitter_ms", 0))
    exponent = float(config.get("overload_exponent", 1.35))

    if current_tps <= capacity:
        delay = normal
    else:
        pressure = min(1.0, (current_tps - capacity) / capacity)
        delay = normal + (max_latency - normal) * (pressure**exponent)

    if jitter:
        delay += random.uniform(-jitter, jitter)

    return max(0.0, min(max_latency, delay))


def replay_response_for(replay_responses, path, query):
    for item in replay_responses:
        if item.get("path") != path:
            continue
        expected_query = item.get("query") or {}
        matches = True
        for key, expected_value in expected_query.items():
            actual_values = query.get(key)
            if not actual_values or str(actual_values[0]) != str(expected_value):
                matches = False
                break
        if matches:
            return item
    return None


def synthetic_payload(path, method, query):
    if "OB_SA_details" in path:
        return [
            {
                "accountId": "102000000001",
                "accountType": "ACCOUNTS",
                "productGroup": "Savings Account - LCY",
                "drawPower": "125000.00",
                "workingBalance": "125000.00",
                "currency": "LKR",
                "accountStatus": "AUTH",
                "branchId": "LK0010001",
                "branchName": "MOCK BRANCH",
                "jointCustomer": "100001",
                "jointCustomerRole": "OWNER",
                "jointCustShortName": "MOCK CUSTOMER",
                "lockedAmount": "0",
                "floatBalance": "0",
                "customerPostingRestrict": "N",
            }
        ]
    if "OB_CA_details" in path:
        return [
            {
                "accountNumber": "101000000001",
                "accountType": "CURRENT",
                "productGroup": "Current Account - LCY",
                "workingBalance": "93000.00",
                "currency": "LKR",
                "accountStatus": "AUTH",
                "branchId": "LK0010001",
                "branchName": "MOCK BRANCH",
                "jointCustomer": "100001",
                "jointCustomerRole": "OWNER",
                "jointCusShortName": "MOCK CUSTOMER",
                "lockedAmount": "0",
                "floatBalance": "0",
                "customerPostingRestrict": "N",
            }
        ]
    if "OB_FD_details" in path:
        return [
            {
                "accountNumber": "103000000001",
                "accountType": "DEPOSITS",
                "principalAmount": "500000.00",
                "workingBalance": "500000.00",
                "interestRate": "8.75",
                "maturityDate": "2027-05-04",
                "currency": "LKR",
                "branchName": "MOCK BRANCH",
                "jointCustomer": "100001",
                "jointCustomerRole": "OWNER",
                "jointCustShortName": "MOCK CUSTOMER",
                "accountStatus": "CURRENT",
                "productId": "FD.DEPOSIT.MAT.P",
            }
        ]
    if "OB_LOAN_details" in path:
        return [
            {
                "accountNumber": "104000000001",
                "accountType": "LOANS",
                "outstandingBalance": "250000.00",
                "currency": "LKR",
                "status": "ACTIVE",
                "branchName": "MOCK BRANCH",
                "jointCustomer": "100001",
                "jointCustomerRole": "OWNER",
                "jointCusShortName": "MOCK CUSTOMER",
                "productGroup": "Personal Loan",
                "arrNo": "AA-MOCK-LOAN",
            }
        ]
    if "OB_CASA_view" in path:
        return [
            {
                "accountNo": query.get("accountNo", ["102000000001"])[0],
                "clientId": "100001",
                "accountName": "MOCK CUSTOMER",
                "ownershipType": "OWNER",
                "jointHolderIds": "",
                "jointHolderLegacyIds": "",
                "workingBalance": "125000.00",
                "floatBalance": "0",
                "accountCurrency": "LKR",
                "accountOpeningDate": "20260501",
                "product": "SA.SAVINGS.MOCK",
                "depositType": "SAVING",
                "authStatus": "verified",
                "accountInactiveStatus": "ACTIVE",
                "accountClosedDate": None,
                "accountBranch": "LK0010001",
                "drawPower": "125000.00",
                "lockedAmount": "0",
                "intRateKey": "2.50",
                "postingRestriction": "",
                "customerPostingRestrict": "N",
            }
        ]
    if "OB_CUST_view" in path or "OB_CASA_view" in path:
        return [
            {
                "clientId": query.get("clientId", ["100001"])[0],
                "fullName1": "MOCK",
                "fullName2": "CUSTOMER",
                "dob": "19900101",
                "customerSince": "20200101",
                "branchName": "MOCK BRANCH",
                "accountOfficer": "MOCK OFFICER",
                "mobileNumber": "94770000000",
                "email": "mock.customer@example.com",
                "Building Number": "1",
                "street": "Mock Street",
                "Address": "Mock Address",
                "town": "Colombo",
                "postCode": "00100",
                "country": "LK",
                "title": "MR",
                "customerStatus": "ACTIVE",
                "exitStatus": "",
                "target": "RETAIL",
                "gender": "M",
                "sector": "1000",
                "legalId": "900000000V",
                "legalDocName": "NIC",
            }
        ]
    if "fundTransfer" in path or "createDfccFundsTransfer" in path:
        external_ref = f"MOCK{int(time.time() * 1000)}"
        return {
            "header": {"status": "success", "audit": {"t24Time": int(time.time())}},
            "body": {
                "channel": "IDH",
                "debitAccount": "102000000001",
                "debitCurrency": "LKR",
                "debitAmount": "100.00",
                "debitReference": "MOCK DR",
                "creditAccount": "102000000002",
                "creditCurrency": "LKR",
                "creditAmount": "100.00",
                "creditReference": "MOCK CR",
                "externalTxnReference": external_ref,
                "transactionType": "400000",
            },
            "linkedActivities": [
                {"body": {"currencyId": "LKR", "accountId": "102000000002"}},
                {"body": {"currencyId": "LKR", "accountId": "102000000001"}},
            ],
        }
    if "getAccMiniStatement" in path:
        return {
            "header": {"status": "success", "total_size": 1},
            "body": [
                {
                    "tranDate": "2026-06-01",
                    "valueDate": "2026-06-01",
                    "reference": "MOCKTXN001",
                    "description": "MOCK TXN",
                    "credit": "1000.00",
                    "balance": "126000.00",
                }
            ],
        }
    return {
        "message": "Success",
        "mock": True,
        "method": method,
        "path": path,
    }


def make_handler(state, config, replay_responses):
    class MockHandler(BaseHTTPRequestHandler):
        server_version = "T24CBSMock/1.0"

        def log_message(self, fmt, *args):
            sys.stdout.write(
                "%s %s\n"
                % (time.strftime("%Y-%m-%d %H:%M:%S"), fmt % args)
            )

        def do_GET(self):
            self.handle_any()

        def do_POST(self):
            self.handle_any()

        def do_PUT(self):
            self.handle_any()

        def do_DELETE(self):
            self.handle_any()

        def read_body(self):
            length = int(self.headers.get("Content-Length") or 0)
            if length <= 0:
                return b""
            return self.rfile.read(length)

        def end_headers(self):
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,DELETE,OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type")
            super().end_headers()

        def do_OPTIONS(self):
            self.send_response(204)
            self.end_headers()

        def write_html(self, status, html):
            data = html.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def write_json(self, status, payload, extra_headers=None):
            data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            if extra_headers:
                for key, value in extra_headers.items():
                    self.send_header(key, str(value))
            self.end_headers()
            self.wfile.write(data)

        def handle_any(self):
            parsed = urlparse(self.path)

            if parsed.path in {"/", "/__mock/ui"}:
                self.write_html(200, UI_HTML)
                return
            if parsed.path == "/__mock/stats":
                self.write_json(200, state.snapshot())
                return
            if parsed.path == "/__mock/config":
                if self.command == "POST":
                    try:
                        body = self.read_body()
                        updates = json.loads(body.decode("utf-8") or "{}")
                        with state.lock:
                            apply_runtime_config(config, updates)
                        self.write_json(200, config)
                    except Exception as exc:
                        self.write_json(
                            400,
                            {
                                "message": "invalid config update",
                                "error": f"{type(exc).__name__}: {exc}",
                            },
                        )
                    return
                self.write_json(200, config)
                return
            if parsed.path == "/__mock/reset":
                state.reset()
                self.write_json(200, {"message": "reset complete"})
                return

            body = self.read_body()
            _ = body  # Body is consumed so clients can send real payloads.
            query = parse_qs(parsed.query)
            request_no, current_tps = state.begin_request()
            profile_name, effective = profile_for_path(config, parsed.path)
            delay_ms = compute_delay_ms(effective, current_tps)
            over_capacity = current_tps > int(config["capacity_tps"])
            error_rate = float(config.get("error_rate_over_capacity", 0.0))
            is_error = over_capacity and error_rate > 0 and random.random() < error_rate

            time.sleep(delay_ms / 1000.0)

            replay_item = None if is_error else replay_response_for(replay_responses, parsed.path, query)
            status = (
                503
                if is_error
                else int(replay_item.get("status", 200))
                if replay_item
                else int(effective.get("default_status", 200))
            )
            payload = (
                {"message": "Mock overloaded", "code": 503}
                if is_error
                else replay_item["body"]
                if replay_item
                else synthetic_payload(parsed.path, self.command, query)
            )
            headers = {
                "X-Mock-Request-No": request_no,
                "X-Mock-Profile": profile_name,
                "X-Mock-Replay": str(bool(replay_item)).lower(),
                "X-Mock-Current-TPS": current_tps,
                "X-Mock-Capacity-TPS": config["capacity_tps"],
                "X-Mock-Delay-Ms": int(delay_ms),
                "X-Mock-Over-Capacity": str(over_capacity).lower(),
            }
            try:
                self.write_json(status, payload, headers)
            finally:
                state.finish_request(is_error)

    return MockHandler


def main():
    parser = argparse.ArgumentParser(description="Run a T24/CBS latency mock.")
    parser.add_argument("--config", default=str(Path(__file__).with_name("mock_config.json")))
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    args = parser.parse_args()

    config = load_config(args.config)
    if args.host:
        config["host"] = args.host
    if args.port:
        config["port"] = args.port

    replay_responses = load_replay_responses(args.config, config)
    state = CapacityState(config)
    handler = make_handler(state, config, replay_responses)
    server = ThreadingHTTPServer((config["host"], int(config["port"])), handler)

    def shutdown(_signum=None, _frame=None):
        print("\nShutting down mock server...")
        server.shutdown()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(
        f"T24/CBS mock listening on http://{config['host']}:{config['port']} "
        f"(capacity={config['capacity_tps']} TPS, max_latency={config['max_latency_ms']}ms)"
    )
    print("Stats: http://%s:%s/__mock/stats" % (config["host"], config["port"]))
    server.serve_forever()


if __name__ == "__main__":
    main()
