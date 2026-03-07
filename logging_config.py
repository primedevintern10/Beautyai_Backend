# logging_config.py
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("config/app.log")
        ]
    )
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
