import unittest

from coe import messagebuilder, CoEType
from coe.message import Message

class TestMessageBuilderV1(unittest.TestCase):


    def test_from_data_invalid(self):
        failing_messages = [
            ([1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11], 'Wrong message length: 12'),
            ([1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12], 'Wrong message length: 13'),
            ([1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14, 15], 'Wrong message length: 15'),
            ([1, 10, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 14], 'Not a valid CoE V1 message'),
        ]
        for data, exception in failing_messages:
            b = bytes(data)
            with self.assertRaises(messagebuilder.InvalidMessageException) as context:
                messagebuilder.from_data_v1(b)
            self.assertEqual(exception, str(context.exception))


    def test_from_data(self):
        valid_messages = [
            (bytearray.fromhex('32  01  06 00 2a 01 d0 07 00 00 01 01 01 00'), 3),
            (bytearray.fromhex('33  01  f0 00 0a 01 00 00 00 00 01 01 03 00'), 3),
            (bytearray.fromhex('32  03  00 00 06 00 00 00 00 00 00 01 00 00'), 1),
            (bytearray.fromhex('32  03  00 00 06 00 00 00 00 00 00 01 00 00'), 1),
            (bytearray.fromhex('31  00  01 00 00 00 00 00 00 00 00 00 00 00'), 16),
            (bytearray.fromhex('30  00  08 00 00 00 00 00 00 00 00 00 00 00'), 16),
        ]
        for data, expected in valid_messages:
            msgs = messagebuilder.from_data_v1(data)
            self.assertEqual(expected, len(msgs))


    def test_parse(self):
        valid_messages = [
            (bytearray.fromhex('32 01 06 00 2a 01 d0 07 00 00 01 01 01 00'),
                ( Message(50, 1, 6, CoEType.CELSIUS),
                  Message(50, 2, 298, CoEType.CELSIUS),
                  Message(50, 3, 2000,CoEType.CELSIUS), )
             ),
            (bytearray.fromhex('33 01 f0 00 0a 01 00 00 00 00 01 01 03 00'),
                ( Message(51, 1, 240, CoEType.CELSIUS),
                  Message(51, 2, 266, CoEType.CELSIUS),
                  Message(51, 3, 0, CoEType.LITERSH), )
             ),
            (bytearray.fromhex('32 03 00 00 06 00 00 00 00 00 00 01 00 00'),
                ( Message(50, 10, 6, CoEType.CELSIUS), )
             ),
            (bytearray.fromhex('31 00 05 00 00 00 00 00 00 00 00 00 00 00'),
                ( Message(49, 1, True),
                  Message(49, 2, False),
                  Message(49, 3, True),
                  Message(49, 4, False),
                  Message(49, 5, False),
                  Message(49, 6, False),
                  Message(49, 7, False),
                  Message(49, 8, False),
                  Message(49, 9, False),
                  Message(49, 10, False),
                  Message(49, 11, False),
                  Message(49, 12, False),
                  Message(49, 13, False),
                  Message(49, 14, False),
                  Message(49, 15, False),
                  Message(49, 16, False), )
             ),
            (bytearray.fromhex('31 09 01 00 00 00 00 00 00 00 00 00 00 00'),
                ( Message(49, 17, True),
                  Message(49, 18, False),
                  Message(49, 19, False),
                  Message(49, 20, False),
                  Message(49, 21, False),
                  Message(49, 22, False),
                  Message(49, 23, False),
                  Message(49, 24, False),
                  Message(49, 25, False),
                  Message(49, 26, False),
                  Message(49, 27, False),
                  Message(49, 28, False),
                  Message(49, 29, False),
                  Message(49, 30, False),
                  Message(49, 31, False),
                  Message(49, 32, False), )
             ),
        ]
        for data, expected in valid_messages:
            msgs = messagebuilder.from_data_v1(data)
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
                 Message(50, 1, 6, CoEType.CELSIUS),
                 Message(50, 5, 6, CoEType.CELSIUS),
             ], 'Invalid address combination ([1, 5])'),
            ([
                 Message(50, 1, 6),
             ], 'Missing datatype: "CoE message: node: 50, address: 1, value: 6"'),
            ([
                 Message(50, 1, 6, None),
             ], 'Missing datatype: "CoE message: node: 50, address: 1, value: 6"'),
        ]
        for messages, exception in failing_messages:
            with self.assertRaises(messagebuilder.InvalidMessageException) as context:
                messagebuilder.to_data_v1(messages)
            self.assertEqual(exception, str(context.exception))


    def test_to_data(self):
        valid_messages = [
            (bytes.fromhex('32 01 2a 01 06 00 d0 07 00 00 01 01 01 00'),
                ( Message(50, 2, 6, CoEType.CELSIUS),
                  Message(50, 1, 298, CoEType.CELSIUS),
                  Message(50, 3, 2000,CoEType.CELSIUS), )
             ),
            (bytes.fromhex('33 01 f0 00 0a 01 00 00 00 00 01 01 03 00'),
                ( Message(51, 1, 240, CoEType.CELSIUS),
                  Message(51, 2, 266, CoEType.CELSIUS),
                  Message(51, 3, 0, CoEType.LITERSH), )
             ),
            (bytes.fromhex('32 03 00 00 06 00 00 00 00 00 00 01 00 00'),
                ( Message(50, 10, 6, CoEType.CELSIUS), )
             ),
            (bytes.fromhex('32 08 00 00 06 00 00 00 06 00 00 01 00 01'),
                ( Message(50, 30, 6, CoEType.CELSIUS),
                  Message(50, 32, 6, CoEType.CELSIUS), )
             ),
            (bytes.fromhex('31 00 05 00 00 00 00 00 00 00 00 00 00 00'),
                ( Message(49, 1, True),
                  Message(49, 3, True), )
             ),
            (bytes.fromhex('31 09 01 00 00 00 00 00 00 00 00 00 00 00'),
                ( Message(49, 17, True), )
             ),
        ]
        for expected, messages in valid_messages:
            data = messagebuilder.to_data_v1(messages)
            self.assertEqual(expected, data)


if __name__ == '__main__':
    unittest.main()
