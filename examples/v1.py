#!/usr/bin/env python

import can
from coe import CoEVersion, messagebuilder
from ipaddress import IPv4Address


def main():
    with can.Bus(
            interface="coe",
            channel=CoEVersion.V1,
            local=IPv4Address('192.168.10.10')
    ) as bus:
        while True:
            canmsg = bus.recv()
            print(canmsg)
            for m in messagebuilder.from_can(canmsg):
                print(m)


if __name__ == "__main__":
    main()
