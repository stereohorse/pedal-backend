#!/usr/bin/env python

import sys
import argparse
import subprocess as sp
import hid


PEDAL_VENDOR_ID = 0x062A
PEDAL_PRODUCT_ID = 0x4101


def is_pedal(device):
    return (device['vid'] == PEDAL_VENDOR_ID
            and device['pid'] == PEDAL_PRODUCT_ID)


def get_pedals():
    devices = [{'vid': device['vendor_id'],
                'pid': device['product_id'],
                'path': device['path'],
                'description': device['product_string']}
               for device in hid.enumerate()]

    pedals = filter(is_pedal, devices)
    return set([pedal['path'] for pedal in pedals])


def handle_pushes(cmd):
    # underlying C API somethimes throws exceptions
    # dirty patched with retries
    OPEN_TRIES_N = 10

    for i in range(OPEN_TRIES_N):
        try:
            pedal = hid.device()
            pedal.open(PEDAL_VENDOR_ID, PEDAL_PRODUCT_ID)
            break
        except IOError:
            pass
    else:
        print 'Unable to open pedal'
        sys.exit(-1)

    pedal.set_nonblocking(1)

    try:
        BUFFER_SIZE_BYTES = 100
        CLICK_SIGNAL_VAL = 4
        READ_TIMEOUT_MS = 1000

        while 1:
            msg = pedal.read(BUFFER_SIZE_BYTES, READ_TIMEOUT_MS)
            if len(msg) > 2 and msg[1] == CLICK_SIGNAL_VAL:
                sp.call(cmd.split(' '))
    finally:
        pedal.close()


def get_args():
    parser = argparse.ArgumentParser(description='Pedal backend',
                                     epilog='Push for glory!')
    parser.add_argument('cmd', help='command to execute on push event')

    return parser.parse_args()


def main():
    handler_cmd = get_args().cmd
    pedals = get_pedals()

    if not pedals:
        print 'Pedal not found! Yuk'
        sys.exit(-1)

    if len(pedals) > 1:
        print 'Multiple devices found! Ugh.'
        print pedals
        sys.exit(-1)

    handle_pushes(handler_cmd)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print ''
        print 'Keep on rotting in the free world!'
