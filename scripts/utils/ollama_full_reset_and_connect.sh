run it
/bash

echo "==== Ollama Full Reset Complete $(date) ====" | tee -a $LOG

LOG=~/ollama_full_reset.log
while true; do
  echo "==== Ollama Full Reset $(date) ====" | tee -a $LOG

  # 1. Kill all Ollama processes in WSL2 (excluding this script)
  echo "[WSL2] Killing all Ollama processes except this script..." | tee -a $LOG
  MY_PID=$$
  ps -eo pid,cmd | grep '[o]llama' | awk -v mypid=$MY_PID '$1 != mypid {print $1}' | xargs -r sudo kill -9
  echo "[WSL2] Killed Ollama processes (excluding this script)." | tee -a $LOG
  sleep 2

  # 2. Prompt for Windows steps
  echo "[ACTION REQUIRED] On Windows:" | tee -a $LOG
  echo "  - Enable 'Expose Ollama to the network' in the Ollama Desktop GUI." | tee -a $LOG
  echo "  - Open PowerShell as Admin and run: taskkill /IM ollama.exe /F" | tee -a $LOG
  echo "  - Restart Ollama Desktop GUI." | tee -a $LOG
  read -p "Press Enter after completing the Windows steps..."

  # 3. Remove all cached models in WSL2
  echo "[WSL2] Removing all cached models..." | tee -a $LOG
  ollama list | awk '{print $1}' | grep -v NAME | xargs -r ollama rm && echo "[WSL2] Removed all cached models." | tee -a $LOG
  sleep 2

  # 4. Start Ollama server in WSL2 (for local use/testing)
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

  # 6. Verify Ollama server in Windows from WSL2
  WINIP=$(cat /etc/resolv.conf | grep nameserver | awk '{print $2}')
  echo "[WSL2] Verifying Windows host API at $WINIP..." | tee -a $LOG
  if curl -s http://$WINIP:11434/api/tags | grep -q 'models'; then
      echo "[WSL2] Windows API check PASSED." | tee -a $LOG
  else
      echo "[WSL2] Windows API check FAILED!" | tee -a $LOG
  fi

  echo "==== Ollama Full Reset Complete $(date) ====" | tee -a $LOG
  echo "See $LOG for details."
  echo "--- Press Ctrl+C to exit, or Enter to run the loop again. ---"
  read -p ""
done
