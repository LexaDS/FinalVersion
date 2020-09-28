
import logging
from logging.handlers import RotatingFileHandler
from functools import wraps
from warnings import warn


###############################LoggingDecorators#####################################
class LoggingDecorator(object):

    #Base log decorator , other classes can inherit from it.
    #Class holds the __call__ implementation to be used as decorator

    def __init__(self, log_level, message, logger=None):
        self.log_level = log_level
        self.message = message
        self._logger = logger

    #method to replace the before_execution code if no log_on_start decorator is used
    def before_execution(self, fn, *args, **kwargs):
        pass

    # method to replace the after_execution code if no log_on_end decorator is used
    def after_execution(self, fn, result, *args, **kwargs):
        pass

    # method to replace the on_error code if no log_on_error decorator is used
    def on_error(self, fn, exception, *args, **kwargs):
        raise exception

    @staticmethod
    def log(logger, msg, log_level):
        logger.log(msg, log_level)


    def get_logger(self, fn):
        #logic to receive a logger instance with the module name if no logger was attributed in the __init__
        if self._logger is None:
            self._logger = logging.getLogger(fn.__module__)

        return self._logger

    def __call__(self, fn):
        #wraper function for the decorator flow
        @wraps(fn)
        def wrapper(*args, **kwargs):

            self.before_execution(fn, *args, **kwargs)

            try:
                result = fn(*args, **kwargs)
            except Exception as e:
                self.on_error(fn, e, *args, **kwargs)
            else:
                self.after_execution(fn, result, *args, **kwargs)

                return result

        return wrapper


class log_on_start(LoggingDecorator):
    #decorator used as first in the decorator sequence
    #logs name of the function with its arguments
    def before_execution(self, fn, *args, **kwargs):
        logger = self.get_logger(fn)
        #log argument list and types of wraped function
        argsList = [" {}=>{} ".format(type(ar), ar) for ar in args]
        argsList.extend([" key={}=>{} value={}=>{} ".format(type(k), k,type(kwargs[k]), kwargs[k]) for k in kwargs ])
        msg = self.message + "Called method/function {}({})".format(fn.__name__,str(argsList)[1:-1])
        self.log(logger, msg, self.log_level)


class log_on_end(LoggingDecorator):
    #decorator used as last in the decorator sequence
    #logs returned value and marks if function was successful and no unexpected exceptions were raised
    def __init__(self, log_level, message, logger=None,
                 result_format_variable="Result/Return :"):
        super(log_on_end,self).__init__(log_level, message, logger=logger)
        self.result_format_variable = result_format_variable

    def after_execution(self, fn, result, *args, **kwargs):
        logger = self.get_logger(fn)
        formatedResult = self.result_format_variable + str(result)
        #log return value and type
        msg = self.message + "Exiting method/function {} | {} type={}".format(fn.__name__,formatedResult, type(result))
        self.log(logger, msg, self.log_level)


class log_on_error(LoggingDecorator):

    def __init__(self, log_level, message, logger=None,
                 on_exceptions=None, reraise=None,
                 exception_format_variable="e"):
        super(log_on_error,self).__init__(log_level, message, logger=logger)

        self.on_exceptions = on_exceptions


        if reraise is None:
            warn("The default value of the `reraise` parameter will be changed "
                 "to `True` in the future. If you rely on catching the"
                 "exception, you should explicitly set `reraise` to `False`.",
                 category=DeprecationWarning)
            reraise = False

        self.reraise = reraise
        self.exception_format_variable = exception_format_variable


    def _log_error(self, fn, exception, *args, **kwargs):
        logger = self.get_logger(fn)
        # still needs a little bit of format on the msg side
        msg = exception

        self.log(logger, msg, self.log_level)

    def on_error(self, fn, exception, *args, **kwargs):
        try:
            raise exception
        except self.on_exceptions:
            self._log_error(fn, exception, *args, **kwargs)

            if self.reraise:
                raise


class log_exception(log_on_error):
    #logs exceptions with stack trace
    def __init__(self, log_level, message, logger=None, on_exceptions=None,
                 reraise=None, exception_format_variable="e"):
        if log_level != logging.ERROR:
            warn("`log_exception` can only log into ERROR log level")

        super(log_exception,self).__init__(log_level, message, logger=logger,
                         on_exceptions=on_exceptions, reraise=reraise,
                         exception_format_variable=exception_format_variable)

    @staticmethod
    def log(logger, msg, log_level):
        logger.exception(msg)

