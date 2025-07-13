# Supervisor Utility

`supervisor` is a powerful **process management system** and a **DevOps tool** designed for **application monitoring** and running arbitrary commands. It acts as a wrapper, ensuring **reliable execution** and **uninterrupted operation** of your services. `supervisor` intercepts process launches, tracks their completion or unresponsiveness (via a heartbeat file), and performs **automatic restarts** upon failure. It's an ideal solution for **daemon management**, scripts, and services without built-in watchdog capabilities, providing **application lifecycle management** and **operations automation**.

## Features

*   **Process Launch**: `supervisor` launches a specified command with its arguments, providing **task management** and **process control**.
*   **State Monitoring**: Continuously monitors the supervised process, ensuring **server reliability** and **performance optimization**.
*   **Heartbeat Check (Optional)**: Verifies process activity via a configurable heartbeat file, which is critical for **application monitoring**. **Disabled by default.**
*   **Automatic Restart**: `supervisor` performs **automatic restarts** of the process upon:
    *   Process exit (with non-zero code).
    *   Heartbeat timeout (if enabled), contributing to **uninterrupted operation**.
*   **Graceful Termination**: Attempts to gracefully terminate the supervised process using `SIGTERM` before resorting to `SIGKILL`, ensuring clean **service management**.
*   **Restart Policies**: Supports configurable maximum restart attempts and exponential backoff to prevent "death spirals", enhancing **server reliability**.
*   **Logging**: Provides detailed logging of events, including restart counts and backoff delays, with a clear `[SUPERVISOR]` prefix to distinguish its logs, simplifying **background task management** and **application deployment**.

## Usage

```bash
./supervisor [OPTIONS] <command> [args...]
```

### Options

*   `--timeout <seconds>`: Sets the heartbeat timeout in seconds. If the heartbeat file is not updated within this period, the process is considered unresponsive and restarted. **Only applicable if heartbeat is enabled.** Default: `20` seconds.
*   `--initial-check-delay <seconds>`: Sets an initial delay in seconds before `supervisor` starts checking the heartbeat file. Useful for commands that require time to initialize. Default: `0` seconds.
*   `--heartbeat-file <path>`: Specifies the path and name of the heartbeat file. This allows running multiple `supervisor` instances concurrently without conflicts. **Only applicable if heartbeat is enabled.** Default: `heartbeat.txt`.
*   `--grace-period <seconds>`: Sets the time in seconds `supervisor` waits for a process to terminate gracefully after sending `SIGTERM` before sending `SIGKILL`. Default: `5` seconds.
*   `--max-restarts <count>`: Sets the maximum number of consecutive restarts. If this limit is reached, `supervisor` will exit. Use `-1` for infinite restarts. Default: `-1`.
*   `--backoff-factor <factor>`: Sets the multiplier for exponential backoff between restarts. The delay is calculated as `factor * (2 ** restart_count)`. Default: `1` second.
*   `--enable-heartbeat`: Explicitly enables the heartbeat mechanism. **Heartbeat is disabled by default.**

### Examples

**Basic Usage (Heartbeat Disabled):**
```bash
./supervisor python3 client.py
```

**With Heartbeat Enabled and Custom Timeout:**
```bash
./supervisor --enable-heartbeat --timeout 30 python3 my_long_running_script.py
```

**Monitoring a Process with Periodic Crashes, Limited Restarts, and Heartbeat Enabled:**
```bash
./supervisor --enable-heartbeat --max-restarts 5 --backoff-factor 2 python3 test_client.py crash_periodic 60
```

**Running Multiple Supervisors Concurrently with Heartbeat Enabled:**
```bash
# In terminal 1
./supervisor --enable-heartbeat --heartbeat-file /tmp/heartbeat_app1.txt python3 client_app1.py

# In terminal 2
./supervisor --enable-heartbeat --heartbeat-file /tmp/heartbeat_app2.txt python3 client_app2.py
```

## Client Applications

For `supervisor` to effectively monitor a process using the heartbeat mechanism, the supervised application must periodically update a heartbeat file. The path to this file should be passed to the client application by `supervisor` (e.g., via CLI arguments or environment variables).

### `client.py` (Example Client)

A simple Python script that continuously writes the current timestamp to a specified heartbeat file (or `heartbeat.txt` by default) every 5 seconds.

```python
import time
import logging
import sys
import os

logging.basicConfig(level=logging.INFO)

HEARTBEAT_FILE = "heartbeat.txt" # Default value

def main():
    global HEARTBEAT_FILE
    if len(sys.argv) > 1:
        HEARTBEAT_FILE = sys.argv[1]
        logging.info(f"Using heartbeat file: {HEARTBEAT_FILE}")
    else:
        logging.info(f"Using default heartbeat file: {HEARTBEAT_FILE}")

    while True:
        try:
            with open(HEARTBEAT_FILE, "w") as f:
                f.write(str(time.time()))
            logging.info("Heartbeat sent")
        except IOError as e:
            logging.error(f"Error writing to heartbeat file {HEARTBEAT_FILE}: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()
```

