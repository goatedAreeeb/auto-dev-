import codecs
import os

with codecs.open('d:/hackathon/auto-sre/temp_ui.py', 'r', encoding='utf-16le') as f:
    code = f.read()

code = code.replace('API_BASE = os.getenv("AUTO_SRE_URL", "http://127.0.0.1:8000")', 'ENV_URL = "https://goated1-auto-sre.hf.space"')
code = code.replace('API_BASE', 'ENV_URL')

with codecs.open('d:/hackathon/auto-sre/temp_ui.py', 'w', encoding='utf-8') as f:
    f.write(code)
