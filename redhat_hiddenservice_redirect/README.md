# Red Hat HiddenServices Redirect

This is for testing Spider without changing `HiddenServices.property`.

Source checked:

```text
D:\spider\dfcc-spider-core-confs\dev\configs\application\HiddenServices.property
D:\spider\dfcc-spider-core-confs\sit\configs\application\HiddenServices.property
D:\spider\dfcc-spider-core-confs\uat\configs\application\HiddenServices.property
D:\spider\dfcc-spider-core-confs\prod\configs\application\HiddenServices.property
```

Target mock:

```text
http://10.18.51.93:8780
```

## Important

`/etc/hosts` can only map a hostname to an IP address.

It cannot change:

- IP literal URLs like `http://10.18.50.145:7800`
- port, for example `7800` to `8780`
- protocol, for example `https` to `http`
- URL path

Because dev/sit/uat CBS/T24 in `HiddenServices.property` uses an IP literal, this will not work with `/etc/hosts`:

```text
10.18.50.145 10.18.51.93
```

For that case use the iptables DNAT script.

## Recommended For CBS Mock Test

This redirects dev/sit/uat CBS/T24 HTTP calls:

```text
Original: http://10.18.50.145:7800
Mock:     http://10.18.51.93:8780
```

Copy `iptables-cbs-mock-redirect.sh` to the Red Hat Spider server and run:

```bash
chmod +x iptables-cbs-mock-redirect.sh
sudo ./iptables-cbs-mock-redirect.sh 10.18.51.93 8780 add
```

Test from the Spider server:

```bash
curl -v http://10.18.50.145:7800/__mock/stats
```

If the redirect is active, this should hit the mock server and return mock stats.

List rules:

```bash
sudo ./iptables-cbs-mock-redirect.sh 10.18.51.93 8780 list
```

Remove rules:

```bash
sudo ./iptables-cbs-mock-redirect.sh 10.18.51.93 8780 delete
```

## Load Test Flow

### 1. Check mock directly

From the Windows jump server or any server that can reach the mock:

```bash
curl http://10.18.51.93:8780/__mock/stats
```

UI:

```text
http://10.18.51.93:8780/__mock/ui
```

Direct mock-only load test:

```bash
python load_test_mock.py --base-url http://10.18.51.93:8780 --tps 20 --duration 60 --timeout 20
```

This tests only the mock server. It does not prove Spider is using the mock.

### 2. Enable Spider redirect

Run this on the Red Hat server where Spider is running:

```bash
sudo ./iptables-cbs-mock-redirect.sh 10.18.51.93 8780 add
```

Verify from the same Red Hat server:

```bash
curl -v http://10.18.50.145:7800/__mock/stats
```

If this returns mock stats, Spider calls to `http://10.18.50.145:7800` will be redirected to `http://10.18.51.93:8780`.

### 3. Run the real load test

Reset mock stats first:

```bash
curl http://10.18.51.93:8780/__mock/reset
```

Then run the normal load test against Java Core or Spider, not directly against the mock.

Examples:

```text
Java Core/API gateway -> Spider -> original CBS URL -> iptables redirect -> mock
Spider API directly   -> original CBS URL -> iptables redirect -> mock
```

Watch this while the test is running:

```text
http://10.18.51.93:8780/__mock/ui
```

If `Current TPS`, `Max Observed TPS`, and `Total Requests` increase, the redirect path is working.

### 4. After test

Remove redirect:

```bash
sudo ./iptables-cbs-mock-redirect.sh 10.18.51.93 8780 delete
```

Confirm it is removed:

```bash
sudo ./iptables-cbs-mock-redirect.sh 10.18.51.93 8780 list
```

## When `/etc/hosts` Is Enough

`/etc/hosts` is enough only when the original URL uses a hostname and the mock listens on the same port/protocol expected by Spider.

Example:

```text
10.18.51.93 uat-esb.dfcc.net
```

But if Spider calls `https://uat-esb.dfcc.net:7083`, the mock must also support HTTPS on port `7083` with a certificate Spider accepts. Mapping the hostname alone will not convert HTTPS to HTTP.

## Extracted CBS/T24 Targets

Safe HTTP DNAT candidate:

| Env | Services | Original URL | Redirect Method |
|---|---|---|---|
| dev/sit/uat | `TemenosT24_CBS001`, `TemenosT24_CBS001_2S`, `TemenosT24_CBS001_3S`, `TemenosT24_CBS001_5S`, `TemenosT24_CBS002`, `TemenosT24_CBS003` | `http://10.18.50.145:7800` | iptables DNAT |

Needs HTTPS-capable mock/certificate:

| Env | Services | Original URL | Note |
|---|---|---|---|
| dev/sit/uat | `TemenosT24_CBS004`, `TemenosT24_CBS004_5S` | `https://uat-esb.dfcc.net:7083` | `/etc/hosts` alone is not enough |
| prod | all `TemenosT24_CBS*`, `LankaQR_LP002`, `GovermentPayment_GP001` | `https://esbprod.dfcc.net:7800` | do not redirect prod unless explicitly approved |

## Files

- `iptables-cbs-mock-redirect.sh` - Red Hat redirect script for dev/sit/uat CBS/T24 HTTP IP target.
- `hosts.cbs-example` - optional hostname examples only.
- `hosts.all-hiddenservices-example` - all hostname targets extracted from HiddenServices; use only for controlled testing.