### `test_client.py` (Advanced Test Client)

An advanced client designed to simulate various scenarios for comprehensive testing of `supervisor`. It supports:
*   `normal`: Normal operation, sending heartbeats and exiting gracefully.
*   `crash_periodic`: Simulates periodic crashes.
*   `hang`: Stops sending heartbeats to simulate unresponsiveness.
*   `sigterm_test`: Waits for a `SIGTERM` signal to demonstrate graceful shutdown.
*   `long_request`: Simulates a long operation without sending heartbeats for a specified duration.

Usage: `python3 test_client.py <scenario> [duration] [heartbeat_file_path]`

```python
import time
import logging
import sys
import os
import random
import signal

logging.basicConfig(level=logging.INFO)

HEARTBEAT_FILE = "heartbeat.txt" # Default value

def write_heartbeat():
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(time.time()))
    logging.info("Heartbeat sent")

def signal_handler(signum, frame):
    logging.info(f"Test client: Received signal {signum}. Exiting gracefully.")
    # No need to remove heartbeat file here, atexit in supervisor handles it
    sys.exit(0)

def main():
    global HEARTBEAT_FILE
    
    # Parse heartbeat file argument if provided
    # The heartbeat file argument for test_client.py will be the second argument after the scenario
    # e.g., python3 test_client.py normal heartbeat_test.txt
    # or python3 test_client.py normal 30 heartbeat_test.txt
    
    # Find the last argument that is not a number (scenario or duration)
    # This is a simplified parsing for test_client, supervisor handles its own args
    
    # Check if the last argument is a file path
    if len(sys.argv) > 1 and not sys.argv[-1].isdigit():
        HEARTBEAT_FILE = sys.argv[-1]
        logging.info(f"Test client: Using custom heartbeat file: {HEARTBEAT_FILE}")
        # Remove heartbeat file from sys.argv for scenario parsing
        sys.argv.pop(-1)
    else:
        logging.info(f"Test client: Using default heartbeat file: {HEARTBEAT_FILE}")

    # Clean up heartbeat file before starting, only if it's the default one or explicitly managed by client
    # In a real scenario, supervisor would manage the heartbeat file.
    # For testing, we ensure a clean state for the client's perspective.
    if os.path.exists(HEARTBEAT_FILE):
        try:
            os.remove(HEARTBEAT_FILE)
            logging.info(f"Test client: Cleaned up old heartbeat file: {HEARTBEAT_FILE}")
        except OSError as e:
            logging.error(f"Test client: Error removing old heartbeat file {HEARTBEAT_FILE}: {e}")

    signal.signal(signal.SIGTERM, signal_handler)
    scenario = sys.argv[1] if len(sys.argv) > 1 else "normal"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2].isdigit() else 30 # Default duration for some scenarios

    if scenario == "normal":
        logging.info(f"Test client: Normal operation (sending heartbeat for {duration} seconds)")
        start_time = time.time()
        while time.time() - start_time < duration:
            write_heartbeat()
            time.sleep(random.uniform(3, 7)) # Random pauses
        logging.info("Test client: Exiting normally.")
        sys.exit(0)
    elif scenario == "crash_periodic":
        logging.info(f"Test client: Simulating periodic crashes (sending heartbeat for {duration} seconds)")
        start_time = time.time()
        while time.time() - start_time < duration:
            write_heartbeat()
            time.sleep(random.uniform(3, 7))
            if random.random() < 0.2: # 20% chance to crash
                logging.error("Test client: Simulating a random crash!")
                sys.exit(1)
        logging.info("Test client: Exiting normally after periodic crashes.")
        sys.exit(0)
    elif scenario == "hang":
        logging.info(f"Test client: Simulating a hang (sending heartbeat for 10 seconds, then stopping heartbeat and looping)")
        for i in range(2): # Send heartbeat for 10 seconds (2 * 5s)
            write_heartbeat()
            time.sleep(5)
        logging.warning("Test client: Stopping heartbeat and entering infinite loop. Supervisor should detect timeout.")
        while True:
            time.sleep(1) # Simulate busy work without heartbeat
    elif scenario == "sigterm_test":
        logging.info("Test client: Waiting for SIGTERM (sending heartbeat)")
        while True:
            write_heartbeat()
            time.sleep(5)
    elif scenario == "long_request":
        logging.info(f"Test client: Simulating a long request (sending heartbeat, then pausing for {duration}s without heartbeat)")
        write_heartbeat()
        logging.info(f"Test client: Starting long operation, no heartbeat for {duration} seconds.")
        time.sleep(duration) # Simulate long operation without heartbeat
        write_heartbeat() # Heartbeat after long operation
        logging.info("Test client: Long operation finished, heartbeat sent. Exiting.")
        sys.exit(0)
    else:
        logging.error(f"Unknown scenario: {scenario}")
        sys.exit(1)

if __name__ == "__main__":
    main()