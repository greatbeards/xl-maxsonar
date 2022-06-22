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
import re

import logging

# create logger
logger = logging.getLogger("logger")
logger.setLevel(logging.DEBUG)

from dataclasses import dataclass, field

import asyncio
import serial_asyncio


class XLMaxSonar(asyncio.Protocol):
    """Basic implementation for XLMaxSonar"""

    def __init__( self , regex = r"R(\d+)\s", val_names=["distance"], extra_arg=None):
        super().__init__()
        self._callbacks = set()
        self._raw_callbacks = set()
        self._raw_data = None
        self.buffer = b''
        self.regex = regex
        self.match = None
        self.debug = None
        self.parsed_data = dict(zip(val_names, [None]*len(val_names)))
        self.val_names = val_names
        print(extra_arg)

    def get_fields(self):
        return self.val_names

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data):
        self.buffer += data

        #self.pause_reading() # required?

        if self.debug:
            print('data buffer', repr(self.buffer))

        matches = re.finditer(self.regex, self.buffer.decode('utf-8'))
        match_cnt = 0

        for matchNum, match in enumerate(matches, start=1):
            if self.debug:
                print ("Match {matchNum} was found at {start}-{end}: {match}".format(matchNum = matchNum, start = match.start(), end = match.end(), match = match.group()))

            match_cnt = matchNum
            self.match = match

        if match_cnt:
            self.buffer = b''

            match_dict = {}
            for groupNum in range(0, len(self.match.groups())):
                if(groupNum >= len(self.val_names)):
                    self.resume_reading()
                    raise Exception("To many matched values!")

                name = self.val_names[groupNum]
                match_dict[name] = self.match.group(groupNum + 1)

            self.parsed_data = match_dict
            print(match_dict)

            #send update
            self.publish_updates()
            self.publish_raw_updates()

        #self.resume_reading()



    def pause_reading(self):
        # This will stop the callbacks to data_received
        self.transport.pause_reading()

    def resume_reading(self):
        # This will start the callbacks to data_received again with all data that has been received in the meantime.
        self.transport.resume_reading()

    def get_value(self, name):
        if name in self.parsed_data:
            return self.parsed_data[name]
        raise Exception('Unknown value requested: ' + str(name))
        return None

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

    def publish_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._callbacks:
            callback()

    def publish_raw_updates(self) -> None:
        """Schedule call all registered callbacks."""
        for callback in self._raw_callbacks:
            callback()

    def register_raw_callback(self, callback: Callable[[], None]) -> None:
        """Register callback, called when a raw message was received."""
        self._raw_callbacks.add(callback)




if __name__ == "__main__":
    serial_port="/dev/tty"
    baudrate=9600
    timeout=10


    loop = asyncio.get_event_loop()
    coro = serial_asyncio.create_serial_connection(loop, XLMaxSonar, serial_port, baudrate=baudrate, )

    transport, protocol = loop.run_until_complete(coro)
    print(dir(transport))
    print(dir(protocol))
    #loop.close()


