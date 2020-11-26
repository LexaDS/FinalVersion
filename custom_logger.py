import inspect
import logging

def customLogger(logLevel=logging.DEBUG):
    loggername=inspect.stack()[1][3]
    logger=logging.getLogger(loggername)
    logger.setLevel(logging.DEBUG)
    filehandler=logging.FileHandler("Docker_automation.log".format(loggername),mode="a")
    filehandler.setLevel(logLevel)
    formatter=logging.Formatter("%(asctime)s-%(name)s-%(levelname)s:%(message)s",datefmt="%m/%d/%Y %I:%M:%S %p")
    filehandler.setFormatter(formatter)
    logger.addHandler(filehandler)

    return logger