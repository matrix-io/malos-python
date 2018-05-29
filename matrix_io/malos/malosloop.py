import asyncio

from .drivers import run_driver


class MalosLoop:
    def __init__(self):
        self.loop = asyncio.get_event_loop()
        self.drivers = []

    def configure_driver(self, address, base_port, config, data_callback, error_callback=None):
        self.drivers.append(asyncio.ensure_future(
            run_driver(self.loop, address, base_port, config, data_callback, error_callback),
            loop=self.loop))

    def run(self):
        self.loop.run_forever()

    def stop(self):
        # Cancel the all channels for each driver
        for driver in self.drivers:
            driver.cancel()

        # print raised exceptions
        for driver in self.drivers:
            try:
                if driver.done():
                    driver.result()
            except Exception as e:
                print("Unexpected exception: ", e)

        #malosclient --malos-host 10.0.2.19 IMU_PORT

        # Cancel driver children
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        # Workaround: cancel run_driver. If this line is removed,
        # run_driver pending warning will show up
        self.loop.run_until_complete(self.loop.shutdown_asyncgens())
        self.loop.close()
