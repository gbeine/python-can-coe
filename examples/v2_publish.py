#!/usr/bin/env python
from time import sleep

import can
from coe import CoEType, CoEVersion, Message, messagebuilder
from ipaddress import IPv4Address


def main():
    with can.Bus(
            interface="coe",
            channel=CoEVersion.V2,
            local=IPv4Address('192.168.10.10'),
            peer=IPv4Address('192.168.10.20')
    ) as bus:
        while True:
            canmsg = messagebuilder.to_can(CoEVersion.V2, [Message(50, 1, 6, CoEType.CELSIUS)])
            print(canmsg)
            bus.send(canmsg)
            sleep(1)
            canmsg = messagebuilder.to_can(CoEVersion.V2, [Message(49, 1, True)])
            print(canmsg)
            bus.send(canmsg)
            sleep(5)


if __name__ == "__main__":
    main()
