import asyncio
from .drivers import run_driver


class MalosLoop:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.drivers = []

    def configure_driver(self, address, base_port, config, data_callback, error_callback=None):
        self.drivers.append(asyncio.ensure_future(
            run_driver(address, base_port, config, data_callback, error_callback),
            loop=self.loop))

    def run(self):
        self.loop.run_forever()

    def stop(self):
        # Cancel the data channel and let it complete pending tasks (ie. cancel the keep alive)
        for driver in self.drivers:
            driver.cancel()

        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()
