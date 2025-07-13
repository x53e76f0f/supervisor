# Supervisor Utility

`supervisor` is a lightweight utility designed to run and monitor arbitrary commands. It acts as a wrapper, intercepting process launches, tracking their completion or unresponsiveness (via a heartbeat file), and automatically restarting them upon failure. It is intended for services, scripts, and daemons without built-in watchdog capabilities.

## Features

*   **Process Launch**: Launches a specified command with its arguments.
*   **State Monitoring**: Continuously monitors the supervised process.
*   **Heartbeat Check**: Verifies process activity via a configurable heartbeat file.
*   **Automatic Restart**: Restarts the process upon:
    *   Process exit (with non-zero code).
    *   Heartbeat timeout.
*   **Graceful Termination**: Attempts to gracefully terminate the supervised process using `SIGTERM` before resorting to `SIGKILL`.
*   **Restart Policies**: Supports configurable maximum restart attempts and exponential backoff to prevent "death spirals".
*   **Logging**: Provides detailed logging of events, including restart counts and backoff delays.

## Usage

```bash
./supervisor [OPTIONS] <command> [args...]
```

### Options

*   `--timeout <seconds>`: Sets the heartbeat timeout in seconds. If the heartbeat file is not updated within this period, the process is considered unresponsive and restarted. Default: `20` seconds.
*   `--initial-check-delay <seconds>`: Sets an initial delay in seconds before `supervisor` starts checking the heartbeat file. Useful for commands that require time to initialize. Default: `0` seconds.
*   `--heartbeat-file <path>`: Specifies the path and name of the heartbeat file. This allows running multiple `supervisor` instances concurrently without conflicts. Default: `heartbeat.txt`.
*   `--grace-period <seconds>`: Sets the time in seconds `supervisor` waits for a process to terminate gracefully after sending `SIGTERM` before sending `SIGKILL`. Default: `5` seconds.
*   `--max-restarts <count>`: Sets the maximum number of consecutive restarts. If this limit is reached, `supervisor` will exit. Use `-1` for infinite restarts. Default: `-1`.
*   `--backoff-factor <factor>`: Sets the multiplier for exponential backoff between restarts. The delay is calculated as `factor * (2 ** restart_count)`. Default: `1` second.

### Examples

**Basic Usage:**
```bash
./supervisor python3 client.py
```

**With Custom Timeout and Initial Delay:**
```bash
./supervisor --timeout 30 --initial-check-delay 10 python3 my_long_running_script.py
```

**Monitoring a Process with Periodic Crashes and Limited Restarts:**
```bash
./supervisor --max-restarts 5 --backoff-factor 2 python3 test_client.py crash_periodic 60
```

**Running Multiple Supervisors Concurrently:**
```bash
# In terminal 1
./supervisor --heartbeat-file /tmp/heartbeat_app1.txt python3 client_app1.py

# In terminal 2
./supervisor --heartbeat-file /tmp/heartbeat_app2.txt python3 client_app2.py
```

## Client Applications

For `supervisor` to effectively monitor a process, the supervised application must periodically update a heartbeat file.

### `client.py` (Example Client)

A simple Python script that continuously writes the current timestamp to `heartbeat.txt` every 5 seconds.

```python
import time
import logging

logging.basicConfig(level=logging.INFO)

def main():
    while True:
        with open("heartbeat.txt", "w") as f:
            f.write(str(time.time()))
        logging.info("Heartbeat sent")
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

Usage: `python3 test_client.py <scenario> [duration]`

```python
import time
import logging
import sys
import os
import random
import signal

logging.basicConfig(level=logging.INFO)
HEARTBEAT_FILE = "heartbeat.txt" # Note: This should be configured by supervisor via CLI arg or env var in real use

def write_heartbeat():
    with open(HEARTBEAT_FILE, "w") as f:
        f.write(str(time.time()))
    logging.info("Heartbeat sent")

def signal_handler(signum, frame):
    logging.info(f"Test client: Received signal {signum}. Exiting gracefully.")
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    scenario = sys.argv[1] if len(sys.argv) > 1 else "normal"
    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30 # Default duration for some scenarios

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
    # Clean up heartbeat file before starting
    if os.path.exists(HEARTBEAT_FILE):
        os.remove(HEARTBEAT_FILE)
    main()
```