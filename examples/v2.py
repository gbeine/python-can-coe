#!/usr/bin/env python

import can
from coe import CoEVersion, messagebuilder
from ipaddress import IPv4Address


def main():
    with can.Bus(
            interface="coe",
            channel=CoEVersion.V2,
            local=IPv4Address('192.168.10.10'),
            peer=IPv4Address('192.168.10.20')
    ) as bus:
        while True:
            busmsg = bus.recv(timeout=600)
            print(busmsg)
            for m in messagebuilder.from_can(busmsg):
                print(m)


if __name__ == "__main__":
    main()
