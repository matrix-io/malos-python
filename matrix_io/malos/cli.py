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

Examples:

    # Read IMU from a locally running MALOS service
    malosclient IMU_PORT

    # Read IMU from a remotely running MALOS service
    malosclient --malos-host 192.168.0.101 IMU_PORT

"""
import asyncio
import sys
import math
from docopt import docopt

from . import __version__ as VERSION

from matrix_io.proto.malos.v1 import driver_pb2
from matrix_io.proto.malos.v1 import sense_pb2, io_pb2
from . import drivers, malosloop

""" Driver to proto message mappings """
DRIVER_PROTOS = {
    'HUMIDITY_PORT': sense_pb2.Humidity(),
    'IMU_PORT': sense_pb2.Imu(),
    'MICARRAY_ALSA_PORT': io_pb2.MicArrayParams(),
    'PRESSURE_PORT': sense_pb2.Pressure(),
    'UV_PORT': sense_pb2.UV()
}


def get_data_handler(driver):
    """ Obtains a function that prints decoded protos to STDOUT """

    async def micarray_decoder(msg):
        dt = io_pb2.MicArrayParams.FromString(msg)
        print('Azimutal angle (deg): {}'.format(dt.azimutal_angle * 180.0 / math.pi))
        print('Polar angle (deg): {}'.format(dt.polar_angle * 180.0 / math.pi))

        # Simulate some I/O operation
        await asyncio.sleep(1.0)


    def wrap(d):
        async def data_handler(msg):
            print(d.FromString(msg))

            # Simulate some I/O operation
            await asyncio.sleep(1.0)
        return data_handler

    if driver == 'MICARRAY_ALSA_PORT':
        return micarray_decoder

    return wrap(DRIVER_PROTOS[driver])


async def error_handler(msg):
    """ STDERR Error message printer """
    print(msg, file=sys.stderr)
    await asyncio.sleep(1.0)


def main():
    """CLI entrypoint """

    options = docopt(__doc__, version=VERSION)
    driver_port = None

    # Driver configuration
    driver_config = driver_pb2.DriverConfig()

    # Sanity check on driver
    try:
        driver_port = getattr(drivers, options['<driver>'])
    except AttributeError:
        print('Driver %s is not valid' % options['<driver>'], file=sys.stderr)
        exit(1)

    # Sanity checks on driver config
    try:
        update_delay = float(options['--update-delay'])
    except ValueError:
        print("Invalid --update-delay value. Try something like 1.3")
        exit(1)
    else:
        # Set the delay between updates that the driver returns
        driver_config.delay_between_updates = update_delay

    try:
        keepalive_timeout = float(options['--keepalive-timeout'])
    except ValueError:
        print("Invalid --keepalive-delay value. Try something like 8.0")
        exit(1)
    else:
        # Stop sending updates if there is no ping for 10 seconds
        driver_config.timeout_after_last_ping = keepalive_timeout

    # Init MALOS loop
    malos = malosloop.MalosLoop()
    malos.configure_driver(
        options['--malos-host'],
        driver_port,
        driver_config,
        get_data_handler(options['<driver>']),
        error_handler)

    try:
        malos.run()
    except KeyboardInterrupt:
        print('Shutting down. Bye, bye !', file=sys.stderr)
    finally:
        malos.stop()

