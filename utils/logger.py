import logging
import sys

def setup_shared_logger(name, log_file="lmcontrol.log"):
  formatter = logging.Formatter(
      fmt='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
      datefmt='%d-%m-%Y %H:%M:%S'
  )

  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setFormatter(formatter)
  console_handler.setLevel(logging.INFO) 

  file_handler = logging.FileHandler(log_file)
  file_handler.setFormatter(formatter)
  file_handler.setLevel(logging.DEBUG) 

  logger = logging.getLogger(name)
  logger.setLevel(logging.DEBUG)
  
  if not logger.handlers:
      logger.addHandler(console_handler)
      logger.addHandler(file_handler)
  
  return logger

logger = setup_shared_logger("lmcontrol")