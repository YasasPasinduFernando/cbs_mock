# Run T24/CBS Mock on Ubuntu VPS

You can run this mock on Ubuntu either with Docker or directly with Python.

## Option 1 - Docker

Install Docker if needed:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin
sudo systemctl enable --now docker
```

Copy the `cbs_mock` folder to the VPS, then:

```bash
cd cbs_mock
sudo docker compose up -d --build
```

Check logs:

```bash
sudo docker logs -f t24-cbs-mock
```

Open UI:

```text
http://YOUR_VPS_IP:8780/__mock/ui
```

Stats:

```bash
curl http://127.0.0.1:8780/__mock/stats
```

Stop:

```bash
sudo docker compose down
```

## Option 2 - Direct Python

Python 3 is enough; no external packages are required.

```bash
sudo apt update
sudo apt install -y python3
cd cbs_mock
python3 mock_t24_cbs.py --host 0.0.0.0 --port 8780
```

Open UI:

```text
http://YOUR_VPS_IP:8780/__mock/ui
```

## Run as systemd Service Without Docker

Copy `cbs_mock` to:

```text
/opt/cbs_mock
```

Create service:

```bash
sudo tee /etc/systemd/system/cbs-mock.service >/dev/null <<'EOF'
[Unit]
Description=T24/CBS Mock Server
After=network.target

[Service]
WorkingDirectory=/opt/cbs_mock
ExecStart=/usr/bin/python3 /opt/cbs_mock/mock_t24_cbs.py --host 0.0.0.0 --port 8780 --config /opt/cbs_mock/mock_config.json
Restart=always
RestartSec=3
User=root

[Install]
WantedBy=multi-user.target
EOF
```

Start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now cbs-mock
sudo systemctl status cbs-mock
```

Logs:

```bash
journalctl -u cbs-mock -f
```

Stop:

```bash
sudo systemctl stop cbs-mock
```

## Firewall

If UFW is enabled:

```bash
sudo ufw allow 8780/tcp
sudo ufw status
```

If cloud provider firewall/security group exists, open TCP port `8780` there too.

## Spider Config

When mock runs on VPS, Spider hidden service URI should use the VPS IP:

```ini
uri = http://YOUR_VPS_IP:8780
protocol = http
```

Do this only in dev/SIT/test configs.
