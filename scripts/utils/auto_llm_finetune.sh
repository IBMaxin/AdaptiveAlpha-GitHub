#!/bin/bash
# Auto-export Freqtrade agent data and run Axolotl LLM fine-tuning

# 0. Run agent loop to generate new data (20 cycles)
echo "[Auto-LLM] Running agent loop to generate fresh data (20 cycles)..."
PYTHONPATH=. python -m agents.self_loop_agent --spec "Minimal robust Freqtrade strategy for BTC/USDT, 1h timeframe, with clear logic and comments" --config config.json --max-loops 20

# 1. Export agent learning log and trade book to JSONL for LLM training
echo "[Auto-LLM] Exporting ML logs to JSONL..."
python scripts/export_ml_logs_to_jsonl.py --log user_data/learning_log.csv --trades user_data/ml_trades_book.csv --out ./llm_train_data.jsonl

# 2. Generate Axolotl config for Qwen2.5-7B (edit as needed for your GPU/model)

cat <<EOF >axolotl_config.yaml
base_model: Qwen/Qwen1.5-7B-Chat
datasets:
  - path: ./llm_train_data.jsonl
    type: alpaca
output_dir: ./finetuned-llm
adapter: qlora
load_in_8bit: true
batch_size: 2
# gradient_accumulation_steps removed for compatibility
num_epochs: 3
fp16: true
EOF

echo "[Auto-LLM] Axolotl config generated."

# 3. Run Axolotl fine-tuning
echo "[Auto-LLM] Starting Axolotl fine-tuning..."
axolotl train axolotl_config.yaml

echo "[Auto-LLM] Fine-tuning complete. Model saved to ./finetuned-llm"
