#!/usr/bin/env bash
set -e

echo "============================================================"
echo "🚀 AI REVENUE RECOVERY AGENT — DEMO RUNNER"
echo "============================================================"

# Ensure virtualenv exists
if [ ! -d "venv" ]; then
    echo "[1/4] Creating virtual environment..."
    python3 -m venv venv
else
    echo "[1/4] Virtual environment exists."
fi

# Activate and install dependencies
source venv/bin/activate
echo "[2/4] Installing requirements..."
pip install -r requirements.txt -q

# Set dummy environment variables if not present
if [ ! -f .env ]; then
    echo "RAZORPAY_KEY=rzp_test_dummy" > .env
    echo "RAZORPAY_SECRET=dummy_secret" >> .env
fi
export $(grep -v '^#' .env | xargs)

echo "[3/4] Running end-to-end recovery pipeline..."
python run_pipeline.py --size 400

echo "[4/4] Launching Dashboard..."
streamlit run dashboard/app.py --server.headless true
