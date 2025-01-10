import unittest

from coe import CoEVersion, Message, messagebuilder, CoEType


class TestMessageBuilderV2(unittest.TestCase):

    def test_from_data_invalid(self):
        failing_messages = [
            ([1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 'Not a CoE V2 message: 1'),
            ([2, 1, 2, 3], 'Message too short: 4'),
            ([2, 1, 2, 3, 4, 5, 6, 7], 'Message too short: 8'),
            ([2, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 'Message too short: 11'),
            ([2, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 'Not a valid message size: 13'),
            ([2, 1, 11, 3, 4, 5, 6, 7, 8, 9, 10, 11], 'Message length does not match: 11'),
            ([2, 1, 12, 2, 4, 5, 6, 7, 8, 9, 10, 11], 'Message parts do not match: 2'),
        ]
        for data, exception in failing_messages:
            b = bytes(data)
            with self.assertRaises(messagebuilder.InvalidMessageException) as context:
                messagebuilder.from_data_v2(b)
            self.assertEqual(exception, str(context.exception))


    def test_from_data(self):
        valid_messages = [
            (bytearray.fromhex('02 00 0c 01 30 00 00 2b 01 00 00 00'), 1),
            (bytearray.fromhex('02 00 0c 01 32 09 01 01 fe ff ff ff'), 1),
            (bytearray.fromhex('02 00 1c 03 33 00 01 01 fd 00 00 00 33 01 01 01 fc 00 00 00 33 02 01 03 42 05 00 00'), 3),
            (bytearray.fromhex('02 00 24 04 31 00 00 2b 01 00 00 00 31 01 00 2b 00 00 00 00 31 02 00 2b 01 00 00 00 31 3f 00 2b 01 00 00 00 '), 4),
        ]
        for data, expected in valid_messages:
            msgs = messagebuilder.from_data_v2(data)
            self.assertEqual(expected, len(msgs))


    def test_parse(self):
        valid_messages = [
            (bytearray.fromhex('02 00 0c 01 30 00 00 2b 01 00 00 00'),
                ( Message(48, 1, True), )
             ),
            (bytearray.fromhex('02 00 0c 01 30 01 00 2b 00 00 00 00'),
                ( Message(48, 2, False), )
             ),
            (bytearray.fromhex('02 00 0c 01 30 02 00 2b 01 00 00 00'),
                ( Message(48, 3, True), )
             ),
            (bytearray.fromhex('02 00 0c 01 32 13 01 01 47 00 00 00'),
                ( Message(50, 20, 71, CoEType.CELSIUS), )
             ),
            (bytearray.fromhex('02 00 0c 01 32 01 01 01 2f 01 00 00'),
                ( Message(50, 2, 303, CoEType.CELSIUS), )
             ),
            (bytearray.fromhex('02 00 0c 01 32 02 01 01 d0 07 00 00'),
                ( Message(50, 3, 2000, CoEType.CELSIUS), )
             ),
            (bytearray.fromhex('02 00 1c 03 32 00 01 01 45 00 00 00 32 01 01 01 2f 01 00 00 32 02 01 01 d0 07 00 00'),
                ( Message(50, 1, 69, CoEType.CELSIUS),
                  Message(50, 2, 303, CoEType.CELSIUS),
                  Message(50, 3, 2000, CoEType.CELSIUS), )
             ),
            (bytearray.fromhex('02 00 0c 01 31 10 00 2b 01 00 00 00'),
                ( Message(49, 17, True), )
             ),
            (bytearray.fromhex('02 00 14 02 33 00 01 01 fc 00 00 00 33 01 01 01 fb 00 00 00'),
                ( Message(51, 1, 252, CoEType.CELSIUS),
                  Message(51, 2, 251, CoEType.CELSIUS), )
             ),
            (bytearray.fromhex('02 00 24 04 31 00 00 2b 01 00 00 00 31 01 00 2b 00 00 00 00 31 02 00 2b 01 00 00 00 31 3f 00 2b 01 00 00 00'),
                ( Message(49, 1, True),
                  Message(49, 2, False),
                  Message(49, 3, True),
                  Message(49, 64, True), )
             ),
            (bytearray.fromhex('02 00 0c 01 33 02 01 03 47 05 00 00'),
                ( Message(51, 3, 1351, CoEType.LITERSH), )
             ),
        ]
        for data, expected in valid_messages:
            msgs = messagebuilder.from_data_v2(data)
            self.assertEqual(len(expected), len(msgs))
            for i in range(0, len(expected)):
                self.assertEqual(expected[i].node, msgs[i].node)
                self.assertEqual(expected[i].address, msgs[i].address)
                self.assertEqual(expected[i].value, msgs[i].value)
                self.assertEqual(expected[i].is_digital, msgs[i].is_digital)
                self.assertEqual(expected[i].datatype, msgs[i].datatype)


    def test_to_data_invalid(self):
        failing_messages = [
            ([], 'Empty messages are not allowed'),
            ([
                 Message(50, 1, 6, CoEType.CELSIUS),
                 Message(51, 1, 6, CoEType.CELSIUS),
                 Message(52, 1, 6, CoEType.CELSIUS),
                 Message(53, 1, 6, CoEType.CELSIUS),
                 Message(54, 1, 6, CoEType.CELSIUS),
             ], 'Too many messages: 5'),
            ([
                 Message(50, 1, 6, CoEType.CELSIUS),
                 Message(51, 1, 6, CoEType.CELSIUS),
             ], 'Messages are for different nodes: 50, 51'),
            ([
                 Message(50, 1, 6, CoEType.CELSIUS),
                 Message(50, 2, True),
             ], 'Messages are mixing digital and analogue values'),
            ([
                 Message(50, 1, 6, CoEType.CELSIUS),
                 Message(50, 1, 6, CoEType.CELSIUS),
             ], 'Duplicate address: "CoE message: node: 50, address: 1, value: 6"'),
            ([
                 Message(50, 65, 6, CoEType.CELSIUS)
             ], 'Address not allowed: "CoE message: node: 50, address: 65, value: 6"'),
            ([
                 Message(50, 1, 6),
             ], 'Missing datatype: "CoE message: node: 50, address: 1, value: 6"'),
            ([
                 Message(50, 1, 6, None),
             ], 'Missing datatype: "CoE message: node: 50, address: 1, value: 6"'),
        ]
        for messages, exception in failing_messages:
            with self.assertRaises(messagebuilder.InvalidMessageException) as context:
                messagebuilder.to_data_v2(messages)
            self.assertEqual(exception, str(context.exception))


    def test_to_can_v2(self):
        valid_messages = [
            (bytes.fromhex('02 00 0c 01 30 00 00 2b 01 00 00 00'),
             (Message(48, 1, True),)
             ),
            (bytes.fromhex('02 00 0c 01 30 01 00 2b 00 00 00 00'),
             (Message(48, 2, False),)
             ),
            (bytes.fromhex('02 00 0c 01 30 02 00 2b 01 00 00 00'),
             (Message(48, 3, True),)
             ),
            (bytes.fromhex('02 00 0c 01 32 13 01 01 47 00 00 00'),
             (Message(50, 20, 71, CoEType.CELSIUS),)
             ),
            (bytes.fromhex('02 00 0c 01 32 01 01 01 2f 01 00 00'),
             (Message(50, 2, 303, CoEType.CELSIUS),)
             ),
            (bytes.fromhex('02 00 0c 01 32 02 01 01 d0 07 00 00'),
             (Message(50, 3, 2000, CoEType.CELSIUS),)
             ),
            (bytes.fromhex('02 00 1c 03 32 00 01 01 45 00 00 00 32 01 01 01 2f 01 00 00 32 02 01 01 d0 07 00 00'),
             (Message(50, 1, 69, CoEType.CELSIUS),
              Message(50, 2, 303, CoEType.CELSIUS),
              Message(50, 3, 2000, CoEType.CELSIUS),)
             ),
            (bytes.fromhex('02 00 0c 01 31 10 00 2b 01 00 00 00'),
             (Message(49, 17, True),)
             ),
            (bytes.fromhex('02 00 14 02 33 00 01 01 fc 00 00 00 33 01 01 01 fb 00 00 00'),
             (Message(51, 1, 252, CoEType.CELSIUS),
              Message(51, 2, 251, CoEType.CELSIUS),)
             ),
            (bytes.fromhex(
                '02 00 24 04 31 00 00 2b 01 00 00 00 31 01 00 2b 00 00 00 00 31 02 00 2b 01 00 00 00 31 3f 00 2b 01 00 00 00'),
             (Message(49, 1, True),
              Message(49, 2, False),
              Message(49, 3, True),
              Message(49, 64, True),)
             ),
            (bytes.fromhex('02 00 0c 01 33 02 01 03 47 05 00 00'),
             (Message(51, 3, 1351, CoEType.LITERSH),)
             ),
        ]
        for expected, messages in valid_messages:
            data = messagebuilder.to_data_v2(messages)
            self.assertEqual(expected, data)


if __name__ == '__main__':
    unittest.main()
