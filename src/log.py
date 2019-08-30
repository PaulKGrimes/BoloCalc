# Built-in modules
import datetime as dt
import os


class Log:
    """
    Log object writes logging information to a file and to stdout

    Args:
    log_file (str): logging file
    log_level (int): how much logging info to print to stdout.
    0 - 2, with 0 being the most info and 2 being the least

    Attributes:
    level (dict): possible logging levels -- 'CRUCIAL', 'MODERATE', 'NOTIFY'
    """
    def __init__(self, log_file):
        # Open log file
        self._log_file = log_file
        if os.path.exists(self._log_file):
            self._f = open(self._log_file, 'a+')
        else:
            self._f = open(self._log_file, 'w')
        # Error preamble
        self._err_preamble = "BoloCalc ERROR: "
        self._wrn_preamble = "BoloCalc WARNING: "

        # Announce the beginning of logging
        self._f.write(
            "\n\n***** Starting BoloCalc Program 'calcBolos.py' *****\n")
        return

    def __del__(self):
        self._f.close()
        return

    # ***** Public methods *****
    def log(self, msg):
        """
        Log a message

        Args:
        msg (str): message to log
        """
        self._write(msg)
        return

    def out(self, msg):
        """
        Log a message

        Args:
        msg (str): message to log
        """
        self._write(msg)
        print(msg),
        return

    def err(self, msg):
        """
        Report an error and raise a BoloCalc exception

        Args:
        msg (str): error message
        """
        err_msg = self._err_preamble + msg
        self._write(err_msg)
        raise Exception(err_msg)

    def wrn(self, msg):
        """
        Report a warning

        Args:
        msg (str): error message
        """
        wrn_msg = self._wrn_preamble + msg
        self._write(wrn_msg)
        print(wrn_msg),
        return

    # ***** Private methods *****
    def _write(self, msg):
        """ Write message to log file """
        self._f.write(self._dt_msg(msg))
        return

    def _dt_msg(self, msg):
        """ Append datetime to message """
        now = dt.datetime.now()
        return ("[%04d-%02d-%02d %02d:%02d:%02d] %s\n" % (
            now.year, now.month, now.day, now.hour,
            now.minute, now.second, msg))
