import subprocess
try:
    ret = subprocess.run(["python", "scripts/run_hardcoded_agent.py"], capture_output=True, text=True, check=True)
    print("SUCCESS")
except subprocess.CalledProcessError as e:
    with open("crash_log.txt", "w", encoding="utf-8") as f:
        f.write("=== STDERR ===\n" + e.stderr)
        f.write("\n=== STDOUT ===\n" + e.stdout)
    print("CRASHED. Wrote log to crash_log.txt")
