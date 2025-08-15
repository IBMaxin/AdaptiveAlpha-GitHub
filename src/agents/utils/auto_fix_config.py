from typing import Dict, List, Any

MODEL_CONFIG: Dict[str, List[dict[str, Any]]] = {
    "primary": [
        {
            "name": "deepseek-coder:6.7b",
            "temp": 0.2,
            "context_length": 8192,
            "use_case": "python_fixes"
        },
        {
            "name": "codellama:7b",
            "temp": 0.1,
            "context_length": 8192,
            "use_case": "system_level"
        },
        {
            "name": "mistral:7b",
            "temp": 0.15,
            "context_length": 8192,
            "use_case": "general"
        }
    ],
    "fallback": [
        {
            "name": "wizardcoder:7b",
            "temp": 0.2,
            "context_length": 8192,
            "use_case": "refactoring"
        }
    ]
}

PROMPT_TEMPLATES = {
    "system_level": (
        "You are a Linux system expert and Python developer.\n"
        "Focus: Fixing system-level integration issues between WSL2 and Windows.\n"
        "Context: {context}\n"
        "Error: {error}\n"
        "Required: Generate ONLY unified diff patch, no explanations.\n"
    ),
    
    "python_fixes": (
        "You are a Python optimization specialist.\n"
        "Focus: Fixing Python-specific code issues, imports, and runtime errors.\n"
        "Context: {context}\n"
        "Error: {error}\n"
        "Style: Follow black formatting, use logging not print().\n"
        "Required: Generate ONLY unified diff patch, no explanations.\n"
    ),
    
    "debugging": (
        "You are a debugging expert.\n"
        "Focus: Identifying and fixing logical errors and edge cases.\n"
        "Context: {context}\n"
        "Error: {error}\n"
        "Required: Generate ONLY unified diff patch, no explanations.\n"
        "Include debug logging in critical sections.\n"
    ),
}

VALIDATION_RULES: dict[str, Any] = {
    "patch_format": r"^(---|\+\+\+|@@|[-+]|\\|\ ).*$",
    "python_syntax": r"^(def|class|import|from|if|for|while|try|except|async|await)",
    "banned_patterns": [
        r"print\(",
        r"import ipdb",
        r"import pdb",
        r"breakpoint\(\)"
    ]
}
