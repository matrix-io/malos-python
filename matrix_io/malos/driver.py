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
VISION with port 60001

Each port reserves a range of 4 ports that are used for a driver:

* Base port: (driver port) port for sending configuration proto to MALOS driver.
* Keep alive port: port for sending keep alive messages, so MALOS driver keeps reading data
  from sensors.
* Error port: port yielding MALOS errors when they occur.
* Data update port: port yielding sensor data updates.

"""

import logging
import asyncio

import zmq
from zmq.asyncio import Context

IMU_PORT = 20013
HUMIDITY_PORT = 20017
EVERLOOP_PORT = 20021
PRESSURE_PORT = 20025
UV_PORT = 20029
MICARRAY_ALSA_PORT = 20037
VISION_PORT = 60001


class MalosDriver(object):
    """ Coroutine based MALOS manager """

    def __init__(self, address, base_port):
        """
        Constructor

        Args:
            address: IP address of the device exposing the MALOS 0MQ sockets
            base_port: MALOS base port to use, see list of base ports above.
            config_proto: a driver.proto containing configuration for the driver
        """
        self.address = address
        self.base_port = base_port

        # 0MQ context
        self.ctx = Context.instance()
        self.logger = logging.getLogger(__name__)
        

        # How long to hold pending messages in memory after
        # closing a socket (in milliseconds).
        # Avoids context hanging indefinitely
        # when destroyed.
        self.ctx.setsockopt(zmq.LINGER, 3000)

    def configure(self, config_proto):
        """
        MALOS configuration

        It sends the provided configuration proto, the driver.proto, to the
        MALOS configuration port to configure the driver.

        Details about the proto structure can be found here:
        https://github.com/matrix-io/protocol-buffers/blob/master/malos/driver.proto

        Args:
            config_proto: a driver.proto containing configuration for the driver

        Returns:
            None
        """

        # Set up socket as a push
        sock = self.ctx.socket(zmq.PUSH)

        # Connect to the config port, same base port
        sock.connect('tcp://{0}:{1}'.format(self.address, self.base_port))

        # Send the configuration
        sock.send(config_proto.SerializeToString())
        sock.close()
        self.logger.debug(':configure: %s' % config_proto)

    async def start_keep_alive(self, delay=5.0):
        """
        MALOS keep-alive starter

        Connects to the corresponding keep-alive port (base_port +1) given the
        desired base_port. We send keep alive pings so MALOS keeps sampling the
        data from the sensors and we can keep yielding with get_data.

        Args:
            delay: delay between pings

        Yields:
            Doesn't yield anything
        """
        sock = self.ctx.socket(zmq.PUSH)
        sock.connect('tcp://{0}:{1}'.format(self.address, self.base_port + 1))

        # If the keep-alive pings stop, MALOS will stop the driver and stop
        # sending updates. Pings are useful to prevent blocked applications
        # from keeping a MALOS driver busy.
        while True:
            try:
                # An empty string is enough to let the driver know we're still
                # listening
                await sock.send_string('')
                self.logger.debug(':keep-alive: ping')
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                # Exit gracefully when cancelled
                self.logger.debug(':keep-alive: cancelled')
                sock.close()
                break

    async def get_error(self):
        """
        MALOS error async generator

        Connects to the corresponding error port (base_port +2) given the desired
        base_port and yields messages.

        Yields:
            Error string when a MALOS error is received
        """
        sock = self.ctx.socket(zmq.SUB)
        sock.connect('tcp://{0}:{1}'.format(self.address, self.base_port + 2))

        # We send an empty message to let it know we're ready
        sock.setsockopt(zmq.SUBSCRIBE, b'')

        while True:
            try:
                msg = await sock.recv_multipart()
                self.logger.debug(':error-port: %s' % msg)
                yield msg
            except asyncio.CancelledError:
                # Exit gracefully when cancelled
                self.logger.debug(':error-port: cancelled')
                sock.close()
                break

    async def get_data(self):
        """
        MALOS data async generator

        Connects to the corresponding data port (base_port +3) and yields
        messages received through it.

        Yields:
            Data protobuf sent by MALOS.
        """
        sock = self.ctx.socket(zmq.SUB)
        sock.connect('tcp://{0}:{1}'.format(self.address, self.base_port + 3))

        # We send an empty message to let it know we're ready
        sock.setsockopt(zmq.SUBSCRIBE, b'')

        while True:
            try:
                msg = await sock.recv_multipart()
                self.logger.debug(':data-port: %s' % msg)
                yield msg[0]
            except asyncio.CancelledError:
                self.logger.debug(':data-port: cancelled')
                sock.close()
                break
