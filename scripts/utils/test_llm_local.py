"""Module: test_llm_local.py — auto-generated docstring for flake8 friendliness."""

from services.llm_client import LLMClient, load_cfg

cfg = load_cfg()
llm = LLMClient(cfg)
print("LLM base_url:", llm.base_url)
print("LLM model:", llm.model)
resp = llm.chat("You are a helpful assistant.", "Say: LLM Studio is working!")
print("LLM response:", resp[:200])
