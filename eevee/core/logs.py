import sys
import logging.handlers
import logging

def init_loggers(debug):
    # d.py stuff
    dpy_logger = logging.getLogger("discord")
    dpy_logger.setLevel(logging.WARNING)
    console = logging.StreamHandler()
    console.setLevel(logging.WARNING)
    dpy_logger.addHandler(console)

    # Eevee
    eevee = logging.getLogger("eevee")

    eevee_format = logging.Formatter(
        '%(asctime)s %(levelname)s %(module)s %(funcName)s %(lineno)d: '
        '%(message)s',
        datefmt="[%d/%m/%Y %H:%M]")

    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(eevee_format)
    eevee.setLevel(logging.INFO)

    logfile_path = 'logs/eevee.log'
    fhandler = logging.handlers.RotatingFileHandler(
        filename=str(logfile_path), encoding='utf-8', mode='a',
        maxBytes=400000, backupCount=20)
    fhandler.setFormatter(eevee_format)

    logger.addHandler(fhandler)
    if debug:
        logger.addHandler(stdout_handler)

    return logger
