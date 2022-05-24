# !/usr/bin/env python3
# this is for creating dummy files to encrypt

import os
import hashlib
import argparse
import logging
import ctypes
import sys
from threading import Thread
from timeit import timeit
from queue import Queue

if sys.platform == 'win32':
    #enable virtual terminal colors (ansii escape codes)
    
    ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7)


def random(size: int) -> str:
    logging.debug("[*] generating random data", extra={"color": "\033[34m"})
    random_data = os.urandom(size)
    logging.debug("[*] hashing", extra={"color": "\033[34m"})
    return hashlib.sha1(random_data).hexdigest()


def createfile(directory, size=1024, text: bytes = None, q=Queue()) -> None:
    try:
        while 1:
            i = q.get()
            if i==0:
                q.task_done()
                break
            logging.debug(
                f"[*] Creating {i}° file", extra={"color": "\033[34m"})
            content = b"\x00"*size if not text else text
            with open(os.path.join(directory, random(size)), 'wb') as fp:
                fp.write(content)
            logging.info(f"[OK] Created file: {fp.name}", extra={
                "color": "\033[32m"})

            q.task_done()

    except Exception as e:
        logging.error(f"[ERROR] {e}", extra={"color": "\033[31m"})


def create_files(directory, size=1024, text=None, number=1) -> None:
    queue = Queue()
    for i in range(number):
        t = Thread(target=createfile, args=(directory, size, text, queue))
        t.daemon = True
        t.start()
    for i in range(number):
        queue.put(i)
    queue.join()

    logging.info(f"[OK] Created {number-1} files in {directory}", extra={
                 "color": "\033[32m"})


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--directory", type=str,
                        default=os.path.dirname(__file__), help='directory to create files in')
    parser.add_argument("-n", "--number", type=int, default=11,
                        help='number of files to create')
    parser.add_argument("-s", "--size", type=int, default=1024,
                        help='size of files to create in kb')
    parser.add_argument("-v", "--verbose", action="store_true",
                        help='activate verbose output.')
    parser.add_argument("-S", "--silent", action="store_true",
                        help='activate silent output.')
    parser.add_argument("-t", "--text", type=str, help='text to put in files')

    args = parser.parse_args()

    logging.basicConfig(format='[%(asctime)s] %(color)s%(message)s\033[0m',
                        datefmt='%H:%M:%S', level=10*(2-args.verbose+2*args.silent))

    number = args.number+1
    size = args.size<<10
    directory = os.path.abspath(args.directory)
    text = bytes(args.text, encoding='utf-8') if args.text else None
    time = timeit(lambda: create_files(
        directory, size, text, number), number=1)
    logging.info(f"Test files created in {time}s", extra={
                 "color": "\033[32m"})


if __name__ == '__main__':
    main()
