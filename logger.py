'''
This module allows logging to file and console

Author: Lukas Beck
Date: 17.04.2023
'''

import logging
import argparse

log_file_path = "plc.log"

log_formatter_file = logging.Formatter("%(asctime)s, %(levelname)s, %(module)s, %(funcName)s(%(lineno)d), %(message)s", datefmt='%H:%M:%S')
log_formatter_console = logging.Formatter("%(levelname)-8s %(module)-10s %(funcName)-20s(%(lineno)d): %(message)s", datefmt='%H:%M:%S')

# enable command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--log", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="DEBUG", help="change output of consol")
log_level: str = parser.parse_args().log

# Setup File handler, change mode tp 'a' to keep the log after relaunch
file_handler = logging.FileHandler(log_file_path, mode='w')
file_handler.setFormatter(log_formatter_file)
file_handler.setLevel(logging.DEBUG)

# Setup Stream Handler (i.e. console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter_console)
stream_handler.setLevel(getattr(logging, log_level.upper(), None))

# Get our logger
log = logging.getLogger("root")
log.setLevel(logging.DEBUG)

# Add both Handlers
log.addHandler(stream_handler)
log.addHandler(file_handler)

log.critical("PROGRAM START\n####################################################################################################")
