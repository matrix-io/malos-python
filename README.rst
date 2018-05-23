MATRIXIO MALOS Libs
===================
`Python`_ tiny set of libraries for communicating with `MATRIX-MALOS`_ services.

Installing
----------

This package is available on `pypi`_ so you can:

::

 pip install matrix-io-malos


Testing
---------

Install `coverage`, `pytest` and `pytest-cov`:

::

    pip install coverage pytest pytest-cov

Run:

::

    python setup.py test

Running the CLI client
----------------------

The library includes a simple command line client to start reading data from 
your MALOS service right away. 

::

    # Get the malosclient help screen
    malosclient --help

    # Get IMU data to STDOUT from a locally running MALOS service
    malosclient IMU_PORT

    # Get HUMIDITY data to STDOUT from a remotely running MALOS service
    malosclient -h 192.168.0.100 HUMIDITY_PORT


Using the MalosLoop
-------------------

To use the MALOS loop in your code do the following:

::

    import asyncio
    import sys

    from matrix_io.malos import malosloop
    from matrix_io.malos.drivers import IMU_PORT, UV_PORT

    from matrix_io.proto.malos.v1 import driver_pb2
    from matrix_io.proto.malos.v1 import sense_pb2, io_pb2

    async def imu_data(msg):
       print(sense_pb2.Imu().FromString(msg)
       await asyncio.sleep(1.0)

    async def uv_data(msg):
       print(sense_pb2.UV().FromString(msg)
       await asyncio.sleep(1.0)

    async def error_handler(msg)
       print('Error: %s' % msg, file=sys.stderr)
       await asyncio.sleep(1.0)

    # Driver configuration
    driver_config = driver_pb2.DriverConfig()

    # Initialize the MalosLoop and the desired drivers
    malos = malosloop.MalosLoop()
    malos.configure_driver('localhost', IMU_PORT, driver_config, imu_data, error_handler)
    malos.configure_driver('localhost', UV_PORT, driver_config, uv_data, error_handler)

    try:
        malos.run()
    except KeyboardInterrupt:
        print('Shutting down. Bye, bye !', file=sys.stderr)
    finally:
        malos.stop()



.. _0MQ: http://zeromq.org/
.. _Python: https://www.python.org/
.. _virtualenv: https://virtualenv.pypa.io/en/stable/
.. _matrixio-protos-0.0.17: https://bitbucket.org/admobilize/vision-agent/downloads/matrix_io-proto-0.0.17.tar.gz
.. _MATRIX-MALOS: https://github.com/matrix-io/matrix-creator-malos
.. _pypi: https://pypi.org/project/matrix-io-malos/

