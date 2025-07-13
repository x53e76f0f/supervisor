import time
import logging
import sys
import os
import random
import signal

logging.basicConfig(level=logging.INFO)
HEARTBEAT_FILE = "heartbeat.txt" # Default heartbeat file

def write_heartbeat(heartbeat_file_path):
    with open(heartbeat_file_path, "w") as f:
        f.write(str(time.time()))
    logging.info(f"Heartbeat sent to {heartbeat_file_path}")

def signal_handler(signum, frame):
    logging.info(f"Test client: Received signal {signum}. Exiting gracefully.")
    sys.exit(0)

def main():
    signal.signal(signal.SIGTERM, signal_handler)
    scenario = sys.argv[1] if len(sys.argv) > 1 else "normal"
    # Parse heartbeat file argument if present
    heartbeat_file_index = -1
    for i, arg in enumerate(sys.argv):
        if arg == "--heartbeat-file":
            if i + 1 < len(sys.argv):
                global HEARTBEAT_FILE
                HEARTBEAT_FILE = sys.argv[i+1]
                logging.info(f"Test client: Using custom heartbeat file: {HEARTBEAT_FILE}")
                # Remove the --heartbeat-file and its value from sys.argv for subsequent parsing
                sys.argv.pop(i+1)
                sys.argv.pop(i)
                break # Only expect one heartbeat file argument

    duration = int(sys.argv[2]) if len(sys.argv) > 2 else 30 # Default duration for some scenarios

    if scenario == "normal":
        logging.info(f"Test client: Normal operation (sending heartbeat for {duration} seconds)")
        start_time = time.time()
        while time.time() - start_time < duration:
            write_heartbeat(HEARTBEAT_FILE)
            time.sleep(random.uniform(3, 7)) # Random pauses
        logging.info("Test client: Exiting normally.")
        sys.exit(0)
    elif scenario == "crash_periodic":
        logging.info(f"Test client: Simulating periodic crashes (sending heartbeat for {duration} seconds)")
        start_time = time.time()
        while time.time() - start_time < duration:
            write_heartbeat(HEARTBEAT_FILE)
            time.sleep(random.uniform(3, 7))
            if random.random() < 0.2: # 20% chance to crash
                logging.error("Test client: Simulating a random crash!")
                sys.exit(1)
        logging.info("Test client: Exiting normally after periodic crashes.")
        sys.exit(0)
    elif scenario == "hang":
        logging.info(f"Test client: Simulating a hang (sending heartbeat for 10 seconds, then stopping heartbeat and looping)")
        for i in range(2): # Send heartbeat for 10 seconds (2 * 5s)
            write_heartbeat(HEARTBEAT_FILE)
            time.sleep(5)
        logging.warning("Test client: Stopping heartbeat and entering infinite loop. Supervisor should detect timeout.")
        while True:
            time.sleep(1) # Simulate busy work without heartbeat
    elif scenario == "sigterm_test":
        logging.info("Test client: Waiting for SIGTERM (sending heartbeat)")
        while True:
            write_heartbeat(HEARTBEAT_FILE)
            time.sleep(5)
    elif scenario == "long_request":
        logging.info(f"Test client: Simulating a long request (sending heartbeat, then pausing for {duration}s without heartbeat)")
        write_heartbeat(HEARTBEAT_FILE)
        logging.info(f"Test client: Starting long operation, no heartbeat for {duration} seconds.")
        time.sleep(duration) # Simulate long operation without heartbeat
        write_heartbeat(HEARTBEAT_FILE) # Heartbeat after long operation
        logging.info("Test client: Long operation finished, heartbeat sent. Exiting.")
        sys.exit(0)
    else:
        logging.error(f"Unknown scenario: {scenario}")
        sys.exit(1)

if __name__ == "__main__":
    main()