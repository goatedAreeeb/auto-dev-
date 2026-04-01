# API Contracts

## 1. Base URL
```
http://localhost:8000
```

---

## 2. Endpoints

### 2.1 `POST /reset`
Resets the environment to a specified task's initial "broken" state.

**Request Body:**
```json
{
  "task_id": "t1_config"
}
```

**Response `200 OK`:**
```json
{
  "observation": {
    "stdout": "Environment reset to task t1_config.",
    "stderr": "",
    "cwd": "/home/user",
    "health_status": false
  },
  "info": {
    "task_id": "t1_config",
    "description": "A critical config file has been misnamed.",
    "max_steps": 10
  }
}
```

---

### 2.2 `POST /step`
Executes a single agent action (shell command) inside the sandbox.

**Request Body:**
```json
{
  "tool": "run_command",
  "arguments": "mv /etc/app/conf.bak /etc/app/conf"
}
```

**Response `200 OK`:**
```json
{
  "observation": {
    "stdout": "",
    "stderr": "",
    "cwd": "/home/user",
    "health_status": true
  },
  "reward": 1.0,
  "done": true,
  "info": {
    "steps_taken": 1,
    "max_steps": 10,
    "grader_message": "Service is healthy. Task complete."
  }
}
```

**Response `400 Bad Request` (disallowed command):**
```json
{
  "detail": "Command 'format c:' is not in the allowed command set."
}
```

**Response `408 Request Timeout` (step exceeds 5s):**
```json
{
  "detail": "Step execution timed out after 5 seconds."
}
```

---

### 2.3 `GET /state`
Returns the current metadata of the environment without performing any action.

**Response `200 OK`:**
```json
{
  "task_id": "t1_config",
  "step_count": 3,
  "health_status": false,
  "is_done": false
}
```

---

## 3. Data Schemas (Pydantic v2)

### `DevOpsAction` (Request)
| Field       | Type   | Required | Description                            |
| :---------- | :----- | :------- | :------------------------------------- |
| `tool`      | `str`  | Yes      | Tool name, e.g. `run_command`          |
| `arguments` | `str`  | Yes      | The shell command string to execute    |

### `Observation` (Response)
| Field           | Type   | Description                                     |
| :-------------- | :----- | :---------------------------------------------- |
| `stdout`        | `str`  | Standard output of the executed command          |
| `stderr`        | `str`  | Standard error of the executed command           |
| `cwd`           | `str`  | Current working directory after execution        |
| `health_status` | `bool` | Whether the target service is currently healthy  |

### `StepResponse` (Response Wrapper)
| Field         | Type          | Description                               |
| :------------ | :------------ | :---------------------------------------- |
| `observation` | `Observation` | The resulting observation                  |
| `reward`      | `float`       | Reward value (0.0 to 1.0)                 |
| `done`        | `bool`        | Whether the episode has ended              |
| `info`        | `dict`        | Additional metadata (steps, grader message)|
