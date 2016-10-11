#!/usr/bin/env python
"""
Collection of utils for the tower companion
"""
import os

class BadKarma(Exception):
    """
    What goes around comes around
    """
    pass

def which(executable):
    """
    A poor man replacement for the 'which' command
    It returns a string with the path of executable.
    It returns an empty string if executable is not found
    Also this function is not nice at all. Ask it to find something it does not
    exist and it will give you a BadKarma exception

    Args:
        executable (str): name of the executable

    Returns:
        (str): executable path

    Raises:
        BadKarma
    """
    for path in os.environ['PATH'].split(':'):
        full_path = os.path.join(path, executable)
        if os.path.isfile(full_path):
            return full_path
    msg = "{0} is not in your path. Giving up. Have a good day".format(
        executable)
    raise BadKarma(msg)
