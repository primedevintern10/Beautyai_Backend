# logging_config.py
import sys
import logging


def setup_logging():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("config/app.log", encoding="utf-8")
        ]
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
