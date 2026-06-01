# Spider Integration Guide for T24/CBS Mock

## Purpose

This guide explains how to connect Spider middleware to the local T24/CBS mock server.

Target test flow:

```text
Java/Spring Boot/Core -> Spider middleware -> Mock T24/CBS
```

The mock replaces the real T24/CBS endpoint only for test/load-test environments. It simulates:

- T24/CBS style HTTP endpoints.
- Configurable TPS capacity, default `35 TPS`.
- Configurable response delay, default up to `10s` under overload.
- Synthetic CBS-like responses for the main slow APIs.

Do not use this in production configuration.

## Files

Mock server:

```text
cbs_mock/mock_t24_cbs.py
```

Mock UI:

```text
http://127.0.0.1:8780/__mock/ui
```

Load tester:

```text
cbs_mock/load_test_mock.py
```

Double-click launchers:

```text
run_cbs_mock.bat
cbs_mock/run_cbs_mock_here.bat
```

## Step 1 - Start the Mock

From project root:

```powershell
.\run_cbs_mock.bat
```

Or from inside `cbs_mock`:

```powershell
.\run_cbs_mock_here.bat
```

Manual run:

```powershell
cd "C:\Users\HP\Desktop\New folder (2)\cbs_mock"
python .\mock_t24_cbs.py
```

Keep the command window open while testing.

## Step 2 - Open the UI

Open:

```text
http://127.0.0.1:8780/__mock/ui
```

Use the UI to change:

- Capacity TPS
- normal latency
- max latency
- jitter
- overload exponent
- error rate over capacity
- per-endpoint profile delays

Click `Save Runtime Config` after changing values.

Use the test buttons:

- `Test CBS Loan`
- `Test CBS Savings`
- `Test Fund Transfer`

If those work, `Total Requests` should increase in the UI.

## Step 3 - Change Spider Hidden Service URL

Spider CBS/T24 hidden service config is here:

```text
D:\spider\dfcc-spider-core-confs\dev\configs\application\HiddenServices.property
```

Change only test/dev/SIT config. Do not change production config.

### Main CBS Services to Point to Mock

Update these hidden service sections:

```text
TemenosT24_CBS001
TemenosT24_CBS001_5S
TemenosT24_CBS002
TemenosT24_CBS003
TemenosT24_CBS004
TemenosT24_CBS004_5S
```

For each section, set:

```ini
uri = http://127.0.0.1:8780
protocol = http
```

Keep these existing settings as-is:

```ini
dynamic_routes = ["service_endpoint"]
query_params = [...]
api = rest
content_type = json
http_method = GET / POST / DELETE
default_headers = ...
header_params = ...
read_timeout = ...
connect_timeout = ...
```

### Example Before

```ini
[TemenosT24_CBS001]
service_name = TemenosT24_CBS001
uri = http://10.18.50.145:7800
dynamic_routes = ["service_endpoint"]
api = rest
content_type = json
http_method = GET
protocol = http
default_headers = {"Accept": "application/json", "credentials": "OBBANK0800/AAbank@100CC"}
```

### Example After

```ini
[TemenosT24_CBS001]
service_name = TemenosT24_CBS001
uri = http://127.0.0.1:8780
dynamic_routes = ["service_endpoint"]
api = rest
content_type = json
http_method = GET
protocol = http
default_headers = {"Accept": "application/json", "credentials": "OBBANK0800/AAbank@100CC"}
```

### Important for CBS004

If the section currently uses HTTPS:

```ini
uri = https://uat-esb.dfcc.net:7083
protocol = https
certificate = acuatsit.crt
```

For local mock testing change to:

```ini
uri = http://127.0.0.1:8780
protocol = http
```

The certificate line is not needed for the local HTTP mock.

## Step 4 - Localhost vs Container/Remote Machine

Use `127.0.0.1` only if Spider and the mock run on the same Windows host.

If Spider runs inside Docker/container, `127.0.0.1` means the container itself, not your Windows host.

For Docker/container testing, use one of these:

```ini
uri = http://host.docker.internal:8780
```

