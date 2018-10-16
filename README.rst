============================
MATRIXIO Python MALOS Driver
============================
A simple `Python`_ coroutine based driver for communicating with `MATRIX-MALOS services`_.

License
=======

This application follows the GNU General Public License, as described in the ``LICENSE`` file.

Installing
==========

The package is available on PyPI, so you can easily install via pip:

.. code-block:: console

    $ pip install matrix-io-malos


Running the CLI client
======================

The library includes a simple command line client to start reading data from 
your MALOS service right away. 

.. code-block:: console

    # Get the malosclient help screen
    $ malosclient --help

    # Get IMU data to STDOUT from a locally running MALOS service
    $ malosclient IMU

    # Get HUMIDITY data to STDOUT from a remotely running MALOS service
    $ malosclient -h 192.168.0.100 HUMIDITY

    # Get FACE detection data using a serialized driver config file
    $ malosclient --driver-config-file ~/driver_config.proto VISION


Using the MalosDriver
=====================

To use the MALOS driver works as an async generator so in your code 
you can do the following:

.. code-block:: python

    import asyncio
    import sys

    from matrix_io.malos.driver import IMU_PORT, UV_PORT
    from matrix_io.proto.malos.v1 import driver_pb2
    from matrix_io.proto.malos.v1 import sense_pb2

    from matrix_io.malos.driver import MalosDriver


    async def imu_data(imu_driver):
        async for msg in imu_driver.get_data():
            print(sense_pb2.Imu().FromString(msg))
            await asyncio.sleep(1.0)


    async def uv_data(uv_driver):
        async for msg in uv_driver.get_data():
            print(sense_pb2.UV().FromString(msg))
            await asyncio.sleep(1.0)


    async def status_handler(driver):

        type_mapping = {
            driver_pb2.Status.NOT_DEFINED: "Not Defined",
            driver_pb2.Status.STARTED: "Started",
            driver_pb2.Status.CONFIG_RECEIVED: "Config Received",
            driver_pb2.Status.COMMAND_EXECUTED: "Command Executed",
            driver_pb2.Status.ERROR: "Error",
            driver_pb2.Status.WARNING: "Warning"
        }

        async for msg in driver.get_status():
            print(type_mapping[msg.type])

            if msg.uuid:
                print("UUID: {}".format(msg.uuid))
            if msg.message:
                print("MESSAGE: {}".format(msg.message))

            await asyncio.sleep(1.0)


    # Driver configuration
    driver_config = driver_pb2.DriverConfig()

    # Create the drivers
    imu_driver = MalosDriver('localhost', IMU_PORT)
    uv_driver = MalosDriver('localhost', UV_PORT)
    imu_driver.configure(driver_config)
    uv_driver.configure(driver_config)

    # Create loop and initialize keep-alive
    loop = asyncio.get_event_loop()
    loop.create_task(imu_driver.start_keep_alive())
    loop.create_task(uv_driver.start_keep_alive())

    # Initialize data and error handlers
    loop.create_task(imu_data(imu_driver))
    loop.create_task(uv_data(uv_driver))
    loop.create_task(status_handler(imu_driver))
    loop.create_task(status_handler(uv_driver))

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('Shutting down. Bye, bye !', file=sys.stderr)
    finally:
        loop.stop()
        asyncio.gather(*asyncio.Task.all_tasks()).cancel()

        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()

Who can answer questions about this library?
============================================

- Heitor Silva <heitor.silva@admobilize.com>
- Maciej Ruckgaber <maciek.ruckgaber@admobilize.com>

More Documentation
==================

.. toctree::
    :titlesonly:

    CHANGELOG

.. _0MQ: http://zeromq.org/
.. _Python: https://www.python.org/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _matrixio-protos-0.0.25: https://pypi.org/project/matrix-io-proto
.. _pypi: https://pypi.org/
.. _MATRIX-MALOS services: https://matrix-io.github.io/matrix-documentation/matrix-core/getting-started/understanding-core/

