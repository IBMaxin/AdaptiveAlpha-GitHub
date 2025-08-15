"""Module: test_hardware_config.py — auto-generated docstring for flake8 friendliness."""

from pathlib import Path

config_path = Path("config/agents.yaml")
with config_path.open("r", encoding="utf-8") as f:
    lines = f.readlines()

hardware_block = []
for line in lines:
    if line.strip().startswith("# Hardware/LLM Studio Tuning"):
        hardware_block.append(line.strip())
        continue
    if hardware_block and (line.startswith("#") or line.strip() == ""):
        hardware_block.append(line.strip())
    elif hardware_block:
        break

if hardware_block:
    print("Hardware/LLM Studio Tuning block found:")
    print("\n".join(hardware_block))
else:
    print("Hardware/LLM Studio Tuning block NOT found!")