or use the Windows host IP:

```ini
uri = http://YOUR_MACHINE_IP:8780
```

Example:

```ini
uri = http://192.168.1.50:8780
```

Make sure firewall allows port `8780`.

## Step 5 - Restart/Reload Spider

After changing `HiddenServices.property`, restart or reload Spider according to your normal process.

If running Spider directly:

```powershell
cd D:\spider\spider-core
python run\StartSpiderServer.py
```

If running through Docker:

```powershell
cd D:\spider\spider-core
docker compose restart spider-core
```

If the config is loaded through mounted files or a separate config loader, make sure the changed `HiddenServices.property` is the one Spider actually uses.

## Step 6 - Verify Spider Is Hitting the Mock

In the mock UI:

```text
http://127.0.0.1:8780/__mock/ui
```

Check:

- `Total Requests` increases when Java/Core calls Spider.
- `Current TPS` changes during load test.
- `X-Mock-Delay-Ms` appears on direct mock test responses.

Stats endpoint:

```text
http://127.0.0.1:8780/__mock/stats
```

If `Total Requests` stays `0`, Spider is not reaching the mock.

## Step 7 - Load Test

Below T24 capacity:

```powershell
python cbs_mock\load_test_mock.py --tps 20 --duration 30 --timeout 15
```

Above T24 capacity:

```powershell
python cbs_mock\load_test_mock.py --tps 50 --duration 30 --timeout 20
```

Expected:

- Around `20 TPS`: response time stays closer to normal delay.
- Above `35 TPS`: response time increases toward max delay.

For real Spider benchmarking, send load to Java/Core or Spider, not directly to the mock. Direct mock load test is only to verify the mock behavior.

## Covered Slow APIs

The mock returns Spider-compatible synthetic response shapes for the main slow CBS APIs:

```text
SavingsAccountDetails_CBS008
CurrentAccountDetails_CBS006
FixedDepositDetails_CBS010
LoanDetails_CBS020
AccountDetails_CBS002
CustomerDetailsCID_CBS003
TransactionListing_CBS017
FundTransfer_CBS011
```

Covered backend paths:

```text
GET  /esb/DFCC_OB_NEW/v1/OB_SA_details
GET  /esb/DFCC_OB_NEW/v1/OB_CA_details
GET  /esb/DFCC_OB_NEW/v1/OB_FD_details
GET  /esb/DFCC_OB_NEW/v1/OB_LOAN_details
GET  /esb/DFCC_OB_NEW/v1/OB_CUST_view
GET  /esb/DFCC_OB_NEW/v1/OB_CASA_view
GET  /t24_account_statement_api/v1/getAccMiniStatement
POST /dfcc_ob_transactions/v1/createDfccFundsTransfer
POST /esb/transaction/v1/fundTransfer
```

Unknown paths still return a generic success response, but exact business schema is not guaranteed.

## Troubleshooting

### UI shows Total Requests = 0

Spider is not calling the mock. Check:

- Hidden service `uri`.
- Spider is using the config file you edited.
- Mock server command window is still open.
- Docker/container cannot use `127.0.0.1` for host mock.
- Firewall allows port `8780`.

### Spider receives connection refused

Mock is not running or wrong host/port is configured.

Check:

```text
http://127.0.0.1:8780/__mock/stats
```

### Spider receives SSL/certificate error

You pointed an HTTPS hidden service section to the HTTP mock but left:

```ini
protocol = https
certificate = ...
```

For local mock testing use:

```ini
protocol = http
uri = http://127.0.0.1:8780
```

### Spider response becomes Internal Server Error

The endpoint may need a more exact response schema. Check Spider logs for the failing service and field name. Then add that field to `synthetic_payload()` in:

```text
cbs_mock/mock_t24_cbs.py
```

## Safe Testing Notes

- Use dev/SIT/test configs only.
- Do not modify production `HiddenServices.property`.
- Do not put real customer payloads into the mock.
- For fund transfer/payment APIs, avoid retry tests unless idempotency is guaranteed.

