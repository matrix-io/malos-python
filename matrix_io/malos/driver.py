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
* Keep alive port: port for sending and receiving keep alive messages, so MALOS driver keeps reading data
  from sensors.
* Status port: port yielding MALOS status when they occur.
* Data update port: port yielding sensor data updates.

"""
import sys

import logging
import asyncio

import zmq
from matrix_io.proto.malos.v1 import driver_pb2
from typing import AsyncIterable
from zmq.asyncio import Context

IMU_PORT = 20013
HUMIDITY_PORT = 20017
EVERLOOP_PORT = 20021
PRESSURE_PORT = 20025
UV_PORT = 20029
MICARRAY_ALSA_PORT = 20037
VISION_PORT = 60001

class MalosKeepAliveTimeout(Exception):
    pass


class MalosDriver(object):
    """ Coroutine based MALOS manager """

    def __init__(self, address: str, base_port: int):
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

    def configure(self, config_proto: driver_pb2.DriverConfig) -> None:
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

        config_string = config_proto.SerializeToString()

        # Send the configuration
        sock.send(config_string)
        sock.close()
        self.logger.debug(':configure: %r bytes' % sys.getsizeof(config_string))

    async def start_keep_alive(self, delay: int = 5.0, timeout: int = 5.0) -> None:
        """
        MALOS keep-alive starter

        Connects to the corresponding keep-alive port (base_port +1) given the
        desired base_port. We send keep alive pings and receive pongs so MALOS
        keeps sampling the data from the sensors and we can keep yielding with get_data.

        Args:
            delay: delay between pings in seconds
            timeout: how long to wait for pongs before timeout in seconds

        Raises:
            MalosKeepAliveTimeout

        Yields:
            Doesn't yield anything
        """
        sock = self.ctx.socket(zmq.REQ)
        sock.connect('tcp://{0}:{1}'.format(self.address, self.base_port + 1))

        sock.setsockopt(zmq.RCVTIMEO, int(1000*timeout))

        # If the keep-alive pings stop, MALOS will stop the driver and stop
        # sending updates. Pings are useful to prevent blocked applications
        # from keeping a MALOS driver busy.
        try:
            while True:
                # An empty string is enough to let the driver know we're still
                # listening
                await sock.send_string('')
                self.logger.debug(':keep-alive: ping')

                await sock.recv_string()
                self.logger.debug(':keep-alive: pong')

                await asyncio.sleep(delay)
        except zmq.error.Again:
            raise MalosKeepAliveTimeout()
        except asyncio.CancelledError:
            self.logger.debug(':keep-alive: cancelled')
            # re-raise CancelledError
            raise
        finally:
            self.logger.debug(':keep-alive: socked closed')
            sock.close()


    async def get_status(self) -> AsyncIterable[driver_pb2.Status]:
        """
        MALOS status async generator

        Connects to the corresponding status port (base_port +2) given the desired
        base_port and yields messages.

        Yields:
            Status proto
        """
        sock = self.ctx.socket(zmq.SUB)
        sock.connect('tcp://{0}:{1}'.format(self.address, self.base_port + 2))

        # We send an empty message to let it know we're ready
        sock.setsockopt(zmq.SUBSCRIBE, b'')

        try:
            while True:
                msg = await sock.recv_multipart()
                status = driver_pb2.Status().FromString(msg[0])
                self.logger.debug(':status-port: %s' % status)
                yield status
        except asyncio.CancelledError:
            self.logger.debug(':status-port: cancelled')
            # Exit gracefully when cancelled
            return
        finally:
            self.logger.debug(':status-port: socked closed')
            sock.close()


    async def get_data(self) -> AsyncIterable[bytes]:
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

        try:
            while True:
                msg = await sock.recv_multipart()
                self.logger.debug(':data-port: %s' % msg)
                yield msg[0]
        except asyncio.CancelledError:
            self.logger.debug(':data-port: cancelled')
            # Exit gracefully when cancelled
            return
        finally:
            self.logger.debug(':data-port: socked closed')
            sock.close()

