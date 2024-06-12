import logging

from app.config import settings

LOGLEVEL = settings.LOGLEVEL
logging.basicConfig(level=LOGLEVEL, style="{")
logger = logging.getLogger("itfits_backend")