###############################LoggingDecorators#####################################


####################################LoggingClass#####################################
class Logger(object):

    #levels work from the selected one upwards, a level of INFO will inlcude WANR, WARNING,ERROR,FATAL,CRITICAL
    levels = {"CRITICAL" : logging.CRITICAL,
              "FATAL" : logging.FATAL,
              "ERROR" : logging.ERROR,
              "WARNING" : logging.WARNING,
              "WARN" : logging.WARN,
              "INFO" : logging.INFO,
              "DEBUG" : logging.DEBUG,
              "NOTSET" : logging.NOTSET}

    def __init__(self, level, filename, format, loggerName='',  maxBytes=0, backupCount=0):
        self.filename = filename
        self.format = format
        self.level = level
        # maxBytes and backupCount are used for log rotate
        self.maxBytes = maxBytes
        self.backupCount = backupCount
        # loggerName is used to indicate in the logfile with logger made which log
        self.loggerName = loggerName
        self.initLogger(self.maxBytes, self.backupCount, self.loggerName)

    def initLogger(self, maxBytes, backupCount, loggerName):
        """ Description:  Internal method to initialize the logger

                    Arguments: maxBytes - max bytes for a log file to have before moving to another file, 0 default does not do rotate
                               backupCount - how many files to create for logs based on maxBytes, 0 default does not do rotate
                               loggerName - name of the logger

                    Return Value: N/A  """
        self.logger = logging.getLogger(loggerName if loggerName else __name__)
        self.logger.setLevel(self.level)
        self.fileHandler = RotatingFileHandler(self.filename, maxBytes=maxBytes, backupCount=backupCount)
        self.formatter = logging.Formatter(self.format)
        self.fileHandler.setFormatter(self.formatter)
        self.logger.addHandler(self.fileHandler)


    @property
    def level(self): return self._level
    @level.setter
    def level(self, value):
        if value in Logger.levels:
            self._level = Logger.levels[value]
        else: raise Exception("level must be of type string and value must be contained in {}".format(Logger.levels))

    @property
    def filename(self): return self._filename
    @filename.setter
    def filename(self, value):
        if isinstance(value, str):
            self._filename = value
        else: raise Exception("logPath must be of type string, given type :{}".format(type(value)))

    @property
    def format(self): return self._format
    @format.setter
    def format(self, value):
        if isinstance(value, str):
            self._format = value
        else: raise Exception("format must be of type string, given type :{}".format(type(value)))

    @property
    def maxBytes(self): return self._maxBytes
    @maxBytes.setter
    def maxBytes(self, value):
        if isinstance(value, int):
            self._maxBytes = value
        else: raise Exception("maxBytes must be of type int, given type :{}".format(type(value)))

    @property
    def backupCount(self): return self._backupCount
    @backupCount.setter
    def backupCount(self, value):
        if isinstance(value, int):
            self._backupCount = value
        else: raise Exception("backupCount must be of type int, given type :{}".format(type(value)))

    @property
    def loggerName(self): return self._loggerName
    @loggerName.setter
    def loggerName(self, value):
        if isinstance(value, str):
            self._loggerName = value
        else: raise Exception("loggerName must be of type str or None, given type :{}".format(type(value)))

    def exception(self, msg):
        """ Description:  wraper method to log exception

                    Arguments: msg - message to be logger

                    Return Value: logged message  """

        self.logger.exception(msg)
        return msg

    def info(self, msg):
        """ Description:  Wraper method to log info

                    Arguments: msg - message to be logger

                    Return Value: logged message  """

        self.logger.info(msg)
        return msg

    def warning(self, msg):
        """ Description:  Wraper method to log warning

                    Arguments: msg - message to be logger

                    Return Value: logged message  """

        self.logger.warning(msg)
        return msg

    def debug(self, msg):
        """ Description:  Wraper method to log debug

                    Arguments: msg - message to be logger

                    Return Value: logged message  """

        self.logger.debug(msg)
        return msg

    def log(self,msg, level=None):
        """ Description:  Wraper method to log

                    Arguments: msg - message to be logger
                               level = level of logging

                    Return Value: logged message  """
        if level is None:
            level = Logger.levels['INFO']
        self.logger.log(level,msg)
        return msg



if __name__ == '__main__':

    mainLogger = Logger('DEBUG', "master.log", '%(asctime)s | %(name)s | %(levelname)s | %(message)s', 'LoggerExample')