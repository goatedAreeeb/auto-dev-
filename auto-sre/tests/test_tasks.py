"""Unit tests for task definitions and registry."""

import pytest
from tasks.registry import get_task, list_tasks, TASK_REGISTRY


class TestRegistry:
    def test_list_tasks(self) -> None:
        ids = list_tasks()
        assert "t1_config" in ids
        assert "t2_port" in ids
        assert "t3_dep" in ids

    def test_get_valid_task(self) -> None:
        task = get_task("t1_config")
        assert task.task_id == "t1_config"
        assert task.max_steps > 0
        assert task.description

    def test_get_invalid_task(self) -> None:
        with pytest.raises(KeyError):
            get_task("nonexistent_task")


class TestTaskInitialStates:
    def test_t1_config_initial_state(self) -> None:
        task = get_task("t1_config")
        fs, pm = task.build_initial_state()
        # The broken state should have conf.bak, not conf
        assert fs.exists("/etc/app/conf.bak")
        assert not fs.exists("/etc/app/conf")

    def test_t2_port_initial_state(self) -> None:
        task = get_task("t2_port")
        fs, pm = task.build_initial_state()
        # Port 8080 should be occupied
        assert not pm.is_port_free(8080)

    def test_t3_dep_initial_state(self) -> None:
        task = get_task("t3_dep")
        fs, pm = task.build_initial_state()
        # node_modules should NOT exist
        assert not fs.exists("/home/user/app/node_modules/.package-lock.json")
        # package.json should exist
        assert fs.exists("/home/user/app/package.json")
