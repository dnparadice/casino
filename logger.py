""" a super simple logger module """

import datetime

class Logger:
    """ A simple logger class that logs messages to the console. """

    def _prefix(self):
        """ Generate a prefix for the log message with the current time. """
        time = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]  # Get current time in HH:MM:SS.mmm format
        str = f'{time}::'
        return str

    def message(self, message: str):
        """ Log a message to the console. """
        print(f"{self._prefix()}{message}")

    def error(self, message: str):
        """ Log an error message to the console. """
        print(f"ERROR::{self._prefix()}{message}")