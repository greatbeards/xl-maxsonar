"""
Component to read XL-MaxSonar sensor by serial port connection.
"""
import asyncio
from datetime import datetime
from io import BytesIO
from functools import reduce
from struct import unpack_from, pack
import time
from typing import Callable

import logging

# create logger
logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)

from dataclasses import dataclass, field

import asyncio
import serial_asyncio


class InputChunkProtocol(asyncio.Protocol):
    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        print('data received', repr(data))

        # stop callbacks again immediately
        self.pause_reading()

    def pause_reading(self):
        # This will stop the callbacks to data_received
        self.transport.pause_reading()

    def resume_reading(self):
        # This will start the callbacks to data_received again with all data that has been received in the meantime.
        self.transport.resume_reading()




class XLMaxSonar(asyncio.Protocol):
    """Basic implementation for XLMaxSonar"""

    def __init__( self, serial_port="/dev/ttyAMA0", baudrate=9600, timeout=10):
        self._callbacks = set()
        self._raw_callbacks = set()
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout  # seconds
        self._raw_data = None
        
        self.parsed_data = None

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        print('data received', repr(data))

        # stop callbacks again immediately
        self.pause_reading()

    def pause_reading(self):
        # This will stop the callbacks to data_received
        self.transport.pause_reading()

    def resume_reading(self):
        # This will start the callbacks to data_received again with all data that has been received in the meantime.
        self.transport.resume_reading()


    @property
    def data(self):
        """return data dictionary"""
        return self.parsed_data

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when a new message was received."""
        self._callbacks.add(callback)

    def remove_callback(self, callback: Callable[[], None]) -> None:
        """Remove previously registered callback."""
        self._callbacks.discard(callback)

    async def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    async def publish_raw_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._raw_callbacks:
            callback()

    def register_raw_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when a raw message was received."""
        self._raw_callbacks.add(callback)


def main():
    async def reader():
        transport, protocol = await serial_asyncio.create_serial_connection(loop, InputChunkProtocol, '/dev/ttyUSB0', baudrate=115200)

        while True:
            await asyncio.sleep(0.3)
            protocol.resume_reading()


    loop = asyncio.get_event_loop()
    loop.run_until_complete(reader())
    loop.close()

if __name__ == "__main__":
    main()
