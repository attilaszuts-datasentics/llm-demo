#!/bin/bash
# Start all 4 demo apps on different ports
# Usage: ./run_demos.sh

source .venv/bin/activate

echo ""
echo "Starting demos..."
echo "  Demo 1 — Pipeline:    http://localhost:8501"
echo "  Demo 2 — Compare:     http://localhost:8502"
echo "  Demo 3 — Review:      http://localhost:8503"
echo "  Demo 4 — Genie:       http://localhost:8504"
echo ""
echo "Press Ctrl+C to stop all."
echo ""

streamlit run demo_pipeline.py --server.port 8501 --server.headless true &
PID1=$!
streamlit run demo_compare.py  --server.port 8502 --server.headless true &
PID2=$!
streamlit run demo_review.py   --server.port 8503 --server.headless true &
PID3=$!
streamlit run demo_genie.py    --server.port 8504 --server.headless true &
PID4=$!

trap "kill $PID1 $PID2 $PID3 $PID4 2>/dev/null" EXIT INT TERM
wait
