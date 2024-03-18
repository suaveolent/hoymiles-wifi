"""Init file for hoymiles_wifi package."""

import logging
import os

LOGLEVEL = os.environ.get("LOGLEVEL", "INFO").upper()
logging.basicConfig(level=LOGLEVEL)

logger = logging.getLogger(__name__)
