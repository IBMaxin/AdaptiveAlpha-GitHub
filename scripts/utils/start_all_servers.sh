#!/bin/bash
# Auto-start Freqtrade and Healing Server in background, safe for endpoint checks

# Start Freqtrade webserver in background with logging
nohup freqtrade webserver --config config.json >freqtrade_webserver.log 2>&1 &
echo "Started Freqtrade webserver in background. Logs: freqtrade_webserver.log"

# Start Healing Server (FastAPI) in background with logging
nohup uvicorn services.healing_server:app --reload --host 0.0.0.0 --port 8000 >healing_server.log 2>&1 &
echo "Started Healing Server (FastAPI) in background on 0.0.0.0:8000. Logs: healing_server.log"

# Print running background jobs
jobs -l

echo "You can now safely check endpoints with curl or browser without killing servers."
