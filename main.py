import psutil
import os
import time
import signal
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get InfluxDB credentials from environment variables
url = os.getenv("INFLUXDB_URL")
token = os.getenv("INFLUXDB_TOKEN")
org = os.getenv("INFLUXDB_ORG")
bucket = os.getenv("INFLUXDB_BUCKET")
interval = os.getenv("INTERVAL_SEC", "1")

if not all([url, token, org, bucket, interval]):
    raise ValueError(
        "Incomplete environment. Please set all variable either in the .env file or in the environment."
    )

interval = int(interval)

GRACEFUL_STOP = False


def graceful_exit(signum, frame):
    global GRACEFUL_STOP
    if GRACEFUL_STOP:
        print("Exiting immediately!")
        exit(1)
    print("Stopping gracefully...")
    GRACEFUL_STOP = True


signal.signal(signal.SIGINT, graceful_exit)


def get_hardware_temperatures():
    """
    Retrieves hardware temperatures using psutil.

    Returns:
    - dict: A dictionary where keys are hardware part names (str) and values are lists of temperatures (list of floats).
    """
    try:
        sensors = psutil.sensors_temperatures()
        temperature_data = {}
        for name, entries in sensors.items():
            temperature_data[name] = [
                entry.current for entry in entries if entry.current is not None
            ]
        return temperature_data
    except AttributeError:
        print("psutil does not support temperature sensors on this platform.")
        return {}


def push_data_to_influxdb(data):
    """
    Pushes temperature data to an InfluxDB 2.0 database.

    Parameters:
    - data (dict): A dictionary where keys are hardware part names (str)
      and values are lists of temperatures (list of floats).
    """
    # Initialize the InfluxDB client
    client = InfluxDBClient(url=url, token=token, org=org)
    write_api = client.write_api(write_options=SYNCHRONOUS)

    for part, temperatures in data.items():
        for nr, temp in enumerate(temperatures):
            # Create a point for each temperature value
            point = Point("hardware_2").tag("sensor", nr).field(part, temp)
            # Write the point to the database
            write_api.write(bucket=bucket, org=org, record=point)

    # Close the client
    client.close()


# Get hardware temperatures using psutil
rounds = 0
while True:
    rounds += 1
    data = get_hardware_temperatures()
    # Push the data to InfluxDB
    if data:
        push_data_to_influxdb(data)
    print(f"pushed run: {rounds}")
    if GRACEFUL_STOP:
        exit(0)
    time.sleep(interval)
