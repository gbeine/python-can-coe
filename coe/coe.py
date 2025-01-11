"""
A CAN over Ethernet bus interface.
"""

import logging
import socket
import time

from can import BusABC, CanInitializationError, Message
from enum import IntEnum, StrEnum, unique
from ipaddress import IPv4Address
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class CoEVersion(StrEnum):
    """The CAN over Ethernet protocol version"""

    V1 = 'V1'
    V2 = 'V2'


class CoEDefaultPort(IntEnum):
    """The CAN over Ethernet default UDP port"""

    V1 = 5441
    V2 = 5442


@unique
class CoEType(IntEnum):
    """The CAN over Ethernet datatype"""

    NONE     =  0 # Not specified

    # All values from TA CMI manual, unfortunately some CMI are configured differently
    CELSIUS  =  1 # Temperature in degree Celsius
    WATTSM2  =  2 # Watts per square meter
    LITERSH  =  3 # Liters per hour
    SECONDS  =  4
    MINUTES  =  5
    LITERSP  =  6 # Liters per pulse
    KELVIN   =  7 # Temperature in degree Kelvin
    PERCENT  =  8
    KILOWATT =  9
    MWHRS    = 10 # Megawatthours
    KWHRS    = 11 # Kilowatthours
    VOLTS    = 12
    MILLIAMP = 13 # Milliampere
    HOURS    = 14
    DAYS     = 15
    PULSES   = 16
    KILOOHM  = 17
    KMH      = 18 # Kilometers per hour
    HERTZ    = 19
    LITERSM  = 20 # Liters per minute
    BAR      = 21
    ONOFF    = 43 # Binary ON/OFF (0 = OFF, 1 = ON)
    PPM      = 67 # Parts per Million
    W        = 69 # Watts


class CoE(BusABC):
    def __init__(
        self,
        channel: CoEVersion,
        local: IPv4Address,
        local_port = None,
        peer: IPv4Address = None,
        peer_port = None,
        **kwargs,
    ):
        self._local_ip = local

        if local_port is None:
            if channel == CoEVersion.V2:
                self._local_port = CoEDefaultPort.V2
            else:
                self._local_port = CoEDefaultPort.V1
        else:
            self._local_port = local_port

        self._peer_ip = peer
        self._peer_port = peer_port if peer_port is not None else self._local_port

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.bind((str(self._local_ip), self._local_port))

        self._version = channel

        self.channel_info = channel
        super().__init__(channel=channel, **kwargs)



    def _recv_internal(
        self, timeout: Optional[float]
    ) -> Tuple[Optional[Message], bool]:

        if self._version == CoEVersion.V1:
            data, addr = self._socket.recvfrom(14)
        elif self._version == CoEVersion.V2:
            data, addr = self._socket.recvfrom(36)
        else:
            raise CanInitializationError("No valid CoE version specified: %s" % self._version)

        logger.debug("Received message %s from %s"%(data.hex(), addr))

        msg = Message(
            timestamp=time.time(),
            dlc=len(data),
            data=data,
            channel="%s@%s" % (self.channel_info, addr)
        )
        return msg, False


    def send(self, msg: Message, timeout: Optional[float] = None) -> None:
        if self._peer_ip is None:
            raise CanInitializationError("No peer address specified")

        data = msg.data
        peer = (str(self._peer_ip), self._peer_port)
        logger.debug("Sending message %s to %s" % (data.hex(), peer))
        self._socket.sendto(data, peer)


    def shutdown(self) -> None:
        self._socket.shutdown(socket.SHUT_RDWR)
        super().shutdown()
