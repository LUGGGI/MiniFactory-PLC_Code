'''This module allows logging to file and console'''

__author__ = "Lukas Beck"
__email__ = "st166506@stud.uni-stuttgart.de"
__copyright__ = "Lukas Beck"

__license__ = "GPL"
__version__ = "2023.07.12"

import logging
import argparse
from os import listdir

STD_LEVEL_CONSOLE = "WARNING"
LEVEL_FILE = logging.DEBUG

log_file_path = f"log/plc{listdir('log').__len__()+1}.log"

# enable command line arguments
parser = argparse.ArgumentParser()
parser.add_argument("--log", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default=STD_LEVEL_CONSOLE, help="change output of consol")
log_level: str = parser.parse_args().log

log_formatter_file = logging.Formatter("%(asctime)s.%(msecs)03d; %(levelname)-8s; %(name)-12s %(message)-70s; %(threadName)s; %(module)s; %(funcName)s(%(lineno)d); ", datefmt='%H:%M:%S')
log_formatter_console = logging.Formatter("%(asctime)s.%(msecs)03d %(levelname)-8s %(name)-12s %(message)-70s %(threadName)s %(module)s %(funcName)s(%(lineno)d): ", datefmt='%M:%S')

# Setup File handler, change mode tp 'a' to keep the log after relaunch
file_handler = logging.FileHandler(log_file_path, mode='a')
file_handler.setFormatter(log_formatter_file)
file_handler.setLevel(LEVEL_FILE)

# Setup Stream Handler (i.e. console)
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(log_formatter_console)
stream_handler.setLevel(getattr(logging, log_level.upper(), None))

# Get our logger
log = logging.getLogger()
log.setLevel(logging.DEBUG)

# Add both Handlers
log.addHandler(stream_handler)
log.addHandler(file_handler)

log.critical("PROGRAM START\n####################################################################################################")
