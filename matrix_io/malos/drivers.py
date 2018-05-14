"""
MALOS -- Hardware abstraction layer for MATRIX Creator usable via 0MQ

This is an asyncio based implementation of the MALOS drivers. It uses
coroutines to handle communications with 0MQ and provides a higher
level API for client code.

You can find more details about the MALOS protocol here:
https://github.com/matrix-io/matrix-creator-malos

List of base ports
------------------

IMU with port 20013.
Humidity with port 20017.
Everloop with port 20021.
Pressure with port 20025.
UV with port 20029.
MicArray_Alsa with port 20037.

Each port reserves a range of 4 ports that are used for a driver:

* Base port: (driver port) port for sending configuration proto to MALOS driver.
* Keep alive port: port for sending keep alive messages, so MALOS driver keeps reading data
  from sensors.
* Error port: port yielding MALOS errors when they occur.
* Data update port: port yielding sensor data updates.

"""

import asyncio
import zmq

from zmq.asyncio import Context

IMU_PORT = 20013
HUMIDITY_PORT = 20017
EVERLOOP_PORT = 20021
PRESSURE_PORT = 20025
UV_PORT = 20029
MICARRAY_ALSA_PORT = 20037


def driver_port(address, base_port, ctx, config_proto):
    """
    MALOS configuration port

    Uses the base port and accepts a configuration proto, the driver.proto
    to configure the driver.

    Details about the proto structure can be found here:
    https://github.com/matrix-io/protocol-buffers/blob/master/malos/driver.proto

    Args:
        address: IP address of the device exposing the MALOS 0MQ sockets
        base_port: desired base port as in List of base ports above (ie. 20013, 20017)
        ctx: a 0MQ context
        config_proto: a driver.proto containing configuration for the driver
    """

    # Set up socket as a push
    sock = ctx.socket(zmq.PUSH)

    # Connect to the config port, same base port
    sock.connect('tcp://{0}:{1}'.format(address, base_port))

    # Send the configuration
    sock.send(config_proto.SerializeToString())
    sock.close()


async def keep_alive_port(address, base_port, ctx, delay=5.0):
    """
    MALOS keep-alive port

    Connects to the corresponding keep-alive port (base_port +1) given the desired
    base_port. The keep alive port will run as long as the data_port is yielding
    messages from 0MQ.

    Args:
        address: IP address of the device exposing the MALOS 0MQ sockets
        base_port: desired base port as in List of base ports above (ie. 20013, 20017)
        ctx: a 0MQ context
        delay: delay between pings
    """

    # Set up socket as a push
    sock = ctx.socket(zmq.PUSH)

    # Connect to the keep alive port to the sensor port from the function args + 1
    sock.connect('tcp://{0}:{1}'.format(address, base_port + 1))

    # If the keep-alive pings stop, MALOS will stop the driver and stop sending
    # updates. Pings are useful to prevent blocked applications from keeping
    # a MALOS driver bussy.
    while True:
        try:
            # Ping with empty string to let the drive know we're still listening
            await sock.send_string('')

            # Delay between next ping
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            # Exit gracefully
            break


async def error_port(address, base_port, ctx, callback):
    """
    MALOS error port

    Connects to the corresponding error port (base_port +2) given the desired
    base_port and pushes messages to the provided callback.

    Args:
        address: IP address of the device exposing the MALOS 0MQ sockets
        base_port: desired base port as in List of base ports above (ie. 20013, 20017)
        ctx: a 0MQ context
        callback: a callback function to send received messages to
    """

    # Set up socket as a subscription
    sock= ctx.socket(zmq.SUB)

    # Connect to the base sensor port provided in the args + 2 for the error port
    sock.connect('tcp://{0}:{1}'.format(address, base_port + 2))

    # Set socket options to subscribe and send off en empty string to let it know we're ready
    sock.setsockopt(zmq.SUBSCRIBE, b'')

    while True:
        msg = await sock.recv_multipart()
        await callback(msg)


async def data_port(address, base_port, ctx, callback):
    """
    MALOS data update port

    Connects to the corresponding error port (base_port +3) given the desired
    base_port and sends messages to the provided callback.

    Args:
        addr: IP address of the device exposing the MALOS 0MQ sockets
        base_port: desired base port as in List of base ports above (ie. 20013, 20017)
        ctx: a 0MQ context
        callback: a callback function to send received messages to
    """

    # Set up socket as a subscription
    sock = ctx.socket(zmq.SUB)

    # Connect to the base sensor port provided in the args + 3 for the data port
    sock.connect('tcp://{0}:{1}'.format(address, base_port + 3))

    # Set socket options to subscribe and send off en empty string to let it know we're ready
    sock.setsockopt(zmq.SUBSCRIBE, b'')

    while True:
        msg = await sock.recv_multipart()
        await callback(msg[0])


async def run_driver(address, base_port, config_proto, data_callback, error_callback):
    context = Context()

    # Configure the MALOS driver first
    driver_port(address, base_port, context, config_proto)

    # Run the keep-alive channel
    kalive = asyncio.ensure_future(keep_alive_port(address, base_port, context))

    # Run the error channel
    error = asyncio.ensure_future(error_port(address, base_port, context, error_callback))
    try:
        # Run the data update channel
        await data_port(address, base_port, context, data_callback)
    except asyncio.CancelledError:
        kalive.cancel()
        error.cancel()
