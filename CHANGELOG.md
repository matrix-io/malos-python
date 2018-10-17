# Changelog
MATRIXIO Python MALOS Driver project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
