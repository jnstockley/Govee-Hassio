"""Govee Integration for H5179 and H7102 devices"""

import logging.handlers
import sys

formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
log = logging.getLogger(__name__)
handler = logging.handlers.RotatingFileHandler(
              'app.log', maxBytes=200000000, backupCount=5)
handler.setFormatter(formatter)
log.addHandler(handler)
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setFormatter(formatter)
log.addHandler(stdout_handler)
log.setLevel(logging.DEBUG)
