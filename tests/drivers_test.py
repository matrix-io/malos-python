import asyncio
import unittest
from unittest.mock import ANY

import zmq
from unittest import mock
from zmq.asyncio import Context

from matrix_io.malos.drivers import driver_port, keep_alive_port, error_port, run_driver, data_port
from .asyncio_test_helper import _run, AsyncMock, async_print
from matrix_io.proto.malos.v1 import driver_pb2

# Driver configuration
driver_config = driver_pb2.DriverConfig()

class DriverTest (unittest.TestCase):
    
    host = "localhost"
    port = 0

    @mock.patch('zmq.asyncio.Socket.connect')
    def test_driver_port_connect(self, connect):
        driver_port(self.host, self.port, Context(), driver_config)
        assert connect.called
        connect.assert_called_with('tcp://{0}:{1}'.format(self.host, self.port))


    @mock.patch('zmq.asyncio.Socket.send')
    def test_driver_port_send(self, send):
        driver_port(self.host, self.port, Context(), driver_config)
        assert send.called
        send.assert_called_with(driver_config.SerializeToString())

    @mock.patch('zmq.asyncio.Socket.close')
    def test_driver_port_close(self, close):
        driver_port(self.host, self.port, Context(), driver_config)
        assert close.called

    @mock.patch('zmq.asyncio.Socket.connect')
    @mock.patch('zmq.asyncio.Socket.send_string', new=AsyncMock(side_effect=asyncio.CancelledError()))
    def test_keep_alive_port(self, connect):
        from zmq.asyncio import Socket
        try:
            _run(keep_alive_port(self.host, self.port, Context()))
            connect.assert_called_with('tcp://{0}:{1}'.format(self.host, self.port+1))
            assert Socket.send_string.mock.called
        except asyncio.CancelledError:
            self.fail("keep_alive_port shouldn't raise exception")

    @mock.patch('zmq.asyncio.Socket.setsockopt')
    @mock.patch('zmq.asyncio.Socket.connect')
    @mock.patch('zmq.asyncio.Socket.recv_multipart', new=AsyncMock(side_effect=Exception()))
    def test_error_port(self, connect, setsockopt):
        from zmq.asyncio import Socket

        try:
            _run(error_port(self.host, self.port, Context(), async_print))
            self.fail("error_port should have raised exception")
        except Exception:
            connect.assert_called_with('tcp://{0}:{1}'.format(self.host, self.port + 2))
            setsockopt.assert_called_with(zmq.SUBSCRIBE, b'')
            assert Socket.recv_multipart.mock.called

    @mock.patch('zmq.asyncio.Socket.setsockopt')
    @mock.patch('zmq.asyncio.Socket.connect')
    @mock.patch('zmq.asyncio.Socket.recv_multipart', new=AsyncMock(side_effect=Exception()))
    def test_data_port(self, connect, setsockopt):
        from zmq.asyncio import Socket

        try:
            _run(data_port(self.host, self.port, Context(), async_print))
            self.fail("data_port should have raised exception")
        except Exception:
            connect.assert_called_with('tcp://{0}:{1}'.format(self.host, self.port + 3))
            setsockopt.assert_called_with(zmq.SUBSCRIBE, b'')
            assert Socket.recv_multipart.mock.called

    @mock.patch('matrix_io.malos.drivers.driver_port')
    @mock.patch('zmq.asyncio.Socket.recv_multipart', new=AsyncMock(side_effect=Exception()))
    @mock.patch('matrix_io.malos.drivers.keep_alive_port', new=AsyncMock())
    @mock.patch('matrix_io.malos.drivers.error_port', new=AsyncMock())
    @mock.patch('matrix_io.malos.drivers.data_port', new=AsyncMock())
    def test_run_driver(self, driver_port):
        from matrix_io.malos.drivers import keep_alive_port
        from matrix_io.malos.drivers import error_port
        from matrix_io.malos.drivers import data_port
        try:
            _run(run_driver(self.host, self.port, driver_config, async_print, async_print))
            self.fail("run_driver should have raised exception")
        except Exception:
            driver_port.assert_called_with(self.host, self.port, ANY, driver_config)
            keep_alive_port.mock.assert_called_once_with(self.host, self.port, ANY)
            error_port.mock.assert_called_once_with(self.host, self.port, ANY, ANY)
            data_port.mock.assert_called_once_with(self.host, self.port, ANY, ANY)

