#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
mkdir -p "$SCRIPT_DIR/logs"
cd "$SCRIPT_DIR/frontend"
nohup pnpm dev > "$SCRIPT_DIR/logs/frontend.log" 2>&1 &
echo "Frontend PID: $!" >> "$SCRIPT_DIR/logs/dev.log"
echo "Started at $(date)" >> "$SCRIPT_DIR/logs/dev.log"