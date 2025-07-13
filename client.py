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
            with open(HEARTBEBEAT_FILE, "w") as f:
                f.write(str(time.time()))
            logging.info("Heartbeat sent")
        except IOError as e:
            logging.error(f"Error writing to heartbeat file {HEARTBEAT_FILE}: {e}")
        time.sleep(5)

if __name__ == "__main__":
    main()