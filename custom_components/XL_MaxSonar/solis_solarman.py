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



class SolarmanServer:
    """Basic implementation of TCP server for processing of Solis data logger"""

    def __init__( self, serial_port="/dev/ttyAMA0", baudrate=9600, timeout=10):
        self._callbacks = set()
        self._raw_callbacks = set()
        self.serial_port = serial_port
        self.baudrate = baudrate
        self.timeout = timeout  # seconds
        self._raw_data = None
        

    @property
    def client_connected(self):
        return False

    def get_fields(self):
        """Return valid sensor fields"""
        return [
            name
            for name in self.inverter_fields.keys()
            if len(self.inverter_fields[name]) == 3
        ]

    @property
    def data(self):
        """return data dictionary"""
        return self.parsed_data

    @property
    def raw_data(self):
        """Return last raw data message a bytearray"""
        return self._raw_data

    def get_value(self, name):
        """Get parced value by name"""
        if self.parsed_data and name in self.parsed_data:
            return self.parsed_data[name]

    def _get_message_length(self):
        max_pos = 0
        for name, frmt in self.inverter_fields.items():
            if len(frmt) == 0:
                continue
            val_type, start_idx, scale = frmt
            max_pos = max(max_pos, start_idx)
        return max_pos

    async def run(self):
        """run server"""
        self.server = await asyncio.start_server(self.handle_client, self.ip, self.port)

        try:
            self.new_message = False
            async with self.server:
                logger.info('start serving ...')
                await self.server.serve_forever()
        except asyncio.exceptions.CancelledError as err:
            if self.new_message:
                return self.parsed_data.items()
            raise err

    async def handle_client(self, reader, writer):
        """TCP client connection handler"""
        while True:
            try:
                msghdr  = await reader.readexactly(11)
                header = self.parse_header(msghdr )
                payload_plus_footer = await reader.readexactly(header['payload_length']+2)
            except ConnectionResetError:
                logger.warning('Connection reset')
                break
            except asyncio.exceptions.IncompleteReadError:
                logger.warning('Connection without data')
                break

            if self._is_heartbeat(header):
                logger.debug("Received heartbeat message")

            elif self._is_data_packet(header):
                raw_data = msghdr + payload_plus_footer

                self.parsed_data = self.parse_inverter_message(raw_data)
                logger.debug("Parsed message: %s" % self.parsed_data)

                self.new_message = True
                self._raw_data = raw_data

            else:
                logger.warning('Unknown packet: %s'% str(header))

            writer.write(self.mock_server_response(header, payload_plus_footer))
            self._last_seen = time.time()

            if self.new_message:
                await self.publish_updates()
            await self.publish_raw_updates()

        # In test mode: stop the server after one datagram has arrived
        if self.test_mode and self.new_message:
            self.server.close()

    def checksum_byte(self, buffer):
        """calculate checksum"""
        return reduce(lambda lrc, x: (lrc + x) & 255, buffer) & 255

    def mock_server_response(self, header, request_payload, timestamp=None):
        unix_time = int(datetime.utcnow().timestamp() if timestamp is None else timestamp)
        
        # don't know what's the meaning of these magic values
        # the first byte seems to usually echo the first byte of the request payload
        payload = pack("<BBIBBBB", request_payload[0], 0x01, unix_time, 0xaa, 0xaa, 0x00, 0x00)

        resp_type = header['type'] - 0x30
        header = pack("<BHBBBBI", 0xa5, len(payload), 0x00, resp_type, header['req_idx'], header['req_idx'], header['serialno'])
        message = header + payload
        message += pack("BB", self.checksum_byte(message[1:]), 0x15)
        return message

    def _is_heartbeat(self, header):
        """check if message is a hartbeat message"""
        return header['type'] == 0x41

    def _is_data_packet(self, header):
        """check if message is a datagram message"""
        return header['type'] == 0x42

    def parse_header(self,message):
        """Parce the first 11 bytes from message"""
        [ payload_length, type, resp_idx, req_idx, serialno ] = unpack_from("<xHxBBBI", message[0:12], 0)
        return {
            "payload_length": payload_length,
            "type": type,
            "resp_idx": resp_idx,
            "req_idx": req_idx,
            "serialno": serialno
        }

    def parse_inverter_message(self, message):
        """Parse raw data message, extract fields described in sensor_fields"""
        out_dict = {}
        for name, frmt in self.inverter_fields.items():
            if len(frmt) == 0:
                continue
            assert len(frmt) == 3

            val_type, start_idx, scale = frmt

            # message must have at least 2 bytes remaining
            if start_idx > len(message) - 2:
                logger.error("Unable to extract %s, message too short %d" % (name, len(message)))
                out_dict[name] = None
            elif val_type == "string":
                out_dict[name] = message[start_idx:scale].decode("ascii").rstrip()
            else:
                out_dict[name] = unpack_from(val_type, message, start_idx)[0] * scale

        return out_dict

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
    ser = SolarmanServer(solis_inverter_fields)

    def callback_example():
        print(ser.data)

    ser.register_callback(callback_example)
    asyncio.run(ser.run())


if __name__ == "__main__":
    main()
