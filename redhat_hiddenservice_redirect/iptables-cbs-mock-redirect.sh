#!/usr/bin/env bash
set -euo pipefail

MOCK_IP="${1:-10.18.51.93}"
MOCK_PORT="${2:-8780}"
ACTION="${3:-add}"

ORIGINAL_CBS_IP="10.18.50.145"
ORIGINAL_CBS_PORT="7800"

usage() {
  cat <<USAGE
Usage:
  sudo $0 [mock_ip] [mock_port] add
  sudo $0 [mock_ip] [mock_port] delete
  sudo $0 [mock_ip] [mock_port] list

Default:
  mock_ip   = 10.18.51.93
  mock_port = 8780

Redirected:
  http://${ORIGINAL_CBS_IP}:${ORIGINAL_CBS_PORT} -> http://MOCK_IP:MOCK_PORT

This is intended for dev/sit/uat CBS/T24 HTTP services in HiddenServices.property.
USAGE
}

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run with sudo."
  exit 1
fi

if ! command -v iptables >/dev/null 2>&1; then
  echo "iptables command not found. Install iptables-services or use nftables equivalent."
  exit 1
fi

OUTPUT_RULE=(
  OUTPUT
  -p tcp
  -d "${ORIGINAL_CBS_IP}"
  --dport "${ORIGINAL_CBS_PORT}"
  -j DNAT
  --to-destination "${MOCK_IP}:${MOCK_PORT}"
)

PREROUTING_RULE=(
  PREROUTING
  -p tcp
  -d "${ORIGINAL_CBS_IP}"
  --dport "${ORIGINAL_CBS_PORT}"
  -j DNAT
  --to-destination "${MOCK_IP}:${MOCK_PORT}"
)

MASQUERADE_RULE=(
  POSTROUTING
  -p tcp
  -d "${MOCK_IP}"
  --dport "${MOCK_PORT}"
  -j MASQUERADE
)

add_rule() {
  if ! iptables -t nat -C "$@" 2>/dev/null; then
    iptables -t nat -A "$@"
  fi
}

delete_rule() {
  while iptables -t nat -C "$@" 2>/dev/null; do
    iptables -t nat -D "$@"
  done
}

case "${ACTION}" in
  add)
    add_rule "${OUTPUT_RULE[@]}"
    add_rule "${PREROUTING_RULE[@]}"
    add_rule "${MASQUERADE_RULE[@]}"
    echo "Added CBS/T24 redirect to ${MOCK_IP}:${MOCK_PORT}"
    ;;
  delete|del|remove)
    delete_rule "${OUTPUT_RULE[@]}"
    delete_rule "${PREROUTING_RULE[@]}"
    delete_rule "${MASQUERADE_RULE[@]}"
    echo "Deleted CBS/T24 redirect to ${MOCK_IP}:${MOCK_PORT}"
    ;;
  list)
    iptables -t nat -S | grep -E "(${ORIGINAL_CBS_IP}|${MOCK_IP}|${MOCK_PORT})" || true
    ;;
  -h|--help|help)
    usage
    ;;
  *)
    usage
    exit 1
    ;;
esac
