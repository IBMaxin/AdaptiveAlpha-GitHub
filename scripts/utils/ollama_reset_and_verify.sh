#!/bin/bash

# ollama_reset_and_verify.sh
# Robust script: kills all Ollama processes, clears cache, starts clean, verifies, and logs everything.

LOG=~/ollama_reset.log
echo "==== Ollama Clean Start $(date) ====" | tee -a $LOG

# 1. Kill all Ollama processes in WSL2 (exclude this script)
echo "[WSL2] Killing all Ollama processes except this script..." | tee -a $LOG
MY_PID=$$
ps -eo pid,cmd | grep '[o]llama' | awk -v mypid=$MY_PID '$1 != mypid {print $1}' | xargs -r sudo kill -9
echo "[WSL2] Killed Ollama processes (excluding this script)." | tee -a $LOG
sleep 2

# 2. Prompt to kill Ollama in Windows
echo "[Windows] Please run in Windows PowerShell as Admin: taskkill /IM ollama.exe /F" | tee -a $LOG
sleep 2

# 3. Remove all cached models in WSL2
echo "[WSL2] Removing all cached models..." | tee -a $LOG
ollama list | awk '{print $1}' | grep -v NAME | xargs -r ollama rm && echo "[WSL2] Removed all cached models." | tee -a $LOG
sleep 2

# 4. Start Ollama server in WSL2 (for local use only)
echo "[WSL2] Starting Ollama server..." | tee -a $LOG
nohup ollama serve > ~/ollama_server.log 2>&1 &
sleep 5
ps aux | grep '[o]llama serve' && echo "[WSL2] Ollama server started." | tee -a $LOG

# 5. Verify Ollama server in WSL2
echo "[WSL2] Verifying localhost API..." | tee -a $LOG
if curl -s http://localhost:11434/api/tags | grep -q 'models'; then
	echo "[WSL2] Localhost API check PASSED." | tee -a $LOG
else
	echo "[WSL2] Localhost API check FAILED!" | tee -a $LOG
fi

# 6. Verify Ollama server in Windows from WSL2 (if Expose to network is enabled)
WINIP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
echo "[WSL2] Verifying Windows host API at $WINIP..." | tee -a $LOG
if curl -s http://$WINIP:11434/api/tags | grep -q 'models'; then
	echo "[WSL2] Windows API check PASSED." | tee -a $LOG
else
	echo "[WSL2] Windows API check FAILED!" | tee -a $LOG
fi

echo "==== Ollama Clean Start Complete $(date) ====" | tee -a $LOG
echo "See $LOG for details."
