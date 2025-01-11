import time

import can
import logging

from coe import CoEVersion, CoEType
from coe.message import Message

logger = logging.getLogger(__name__)


def from_can(msg: can.Message) -> [type[Message]]:
    if msg.channel.startswith('V1'):
        return from_data_v1(msg.data)
    elif msg.channel.startswith('V2'):
        return from_data_v2(msg.data)
    else:
        raise InvalidMessageException('Not a valid CAN over Ethernet message %s' % msg.data.hex())


def to_can(version: CoEVersion, messages: [type[Message]])  -> can.Message:
    if version == CoEVersion.V1:
        msg = _build_v1(messages)
        return can.Message(
            timestamp=time.time(),
            dlc=len(msg),
            data=msg,
            channel=version
        )
    elif version == CoEVersion.V2:
        msg = _build_v2(messages)
        return can.Message(
            timestamp=time.time(),
            dlc=len(msg),
            data=msg,
            channel=version
        )
    else:
        raise InvalidMessageException('Invalid CAN over Ethernet version %s' % version)


def from_data_v1(msg: bytes) -> [type[Message]]:
    _validate_v1(msg)
    return _parse_v1(msg)


def to_data_v1(messages: [type[Message]]) -> bytes:
    return _build_v1(messages)


def from_data_v2(msg: bytes) -> [type[Message]]:
    _validate_v2(msg)
    return _parse_v2(msg)


def to_data_v2(messages: [type[Message]]) -> bytes:
    return _build_v2(messages)


# V2 messages

def _build_v2(messages: [type[Message]]) -> bytes:
    if len(messages) < 1:
        raise InvalidMessageException('Empty messages are not allowed')

    if len(messages) > 4:
        raise InvalidMessageException('Too many messages: %i' % len(messages))

    # Set the default node and message type for the CAN message from the first message
    node = messages[0].node
    digital = messages[0].is_digital

    # Validate if all messages are compatible
    addresses = []
    for msg in messages:
        if msg.node != node:
            raise InvalidMessageException('Messages are for different nodes: %i, %i' % (node, msg.node))
        if msg.is_digital != digital:
            raise InvalidMessageException('Messages are mixing digital and analogue values')
        if msg.address > 64:
            raise InvalidMessageException('Address not allowed: "%s"' % str(msg))
        if msg.address in addresses:
            raise InvalidMessageException('Duplicate address: "%s"' % str(msg))
        if not msg.is_digital:
            if msg.datatype == CoEType.NONE or msg.datatype is None:
                raise InvalidMessageException('Missing datatype: "%s"' % str(msg))
        addresses.append(msg.address)

    data = [0] * (4 + 8 * len(messages))

    data[0] = 2
    data[2] = len(data)
    data[3] = len(messages)

    start = 4

    for i in range(0, len(messages)):
        base = start
        data[base] = messages[i].node
        data[base+1] = messages[i].address - 1
        if digital:
            data[base+2] = 0
            data[base+3] = CoEType.ONOFF
            data[base+4] = int(messages[i].value)
        else:
            data[base+2] = 1
            data[base+3] = int(messages[i].datatype)
            data[(base+4):(base+8)] = messages[i].value.to_bytes(4, byteorder='little', signed=True)
        start += 8

    return bytes(data)


def _validate_v2(data: bytes):
    if data[0] != 2:
        raise InvalidMessageException('Not a CoE V2 message: %i' % data[0])

    length = len(data)

    if length < 12:
        raise InvalidMessageException('Message too short: %i' % length)
    if (length - 4) % 8 != 0:
        raise InvalidMessageException('Not a valid message size: %i' % length)
    if data[2] != length:
        raise InvalidMessageException('Message length does not match: %i' % data[2])
    if data[3] != (length - 4) / 8:
        raise InvalidMessageException('Message parts do not match: %i' % data[3])


def _parse_v2(data) -> [type[Message]]:
    messages = []

    start = 4
    count = int(data[3])

    for i in range(0, count):
        frame = data[start:start + 8]

        node = int(frame[0])  # node are from 0..62
        address = int(frame[1]) + 1  # addresses are from 1..64
        is_digital = frame[2] == 0

        if is_digital:
            value = bool(frame[4])
            messages.append(Message(node, address, value))
        else:
            value = int.from_bytes(frame[4:8], byteorder='little', signed=True)
            messages.append(Message(node, address, value, CoEType(frame[3])))

        start += 8

    return messages


# V1 messages

