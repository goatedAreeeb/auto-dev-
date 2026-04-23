"""Debug script: trace every task's grade outcome for the optimal command sequence."""
import sys
sys.path.insert(0, ".")

from app.routes._session import Session

SEQUENCES = {
    "t1_config": ["mv /etc/app/conf.bak /etc/app/conf", "systemctl restart app"],
    "t2_port": ["ps", "kill -9 {rogue_pid}", "systemctl restart app"],
    "t3_dep": ["npm install", "systemctl restart app"],
    "t4_trap": ["cat /etc/app/conf", "ps", "ls /etc/app"],
    "t5_disk_full": ["rm /var/log/syslog"],
    "t6_oom_killer": ["ps", "kill -9 {rogue_pid}"],
    "t7_cascading_meltdown": ["df -h", "rm /var/log/syslog", "ps", "kill -9 {rogue_pid}", "systemctl restart db"],
    "t8_memory_leak_loop": ["ps", "kill -9 {rogue_pid}", "systemctl restart leak-daemon"],
    "t9_dependency_chain_failure": ["systemctl restart db", "systemctl restart cache", "systemctl restart app"],
    "t10_config_secret_failure": ["cat /var/log/app.log", "echo DB_PASSWORD=CORRECT_SECRET > /etc/app/secrets.conf", "systemctl restart app"],
}

for task_id, cmds in SEQUENCES.items():
    s = Session()
    s.load_task(task_id)
    rogue_pid = s.sandbox.state.get("rogue_pid", 999)
    print(f"\n{'='*60}")
    print(f"TASK: {task_id}  | rogue_pid={rogue_pid}")
    print(f"Initial state: {s.sandbox.state}")
    for cmd_template in cmds:
        cmd = cmd_template.replace("{rogue_pid}", str(rogue_pid))
        result = s.sandbox.execute(cmd)
        reward, done, msg = s.task_def.grader.grade(
            s.sandbox.fs, s.sandbox.pm, s.sandbox.command_history, s.sandbox.state
        )
        print(f"  $ {cmd}")
        print(f"    stdout={result.stdout[:80]!r}  stderr={result.stderr[:80]!r}")
        print(f"    reward={reward:.3f}  done={done}  [{msg}]")
    print(f"Final state: svcs={s.sandbox.state.get('services_running')} config_valid={s.sandbox.state.get('config_valid')}")
