# Changelog
MATRIXIO Python MALOS Driver project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.1] - 2018-08.31

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
