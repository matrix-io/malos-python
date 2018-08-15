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

Examples:

    # Read IMU from a locally running MALOS service
    malosclient IMU_PORT

    # Read IMU from a remotely running MALOS service
    malosclient --malos-host 192.168.0.101 IMU_PORT

    # Load FACE driver config from file
    malosclient --driver-config-file ~/driver_config.proto FACE_PORT

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

from . import __version__ as VERSION
from . import driver

""" Driver to proto message mappings """
DRIVER_PROTOS = {
    'HUMIDITY_PORT': sense_pb2.Humidity(),
    'IMU_PORT': sense_pb2.Imu(),
    'MICARRAY_ALSA_PORT': io_pb2.MicArrayParams(),
    'PRESSURE_PORT': sense_pb2.Pressure(),
    'UV_PORT': sense_pb2.UV(),
    'FACE_PORT': vision_pb2.VisionResult()
}


async def data_handler(malos_driver, driver_name):
    async for data in malos_driver.get_data():
        proto_msg = DRIVER_PROTOS[driver_name].FromString(data)

        if driver_name == 'MICARRAY_ALSA_PORT':
            print('Azimutal angle (deg): {}'.format(proto_msg.azimutal_angle * 180.0 / math.pi))
            print('Polar angle (deg): {}'.format(proto_msg.polar_angle * 180.0 / math.pi))
        else:
            print(proto_msg)

        await asyncio.sleep(0.5)


async def error_handler(malos_driver):
    async for msg in malos_driver.get_error():
        """ STDERR Error message printer """
        print(msg, file=sys.stderr)
        await asyncio.sleep(0.5)


def main():
    """CLI entrypoint """
    logging.basicConfig(level=logging.DEBUG)

    options = docopt(__doc__, version=VERSION)
    driver_port = None

    # Driver configuration
    driver_config = driver_pb2.DriverConfig()

    # Sanity check on driver
    try:
        driver_port = getattr(driver, options['<driver>'])
    except AttributeError:
        print('Driver %s is not valid' % options['<driver>'], file=sys.stderr)
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
            file_content = open(os.path.expanduser(options['--driver-config-file']), 'rb').read()
        except Exception as err:
            print("Failed to load driver config file.", file=sys.stderr)
            sys.exit(1)
        else:
            driver_config.ParseFromString(file_content)

    malos_driver = driver.MalosDriver(
        options['--malos-host'],
        driver_port,
        driver_config)

    loop = asyncio.get_event_loop()

    # Schedule tasks
    loop.create_task(malos_driver.start_keep_alive())
    loop.create_task(data_handler(malos_driver, options['<driver>']))
    loop.create_task(error_handler(malos_driver))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Shutting down. Bye, bye !', file=sys.stderr)
    finally:
        loop.stop()
        asyncio.gather(*asyncio.Task.all_tasks()).cancel()

        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
