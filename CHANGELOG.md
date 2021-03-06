# Changelog
MATRIXIO Python MALOS Driver project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.1] - 2019-04-24
### Changed
- Updated pyzmq dependency from version 17.1.2 to 18.0.1.

## [0.4.0] - 2019-04-23
### Added
- `get_frame` asynchronous generator to handle
  video streaming from Malos.

## [0.3.2] - 2018-11-14
### Changed
- Set matrix-io-proto to be at least version 0.0.29

## [0.3.1] - 2018-11-08
### Changed
- `MalosDriver.configure` timeout now waits for the timeout asynchronously

### Added
- New Status message types to example script

## [0.3.0] - 2018-11-07
### Added
- Timeout added to `MalosDriver.configure` function

### Changed
- `MalosDriver.configure` is an async function now
- Update matrix-io-proto from 0.0.26 to 0.0.29

### Removed
- `zmq.LINGER` time reduced from 3000 ms to 0 ms on `MalosDriver` sockets

## [0.2.2] - 2018-10-17
### Changed
- Drone publish configuration.

## [0.2.1] - 2018-10-17
### Added
- Publish package to pypi on tag event.

## [0.2.0] - 2018-10-02

### Added
- `get_status` function that returns a `driver_pb2.Status` object

### Changed
- Update matrix-io-proto from 0.0.26 to 0.0.27
- `error` port became `status` port
- Keep Alive port now raises `MalosKeepAliveTimeout` if Malos doesn't respond with
pong in a certain period defined by the `timeout` parameter
- Keep Alive now raises `asyncio.CancelledError` when cancelled

### Removed
- Print whole `DriverConfig` on debug log when calling `configure`

## [0.1.1] - 2018-08-31

### Added
- Set LINGER option on `MalosDriver` zmq context to avoid hanging 
when closing application 
- Close all sockets after their task is cancelled

### Changed
- Update matrix-io-proto from 0.0.25 to 0.0.26
- Update pyzmq from 17.0.0 to 17.1.2
- `MalosDriver.configure()` is not called on initialization anymore

### Removed
- `MalosDriver.__init__()` `config_proto` parameter

## [0.1.0] - 2018-08-23
### Added
- `MalosDriver` class for encapsulation of driver functions

### Changed
- Change data and error handlers from callback style to asynchronous 
generators

### Removed
- `MalosLoop` class

## [0.0.4] - 2018-05-14
### Added
- MALOS Driver 0MQ interface functions
- MalosLoop class for starting drivers
- `malosagent` command line interface
