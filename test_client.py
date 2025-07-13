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