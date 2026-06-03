import sys
import traceback


RED = '\033[91m'
BOLD = '\033[1m'
ITALIC = '\033[3m'
UL = '\033[4m'
NOBOLD = '\033[22m'
NOITALIC = '\033[23m'
NOUL = '\033[24m'
NC = '\033[0m'

try:
    import argparse
    from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
    import ntpath
    from typing import Any, AnyStr, Union, Type
    from collections.abc import Generator
    from termcolor import colored, cprint
    import colorama
    # from pypager.source import StringSource, FormattedTextSource
    # from pypager.pager import Pager
    # from prompt_toolkit import ANSI
except ImportError as e:
    print(f"{RED}{UL}ERROR:{NOUL} {str(e)}{NC}", file=sys.stderr)
    print(f"{RED}{UL}STACK TRACE:{NOUL} {traceback.format_exc()}{NC}", file=sys.stderr)
    print(f"{RED}One or more required Python packages are not installed, run the install script or 'pip install -r requirements.txt'{NC}", file=sys.stderr)
    sys.exit(1)

PROGRAM_TITLE = "BRtoP"
PROGRAM_NAME = PROGRAM_TITLE.lower()
VERSION = "0.2.0"
DEFAULT_INPUT = "/dev/stdin"
DEFAULT_SEPARATOR = " "
PADDING_LEFT = 0
PADDING_RIGHT = 2
DEFAULT_PRINT_OUTPUT = False
DEFAULT_BOLD = False
DEFAULT_PLAIN_TEXT = False
DEFAULT_QUOTE_EMPTY = False
DEFAULT_HIDE_TITLE = False
COLOR_TITLE_TEXT = "light_grey"
COLOR_TITLE_BG = "on_light_grey"
COLOR_COMMAND = "light_blue"
COLOR_ARG_REQUIRED = "light_yellow"
COLOR_ARG_OPTIONAL = "green"
COLOR_ARG_POSTL_REQ = {"color": "light_yellow", "attrs": ["bold"]}
COLOR_ARG_POSTL_OPT = {"color": "light_green", "attrs": ["bold"]}
COLOR_HELP = "blue"
COLOR_DYN_HELP = "blue"
COLOR_GROUP = "cyan"
# COLOR_DESCRIPTION = "light_magenta"
COLOR_PROGRAM_TITLE = "light_blue"
COLOR_DESCRIPTION = "yellow"


class TextStyle:  # Define text styles
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    reset = '\033[0m'
    NC = reset


#######################################################
# Log functions
#######################################################
# Define a list of colors to be used for the columns.
# Available text colors:
#     black, red, green, yellow, blue, magenta, cyan, white,
#     light_grey, dark_grey, light_red, light_green, light_yellow, light_blue,
#     light_magenta, light_cyan.
#
# Available text highlights:
#     on_black, on_red, on_green, on_yellow, on_blue, on_magenta, on_cyan, on_white,
#     on_light_grey, on_dark_grey, on_light_red, on_light_green, on_light_yellow,
#     on_light_blue, on_light_magenta, on_light_cyan.
#
# Available attributes:
#     bold, dark, underline, blink, reverse, concealed.
colorama.init()
# colors = ['red', 'green', 'yellow', 'blue', 'magenta', 'cyan', 'white', 'grey', 'light_red', 'light_green']

debug = False
color_debug = "magenta"
color_error = "red"
color_warning = "yellow"
color_success = "green"
color_comment = "dark_grey"

LOG_VARS = dict()
LOG_VARS['debug'] = debug


def log(*args, **kwargs):
    print(" ".join(map(str, args)), **kwargs)


def logdbg(*args, **kwargs):
    global debug
    global color_debug
    global LOG_VARS
    label = "DEBUG"
    label_color = color_debug
    # output_debug = debug
    output_debug = LOG_VARS['debug']
    # print(colored(f"[{label}] output_debug is: '{output_debug}'", label_color))
    if output_debug:
        print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logerr(*args, **kwargs):
    global color_error
    label = "ERROR"
    label_color = color_error
    print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


def logwarn(*args, **kwargs):
    global color_warning
    label = "WARNING"
    label_color = color_warning
    print(colored(f"[{label}]", label_color), " ".join(map(str, args)), **kwargs, file=sys.stderr)


logdebug = logdbg
logerror = logerr
logwarning = logwarn

Log = {
    "l": log,
    "e": logerr,
    "w": logwarn,
    "d": logdbg,
}


def exit_error(code: int):
    # Add custom error logging or messages here
    sys.exit(code)

