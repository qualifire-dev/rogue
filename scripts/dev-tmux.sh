#!/usr/bin/env bash
set -euo pipefail

# ===========================================
# Rogue Development - Tmux Dashboard
# ===========================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
SESSION_NAME="rogue"

# Check if tmux is installed
if ! command -v tmux &> /dev/null; then
    echo "tmux is required but not installed. Install with: brew install tmux"
    exit 1
fi

# Kill existing session if it exists
tmux kill-session -t "$SESSION_NAME" 2>/dev/null || true

cd "$ROOT_DIR"

# Helper command to load env
ENV_CMD="set -a; source $ROOT_DIR/.env 2>/dev/null; set +a"

# Service commands (name|command)
declare -a SERVICES=(
    "Server|cd $ROOT_DIR && uv run python -m rogue server"
    "TUI|sleep 2 && cd $ROOT_DIR && make dev"
    "TShirt Agent|cd $ROOT_DIR && uv run --group examples python -m examples.tshirt_store_agent"
    "Langgraph Agent|cd $ROOT_DIR && uv run --group examples python -m examples.tshirt_store_langgraph_agent"
)

# Create new tmux session with first window
tmux new-session -d -s "$SESSION_NAME" -n "services" -x 200 -y 50

# Configure the session
tmux set-option -t "$SESSION_NAME" mouse on
tmux set-option -t "$SESSION_NAME" history-limit 50000

# Create 2x2 grid: split horizontal, then each half vertical
tmux split-window -t "$SESSION_NAME:0" -h
tmux select-pane -t "$SESSION_NAME:0.0"
tmux split-window -t "$SESSION_NAME:0.0" -v
tmux select-pane -t "$SESSION_NAME:0.2"
tmux split-window -t "$SESSION_NAME:0.2" -v

# Pane layout after splits:
#   0: top-left      2: top-right
#   1: bottom-left   3: bottom-right
PANE_ORDER=(0 2 1 3)

for i in "${!SERVICES[@]}"; do
    IFS='|' read -r name cmd <<< "${SERVICES[$i]}"
    pane_idx=${PANE_ORDER[$i]}
    tmux send-keys -t "$SESSION_NAME:0.$pane_idx" "$ENV_CMD && $cmd" C-m
done

# Equalize layout
tmux select-layout -t "$SESSION_NAME:0" tiled

# Add pane titles
tmux set-option -t "$SESSION_NAME" pane-border-status top
tmux set-option -t "$SESSION_NAME" pane-border-format " #{pane_index}: #T "

tmux select-pane -t "$SESSION_NAME:0.0" -T "Server"
tmux select-pane -t "$SESSION_NAME:0.1" -T "TUI"
tmux select-pane -t "$SESSION_NAME:0.2" -T "TShirt Agent"
tmux select-pane -t "$SESSION_NAME:0.3" -T "Langgraph Agent"

# Health check window
tmux new-window -t "$SESSION_NAME" -n "health"
tmux send-keys -t "$SESSION_NAME:health" "watch --color -n5 '$SCRIPT_DIR/healthcheck.sh'" C-m

# Shell window
tmux new-window -t "$SESSION_NAME" -n "shell"
tmux send-keys -t "$SESSION_NAME:shell" "cd $ROOT_DIR" C-m

# Select services window
tmux select-window -t "$SESSION_NAME:0"
tmux select-pane -t "$SESSION_NAME:0.0"

echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║          Rogue Development Dashboard                   ║"
echo "╠════════════════════════════════════════════════════════╣"
echo "║  Layout:                                               ║"
echo "║    ┌─────────────────┬─────────────────┐              ║"
echo "║    │     Server      │   TShirt Agent   │              ║"
echo "║    ├─────────────────┼─────────────────┤              ║"
echo "║    │      TUI        │ Langgraph Agent  │              ║"
echo "║    └─────────────────┴─────────────────┘              ║"
echo "║                                                        ║"
echo "║  Tmux Controls:                                        ║"
echo "║    Ctrl+B, arrow    Navigate between panes             ║"
echo "║    Ctrl+B, z        Zoom/unzoom current pane           ║"
echo "║    Ctrl+B, 1        Switch to 'health' window          ║"
echo "║    Ctrl+B, 2        Switch to 'shell' window           ║"
echo "║    Ctrl+B, d        Detach (services keep running)     ║"
echo "║    Mouse scroll     Scroll history                     ║"
echo "║                                                        ║"
echo "║  To reattach: tmux attach -t rogue                     ║"
echo "║  To stop:     make stop-tmux                           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo ""

# Attach to the session
tmux attach-session -t "$SESSION_NAME"
