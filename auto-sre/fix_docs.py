import glob
import re

TEXT_REPLACEMENTS = {
    "reward\": 1.0": "reward\": 0.999999",
    "reward\": 0.0": "reward\": 0.000001",
    "0.0 to 1.0": "open interval (0, 1)",
    "0 to 1": "open interval (0, 1)",
    "[0.0, 1.0]": "open interval (0, 1)",
    "[0, 1]": "open interval (0, 1)",
    "Returns 1.0": "Returns 1 - 1e-6",
    "Returns 0.0": "Returns 1e-6",
    "scores 0": "scores 1e-6",
    "0.0, 1.0": "1e-6, 1-1e-6",
    "reward == 1.0": "reward >= 1 - 1e-6",
    "reward = 1.0": "reward = 1 - 1e-6",
    "reward = 0.0": "reward = 1e-6",
    "1.0": "0.999999", # Carefully applied
}

FILES = [
    "README.md",
    "8 scoring engine spec.md",
    "6 api contracts.md",
    "5 database schema.md",
    "12 testing strategy.md",
    "9 engineering scope definition.md",
    "4 system architecture.md",
    "11 environment and devops.md",
]

for filename in FILES:
    filepath = f"d:/hackathon/{filename}"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        new_content = content
        
        # Replace occurrences
        new_content = new_content.replace('reward": 1.0', 'reward": 0.999999')
        new_content = new_content.replace('reward": 0.0', 'reward": 0.000001')
        new_content = new_content.replace('0.0 to 1.0', 'open interval (0, 1)')
        new_content = new_content.replace('[0.0, 1.0]', 'open interval (0, 1)')
        new_content = new_content.replace('between 0 and 1', 'strictly between 0 and 1 (exclusive) — i.e. in the open interval (0, 1)')
        new_content = new_content.replace('Returns 1.0', 'Returns 1 - 1e-6')
        new_content = new_content.replace('Returns 0.0', 'Returns 1e-6')
        new_content = new_content.replace('scores 0', 'scores 1e-6')
        new_content = new_content.replace('reward == 1.0', 'reward >= 1-1e-6')
        new_content = new_content.replace('reward = 1.0', 'reward = 1-1e-6')
        new_content = new_content.replace('reward = 0.0', 'reward = 1e-6')

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Updated {filename}")
    except FileNotFoundError:
        pass