def _build_v1(messages: [type[Message]]) -> bytes:
    if len(messages) < 1:
        raise InvalidMessageException('Empty messages are not allowed')

    # Set the default node and message type for the CAN message from the first message
    node = messages[0].node
    digital = messages[0].is_digital

    # Validate if all messages are compatible
    addresses = []
    min_addr = 64 # 64 is the largest address allowed
    for msg in messages:
        if msg.node != node:
            raise InvalidMessageException('Messages are for different nodes: %i, %i' % (node, msg.node))
        if msg.is_digital != digital:
            raise InvalidMessageException('Messages are mixing digital and analogue values')
        if msg.address > 64:
            raise InvalidMessageException('Address not allowed: "%s"' % str(msg))
        if msg.address in addresses:
            raise InvalidMessageException('Duplicate address: "%s"' % str(msg))
        if not msg.is_digital:
            if msg.datatype == CoEType.NONE or msg.datatype is None:
                raise InvalidMessageException('Missing datatype: "%s"' % str(msg))
        if msg.address < min_addr:
            min_addr = msg.address
        addresses.append(msg.address)

    data = [0] * 14
    data[0] = node

    if digital:
        _build_v1_digital(data, addresses, messages)
    else:
        _build_v1_analogue(data, addresses, messages)

    return bytes(data)


def _build_v1_digital(data, addresses, messages):
    # Validate if all addresses are in one address range
    # address ranges are from 1 to 16 for digital messages
    # address range 0 is 1..16, address range 9 is 17..32
    address_tuples = tuple(range(1, 17))
    address_range = 0
    if not (min(addresses) in address_tuples) and not (max(addresses) in address_tuples):
        address_tuples = tuple([16 + x for x in address_tuples])
        address_range = 9
        if not (min(addresses) in address_tuples) and not (max(addresses) in address_tuples):
            raise InvalidMessageException('Invalid address combination (%s)' % addresses)

    data[1] = address_range
    for message in messages:
        shift = (message.address - 1) % 8
        value = int(message.value)<<shift
        if (address_range == 0 and message.address < 9) or (address_range == 9 and message.address < 25):
            data[2] ^= value
        else:
            data[3] ^= value


def _build_v1_analogue(data, addresses, messages):
    # Validate if all addresses are in one address range
    # address ranges are from 1 to 4 for analogue messages
    # address range 1 is 1..4, address range 2 is 5..8, ..., address range 8 is 29..32
    address_tuples = tuple(range(1, 5))
    address_range = 0
    for i in range(1, 9):
        if (min(addresses) in address_tuples) and (max(addresses) in address_tuples):
            address_range = i
            break
        address_tuples = tuple([4 + x for x in address_tuples])

    if address_range == 0:
        raise InvalidMessageException('Invalid address combination (%s)' % addresses)

    data[1] = address_range

    for message in messages:
        position = (message.address - 1) % 4
        data[(2 + position * 2):(4 + position * 2)] = message.value.to_bytes(2, byteorder='little', signed=True)
        data[(10 + position)] = int(message.datatype)


def _validate_v1(data: bytes):
    length = len(data)

    if length != 14:
        raise InvalidMessageException('Wrong message length: %i' % length)
    if data[1] > 9:
        raise InvalidMessageException('Not a valid CoE V1 message')


def _parse_v1(data) -> [type[Message]]:
    is_digital = data[1] == 0 or data[1] == 9

    if is_digital:
        return _parse_v1_digital(data)
    else:
        return _parse_v1_analogue(data)


def _parse_v1_digital(data) -> [type[Message]]:
    messages = []

    node = int(data[0])
    base = 16 if int(data[1]) == 9 else 0

    value = data[2]
    for i in range(1, 9):
        messages.append(Message(node, base + i, bool(value & 1)))
        value >>= 1

    value = data[3]
    for i in range(9, 17):
        messages.append(Message(node, base + i, bool(value & 1)))
        value >>= 1

    return messages


def _parse_v1_analogue(data) -> [type[Message]]:
    messages = []

    node = int(data[0])
    base = (int(data[1]) - 1) * 4

    if data[10] > 0:
        address = base + 1
        value = int.from_bytes(data[2:4], byteorder='little', signed=True)
        messages.append(Message(node, address, value, CoEType(data[10])))
    if data[11] > 0:
        address = base + 2
        value = int.from_bytes(data[4:6], byteorder='little', signed=True)
        messages.append(Message(node, address, value, CoEType(data[11])))
    if data[12] > 0:
        address = base + 3
        value = int.from_bytes(data[6:8], byteorder='little', signed=True)
        messages.append(Message(node, address, value, CoEType(data[12])))
    if data[13] > 0:
        address = base + 4
        value = int.from_bytes(data[8:10], byteorder='little', signed=True)
        messages.append(Message(node, address, value, CoEType(data[13])))

    return messages


class InvalidMessageException(Exception):
    pass
