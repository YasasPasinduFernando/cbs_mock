# T24/CBS Mock Server

This mock simulates a CBS/T24 backend with a configurable TPS capacity.

Default behavior:
- Capacity: `35 TPS`
- Normal response time: around `1s`, endpoint-specific profiles adjust this.
- When traffic goes above `35 TPS`, response delay increases up to `10s`.
- By default it does not fail requests; it delays them. You can configure failure rate if needed.

The mock uses only Python standard library.

For Ubuntu VPS/Docker deployment, see:

```text
cbs_mock/run_on_ubuntu.md
```

## Run

```powershell
python cbs_mock\mock_t24_cbs.py
```

Server:

```text
http://127.0.0.1:8780
```

Browser UI:

```text
http://127.0.0.1:8780/__mock/ui
```

From this page you can change:

- `Capacity TPS`
- default normal/max latency
- overload exponent
- error rate over capacity
- endpoint-profile normal/max latency values

Changes apply immediately for new requests; no restart is needed.

Stats endpoint:

```text
http://127.0.0.1:8780/__mock/stats
```

Config endpoint:

```text
http://127.0.0.1:8780/__mock/config
```

Runtime config update:

```powershell
curl -X POST "http://127.0.0.1:8780/__mock/config" -H "Content-Type: application/json" -d "{\"capacity_tps\":20,\"normal_latency_ms\":1500,\"max_latency_ms\":10000}"
```

Reset stats:

```text
http://127.0.0.1:8780/__mock/reset
```

## Example Calls

```powershell
curl "http://127.0.0.1:8780/esb/DFCC_OB_NEW/v1/OB_SA_details?CIF_NO=100001"
curl "http://127.0.0.1:8780/esb/DFCC_OB_NEW/v1/OB_LOAN_details?CIF_NO=100001"
curl -X POST "http://127.0.0.1:8780/esb/transaction/v1/fundTransfer" -H "Content-Type: application/json" -d "{\"amount\":\"100.00\"}"
curl -X POST "http://127.0.0.1:8780/rest/epicapi/fundTransfer" -H "Content-Type: application/json" -H "Application: dfcc go" -d "{\"object\":{\"transactionType\":1,\"privateData\":\"0\",\"messageFormatVersion\":\"01\",\"channelType\":1,\"applicationID\":\"001\",\"uniqueNumber\":\"SYMF202602121506444333040\",\"transactionDateAndTime\":\"0212150644\"},\"rrn\":\"102604301389\"}"
```

The response includes headers:

```text
X-Mock-Current-TPS
X-Mock-Capacity-TPS
X-Mock-Delay-Ms
X-Mock-Over-Capacity
X-Mock-Replay
```

`X-Mock-Replay: true` means the mock returned a log-derived replay response
from `replay_responses_2026-06-09.json`. `false` means it used the generic
synthetic fallback response.

The current default config loads:

```text
replay_responses_2026-06-09.json
```

Those replay responses were extracted from the 2026-06-09 SIT Spider trace and
cover these exact CBS calls:

```text
GET /esb/DFCC_OB_NEW/v1/OB_CUST_view?clientId=518996
GET /esb/DFCC_OB_NEW/v1/OB_FD_details?CIF_NO=518996
GET /esb/DFCC_OB_NEW/v1/OB_LOAN_details?CIF_NO=110185
GET /esb/DFCC_OB_NEW/v1/OB_LOAN_details?CIF_NO=518996
GET /esb/DFCC_OB_NEW/v1/OB_SA_details?CIF_NO=1018563
GET /esb/DFCC_OB_NEW/v1/OB_SA_details?CIF_NO=110185
GET /esb/DFCC_OB_NEW/v1/OB_CA_details?CIF_NO=1018563
GET /esb/DFCC_OB_NEW/v1/OB_CASA_view?accountNo=102003987261
GET /esb/DFCC_OB_NEW/v1/OB_CASA_view?accountNo=102000318539
```

## CBS/T24 Paths Seen in Logs

The mock accepts any path, but these high-volume backend paths were seen in the logs and have profile-specific latency behavior:

```text
GET  /esb/DFCC_OB_NEW/v1/OB_SA_details
GET  /esb/DFCC_OB_NEW/v1/OB_CA_details
GET  /esb/DFCC_OB_NEW/v1/OB_FD_details
GET  /esb/DFCC_OB_NEW/v1/OB_LOAN_details
GET  /esb/DFCC_OB_NEW/v1/OB_CUST_view
GET  /esb/DFCC_OB_NEW/v1/OB_CASA_view
GET  /t24_account_statement_api/v1/getAccMiniStatement
POST /esb/transaction/v1/fundTransfer
POST /dfcc_ob_transactions/v1/createDfccFundsTransfer
POST /rest/epicapi/fundTransfer
POST /ob_qrpayment/v1/OB_postCeftInwdRevampQrPymnt
POST /esb/ob_account_opening/v1/savingsAccountRupee
POST /esb/ob_account_opening/v1/acctPayments
POST /esb/ob_fdopen/v1/maturityDepositRupee
POST /esb/ob_fdopen/v1/interestPayoutDepositRupee
```

The main CBS paths above return synthetic payloads shaped for the Spider service code paths we inspected:

```text
SavingsAccountDetails_CBS008
CurrentAccountDetails_CBS006
FixedDepositDetails_CBS010
LoanDetails_CBS020
AccountDetails_CBS002
CustomerDetailsCID_CBS003
TransactionListing_CBS017
FundTransfer_CBS011
EpicFundTransfer_EPIC001
```

`/rest/epicapi/fundTransfer` returns the EPIC API response shape:

```json
{
  "object": {
    "messageFormatVersion": "01",
    "applicationID": "001",
    "channelType": "1",
    "transactionType": "1",
    "uniqueNumber": "SYMF202602121506444333040",
    "transactionDateAndTime": "0212150644",
    "privateData": "0"
  },
  "status": "5",
  "rrn": "102604301389",
  "responseCode": "00",
  "common": null,
  "stan": "123456",
  "refNo": "RANDOM_32_HEX_VALUE",
  "profileCode": null
}
```

If Spider is still configured to call `https://uateconnector.dfcc.net:8090`,
the request must be routed to this mock with a matching protocol/port setup
or by changing the relevant hidden-service config to the mock URL.

This is enough for latency/load/timeout benchmarking. It is not a full T24 simulator for every business field and every edge case.

## Load Test

Run below capacity:

```powershell
python cbs_mock\load_test_mock.py --tps 20 --duration 30 --timeout 15
```

Run above the T24 capacity:

```powershell
python cbs_mock\load_test_mock.py --tps 50 --duration 30 --timeout 15
```

Expected behavior:
- Around `20 TPS`: response times should stay near normal profile values.
- Above `35 TPS`: mock response times should increase toward `10s`.

## Configuration

Edit:

```text
cbs_mock/mock_config.json
```

Important fields:

```json
{
  "capacity_tps": 35,
  "normal_latency_ms": 1000,
  "max_latency_ms": 10000,
  "error_rate_over_capacity": 0.0
}
```

If you want overload to return errors as well as delays, set:

```json
"error_rate_over_capacity": 0.05
```

That means roughly 5% of over-capacity requests will return HTTP `503`.

## Spider Integration Notes

Point Spider CBS endpoint configuration to this mock host/port for local/load-test environments.

If Spider expects the original hostnames, either:
- change Spider endpoint configs to `http://127.0.0.1:8780/...`, or
- route those hostnames to the mock through a test DNS/hosts/proxy setup.

Do not copy real CBS response payloads into this mock. The included responses are synthetic.
