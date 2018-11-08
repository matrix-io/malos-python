"""
malosclient -- Python MALOS client

Usage:
  malosclient [options] <driver>

Options:
  -h ADDR --malos-host=ADDR   MALOS Service host [default: localhost].
  --help                      Show help screen.
  --update-delay=VAL          Delay between data updates in seconds [default: 2.0].
  --keepalive-timeout=VAL     How long to wait for a keep alive ping before stopping data updates
                              [default: 10.0] secs.
  --version                   Show version.
  --driver-config-file=PATH   Serialized driver config protobuf file to load.
  --loglevel=LEVEL            Desired loglevel output.

MALOS Drivers (base Ports):

    IMU (port 20013) Inertial Measuring Unit.
    HUMIDITY (port 20017) Humidity sensor.
    PRESSURE (port 20025) Pressure sensor.
    UV (port 20029) Ultra Violet light sensor.
    MICARRAY_ALSA (port 20037) Microphone arrays.
    VISION (port 60001) Computer Vision engine events.
    EVERLOOP (port 20021) Led everloop (write only)

Examples:

    # Read IMU from a locally running MALOS service
    malosclient IMU

    # Read IMU from a remotely running MALOS service
    malosclient --malos-host 192.168.0.101 IMU

    # Load FACE driver config from file
    malosclient --driver-config-file ~/driver_config.proto VISION

"""
import asyncio
import logging
import math
import os
import sys

from docopt import docopt
from matrix_io.proto.malos.v1 import driver_pb2
from matrix_io.proto.malos.v1 import sense_pb2, io_pb2
from matrix_io.proto.vision.v1 import vision_pb2

from matrix_io.malos import driver
""" Driver to proto message mappings """
DRIVER_PROTOS = {
    'HUMIDITY': sense_pb2.Humidity(),
    'IMU': sense_pb2.Imu(),
    'MICARRAY_ALSA': io_pb2.MicArrayParams(),
    'PRESSURE': sense_pb2.Pressure(),
    'UV': sense_pb2.UV(),
    'VISION': vision_pb2.VisionResult()
}


async def data_handler(malos_driver, driver_name):
    """
    Sample coroutine accessing the MALOS driver data generator

    Args:
        malos_driver: MALOSDriver instance
        driver_name: driver name as a string (IMU, UV, PRESSURE)

    Returns:
        None
    """
    async for data in malos_driver.get_data():
        proto_msg = DRIVER_PROTOS[driver_name].FromString(data)

        if driver_name == 'MICARRAY_ALSA':
            print('Azimuthal angle (deg): {}'.format(
                proto_msg.azimutal_angle * 180.0 / math.pi))
            print('Polar angle (deg): {}'.format(
                proto_msg.polar_angle * 180.0 / math.pi))
        else:
            print(proto_msg)


async def status_handler(malos_driver):
    """
    Sample coroutine accessing the MALOS driver error generator

    Args:
        malos_driver: MalosDriver instance

    Returns:
        None
    """

    type_mapping = {
        driver_pb2.Status.MESSAGE_TYPE_NOT_DEFINED: "Not Defined",
        driver_pb2.Status.STARTED: "Started",
        driver_pb2.Status.STOPPED: "Stopped",
        driver_pb2.Status.CONFIG_RECEIVED: "Config Received",
        driver_pb2.Status.COMMAND_EXECUTED: "Command Executed",
        driver_pb2.Status.STATUS_CRITICAL: "Critical log",
        driver_pb2.Status.STATUS_ERROR: "Error log",
        driver_pb2.Status.STATUS_WARNING: "Warning log",
        driver_pb2.Status.STATUS_INFO: "Info log",
        driver_pb2.Status.STATUS_DEBUG: "Debug log"
    }

    async for msg in malos_driver.get_status():
        """ STDERR Error message printer """

        print(type_mapping[msg.type])

        if msg.uuid:
            print("UUID: {}".format(msg.uuid))
        if msg.message:
            print("MESSAGE: {}".format(msg.message))


def main():
    """ CLI entrypoint.

    Parses command line options and initializes the MALOS driver

    Returns:
        None
    """
    options = docopt(__doc__)

    # Driver configuration
    driver_config = driver_pb2.DriverConfig()
    driver_name = options['<driver>'].upper()

    # Sanity check on driver
    try:
        driver_port = getattr(driver, '{}_PORT'.format(driver_name))
    except AttributeError:
        print(
            "Driver '%s' is not valid, try any of: IMU, HUMIDITY, PRESSURE,"
            " UV, MICARRAY_ALSA" % options['<driver>'],
            file=sys.stderr)
        sys.exit(1)

    # Sanity checks on driver config
    try:
        update_delay = float(options['--update-delay'])
    except ValueError:
        print("Invalid --update-delay value. Try something like 1.3")
        sys.exit(1)
    else:
        # Set the delay between updates that the driver returns
        driver_config.delay_between_updates = update_delay

    try:
        keepalive_timeout = float(options['--keepalive-timeout'])
    except ValueError:
        print("Invalid --keepalive-delay value. Try something like 8.0")
        sys.exit(1)
    else:
        # Stop sending updates if there is no ping for 10 seconds
        driver_config.timeout_after_last_ping = keepalive_timeout

    if options['--driver-config-file'] is not None:
        try:
            file_content = open(
                os.path.expanduser(options['--driver-config-file']),
                'rb').read()
        # @TODO (heitorgo, maciekrb) let's improve for specific exceptions here
        except Exception as err:
            print("Failed to load driver config file.", file=sys.stderr)
            sys.exit(1)
        else:
            driver_config.ParseFromString(file_content)

    # Logging configuration
    if options['--loglevel']:
        numeric_level = getattr(logging, options['--loglevel'].upper(), None)
        if not isinstance(numeric_level, int):
            logging.error('Invalid --loglevel: %s', options['--loglevel'])
            raise SystemExit(1)

        logging.basicConfig(format='%(asctime)s %(message)s', level=numeric_level)


    malos_driver = driver.MalosDriver(options['--malos-host'], driver_port)

    loop = asyncio.get_event_loop()
    
    # Schedule tasks
    loop.run_until_complete(malos_driver.configure(driver_config))
    loop.create_task(malos_driver.start_keep_alive())
    loop.create_task(data_handler(malos_driver, driver_name))
    loop.create_task(status_handler(malos_driver))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Shutting down. Bye, bye !', file=sys.stderr)
    finally:
        loop.stop()
        asyncio.gather(*asyncio.Task.all_tasks()).cancel()

        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
