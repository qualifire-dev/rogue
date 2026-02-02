#!/usr/bin/env bash
# Healthcheck display for Rogue dev services

GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
DIM='\033[2m'
BOLD='\033[1m'
RESET='\033[0m'

check_service() {
    local name="$1"
    local url="$2"
    local port="$3"

    if curl -sf --max-time 2 "$url" > /dev/null 2>&1; then
        printf "  ${GREEN}●${RESET}  %-22s ${DIM}:${port}${RESET}\n" "$name"
    else
        printf "  ${RED}●${RESET}  %-22s ${DIM}:${port}${RESET}\n" "$name"
    fi
}

echo ""
printf "  ${BOLD}${CYAN}Rogue Services${RESET}        ${DIM}$(date +%H:%M:%S)${RESET}\n"
echo "  ─────────────────────────────"
echo ""
check_service "Server"           "http://localhost:8000/api/v1/health" "8000"
check_service "TShirt Agent"     "http://localhost:10001/.well-known/agent.json" "10001"
check_service "Langgraph Agent"  "http://localhost:10002/.well-known/agent.json" "10002"
echo ""
printf "  ${GREEN}●${RESET} up  ${RED}●${RESET} down       ${DIM}refreshes every 5s${RESET}\n"
