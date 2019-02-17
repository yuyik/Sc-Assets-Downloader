# -*- coding: utf-8 -*-

import os
import sys
import json
import ctypes
import socket
import argparse

import requests

from Downloader import StartDownload
from Packet.Reader import CoCMessageReader
from Packet.Writer import Write
from Packet.PreAuth import PreAuth


CLIENT_VERSION = '1.41.17'


def recvall(sock, size):
    data = []
    while size > 0:
        sock.settimeout(5.0)
        s = sock.recv(size)
        sock.settimeout(None)
        if not s:
            raise EOFError
        data.append(s)
        size -= len(s)
    return b''.join(data)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download assets from official servers')
    parser.add_argument('-s', '--specific', help='Download only files with specified extension', type=str, nargs='+', default=[])
    parser.add_argument('-d', '--decompress', help='Decompress .csv and .sc files (tex.sc included)', action='store_true')
    parser.add_argument('-o', '--overwrite', help='Overwrite already existing files', action='store_true')
    parser.add_argument('-f', '--fingerprint', help='Download fingerprint.json', action='store_true')

    args = parser.parse_args()

    if os.name == "nt":
        ctypes.windll.kernel32.SetConsoleTitleW("Starting download")
    else:
        sys.stdout.write("\x1b]2;Starting download\x07")

    s = socket.socket()
    s.connect(('game.haydaygame.com', 9339))
    s.send(Write(PreAuth))

    header = s.recv(7)
    size = int.from_bytes(header[2:5], 'big')

    print('[*] Receiving {}'.format(int.from_bytes(header[:2], 'big')))

    data = recvall(s, size)
    Reader = CoCMessageReader(data)

    if Reader.read_int() == 7:
        print('[*] FingerPrint has been received')
    else:
        print('[*] PreAuth packet is outdated , please get the latest one on GaLaXy1036 Github !')
        sys.exit()

    fingerprint = Reader.read_string()
    Reader.read_string()  # null
    Reader.read_byte()
    Reader.read_int()
    Reader.read_string()  # null
    Reader.read_byte()
    Reader.read_byte()

    Json = json.loads(fingerprint)

    print('[INFO] Version = {}, MasterHash = {}'.format(Json['version'], Json['sha']))

    r = requests.get('http://gamea.haydaygame.com:8080/env_settings?version=%s&platform=android&store=2' % CLIENT_VERSION)
    resp = r.json()
    StartDownload(resp['assetUrl'][:-1], Json, args)
