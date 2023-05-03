'''
This module allows logging to file and console

Author: Lukas Beck
Date: 17.04.2023
'''

import logging
import argparse

STD_LEVEL_CONSOLE = "INFO"

LEVEL_FILE = logging.INFO
log_file_path = "plc.log"

log_formatter_file = logging.Formatter("%(asctime)s, %(levelname)-8s, %(threadName)-20s, %(module)-10s, %(funcName)-25s(%(lineno)3d), %(message)s")
log_formatter_console = logging.Formatter("%(levelname)-8s %(threadName)-20s %(module)-10s %(funcName)-25s(%(lineno)3d): %(message)s")

# enable command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--log", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=STD_LEVEL_CONSOLE, help="change output of consol")
log_level: str = parser.parse_args().log

# Setup File handler, change mode tp 'a' to keep the log after relaunch
file_handler = logging.FileHandler(log_file_path, mode='w')
file_handler.setFormatter(log_formatter_file)
file_handler.setLevel(LEVEL_FILE)

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
