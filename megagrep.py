# Megagrep
# Locate critical areas and keywords in a code
#
# Lex @ https://github.com/claire-lex/megagrep - 2021
#
# pylint: disable=invalid-name

"""
usage: megagrep.py [-h] [-v] [-s] [-A] [-K] [-S] [-C] [-i files)] [-x file(s)]
                   [-w word(s)] [-d file(s)] [-l list(s] [-c] [-f filename]
                   [path]

Megagrep helps beginning a code review by looking at keywords using "grep".
This is not a static analysis tool, it just searches for places in the code
that require to be investigated manually.

positional arguments:
  path                  Path to files to (mega)grep.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose mode.
  -s, --sensitive       Enable case-sensitive mode (default is case
                        insensitive).
  -K, --keyword         Search by keywords from a dictionary file (default
                        mode).
  -S, --stat            Give only statistics about the code (rely on other
                        modes).
  -C, --comment         Search comments in the code.
  -i file(s), --include file(s)
                        Files to include in search (ex: *.java).
  -x file(s), --exclude file(s)
                        Files to exclude from search (ex: *.min.js).
  -w word(s), --word word(s)
                        Search for specific word(s).
  -d file(s), --dict file(s)
                        Use other dictionary file(s).
  -l list(s), --list list(s)
                        Use specific list from dictionary file(s).
  -c, --csv             Output in CSV format (default is colored ASCII).
  -f filename, --file filename
                        Output to file.
"""

from os import access, R_OK, getcwd, walk
from os.path import sep, dirname, join, realpath, exists, isfile, basename
from textwrap import fill
from argparse import ArgumentParser
from importlib.util import find_spec
from re import finditer, IGNORECASE, compile as re_compile, search as re_search

###############################################################################
# CONFIGURATION                                                               #
###############################################################################

DEFAULT_DICTIONARY = join("dicts", "global.mg")
DEFAULT_EXCLUDE = ("*.min.js,*.css")
COMMENT_TAG = "#"
CSV_TAG = ","
LIST_REGEX = re_compile(r"^\[([\w\-\_\+]*)\]$")

###############################################################################
# GLOBAL FUNCTIONS                                                            #
###############################################################################

#-----------------------------------------------------------------------------#
# Terminal and text utilities                                                 #
#-----------------------------------------------------------------------------#

#--- Text color and ASCII art printing ---------------------------------------#

IS_TERMCOLOR = True if find_spec("termcolor") else False
IS_PYFIGLET = True if find_spec("pyfiglet") else False

if IS_PYFIGLET:
    from pyfiglet import figlet_format
else:
    WARNING("Megagrep requires \"pyfiglet\" to print beautiful text. " \
            "(pip install pyfiglet)")
if IS_TERMCOLOR:
    from termcolor import colored
else:
    WARNING("Megagrep requires \"termcolor\" to color the output. " \
            "(pip install termcolor)")

#--- Messages ----------------------------------------------------------------#

def VERBOSE(message: str) -> None:
    """Prints additional information to stdout if ``verbose`` option is set."""
    if not OPTIONS.verbose:
        return
    if IS_TERMCOLOR:
        print(colored(fill("[INFO]    {0}".format(message), width=80), "cyan"))
    else:
        print(fill("[INFO]    {0}".format(message), width=80))

def WARNING(message: str) -> None:
    """Prints warning messages (non-blocking errors) to stdout."""
    if IS_TERMCOLOR:
        print(colored(fill("[WARNING] {0}".format(message), width=80), "red"))
    else:
        print(fill("[WARNING] {0}".format(message), width=80))

def ERROR(message: str) -> None:
    """Prints error messages to stdout and exits."""
    if IS_TERMCOLOR:
        print(colored(fill("[ERROR]   {0}".format(message), width=80), "red",
                      attrs=["bold"]))
    else:
        print(fill("[ERROR]   {0}".format(message), width=80))
    exit(-1)

#-----------------------------------------------------------------------------#
# File management                                                             #
#-----------------------------------------------------------------------------#

def REALPATH(filename: str) -> str:
    """Returns the absolute path of a file using ``os.path`` library.

    If we only have the filename, the absolute path points to megagrep's source
    directory instead of current working directory.
    """
    if not filename:
        return None
    if sep not in filename:
        filename = join(dirname(realpath(__file__)), filename)
    return realpath(filename)

def CHECKFILE(filename: str, force_file=False) -> bool:
    """Check if source file exists. Returns True or False"""
    fullarg = realpath(filename)
    if not exists(fullarg) or not access(fullarg, R_OK):
        return False
    if force_file and not isfile(fullarg):
        return False
    return True

###############################################################################
# OPTIONS                                                                     #
###############################################################################

#-----------------------------------------------------------------------------#
# Constants                                                                   #
#-----------------------------------------------------------------------------#

# Default values
D_VERBOSE = False
D_SENSITIVE = False
D_KEYWORD = True
D_STAT = False
D_COMMENT = False
D_STRINGS = False
D_INCLUDE = None
D_EXCLUDE = DEFAULT_EXCLUDE
D_WORD = None
D_DICT = None
D_LIST = None
D_CSV = False
D_FILE = None

# Help messages
H_MEGAGREP = "Megagrep helps beginning a code review by looking at keywords \
using \"grep\". This is not a static analysis tool, it just searches for \
places in the code that require to be investigated manually."
H_VERBOSE = "Verbose mode."
H_SENSITIVE = "Enable case-sensitive mode (default is case insensitive)."
H_KEYWORD = "Search by keywords from a dictionary file (default mode)."
H_STAT = "Give only statistics about the code (rely on other modes)."
H_COMMENT = "Search comments in the code."
H_STRINGS = "Search strings in the code."
H_INCLUDE = "Files to include in search (ex: *.java)."
H_EXCLUDE = "Files to exclude from search (ex: *.min.js)."
H_WORD = "Search for specific word(s)."
H_DICT = "Use other dictionary file(s)."
H_LIST = "Use specific list from dictionary file(s)."
H_CSV = "Output in CSV format (default is colored ASCII)."
H_FILE = "Output to file."

# Meta text
M_FILE = "file(s)"
M_WORD = "word(s)"
M_LIST = "list(s)"
M_NAME = "filename"

# Options dictionary
SOPT = 0 # Short option
LOPT = 1 # Long option
HOPT = 2 # Help
DOPT = 3 # Default value
MOPT = 4 # Meta
OPTS_DICT = (
    # Behavior
    ("-v", "--verbose", H_VERBOSE, D_VERBOSE, None),
    ("-s", "--sensitive", H_SENSITIVE, D_SENSITIVE, None),
    # Mode
    ("-K", "--keyword", H_KEYWORD, D_KEYWORD, None),
    ("-S", "--stat", H_STAT, D_STAT, None),
    ("-C", "--comment", H_COMMENT, D_COMMENT, None),
    ("-T", "--strings", H_STRINGS, D_STRINGS, None),
    # Input
    ("-i", "--include", H_INCLUDE, D_INCLUDE, M_FILE),
    ("-x", "--exclude", H_EXCLUDE, D_EXCLUDE, M_FILE),
    # Parsing
    ("-w", "--word", H_WORD, D_WORD, M_WORD),
    ("-d", "--dict", H_DICT, D_DICT, M_FILE),
    ("-l", "--list", H_LIST, D_LIST, M_LIST),
    # Output
    ("-c", "--csv", H_CSV, D_CSV, None),
    ("-f", "--file", H_FILE, D_FILE, M_NAME)
)

#-----------------------------------------------------------------------------#
# Initialize options                                                          #
#-----------------------------------------------------------------------------#

def init_options() -> object:
    """Set options using ``ArgumentParser``."""
    args = ArgumentParser(description=H_MEGAGREP)
    # Store PATH argument
    args.add_argument("path", nargs="?", help="Path to files to (mega)grep.")
    # Store all other options
    for opt in OPTS_DICT:
        if not opt[MOPT]: # Option takes no argument (no meta)
            args.add_argument(opt[SOPT], opt[LOPT], help=opt[HOPT],
                              action='store_true', default=opt[DOPT])
        else:
            args.add_argument(opt[SOPT], opt[LOPT], help=opt[HOPT],
                              metavar=opt[MOPT], default=opt[DOPT])
    return args.parse_args()

###############################################################################
# DICTIONARY                                                                  #
###############################################################################

def parse_dict(dictfile: str, categories: list=None) -> list:
    """Extract keywords from a dictionary file.
    If option ``list`` is set, will only extract keywords from specified list.

    A dictionary file has the following format::

      # This is a comment
      # Keyword 1 and 2 below do not match any category

      keyword 1
      keyword 2

      [category1]
      keyword3
      KeyWord4 # Case matters only when --sensitive is set
    """
    keywords = []
    dictfile = realpath(dictfile)
    current = None
    if not CHECKFILE(dictfile, force_file=True):
        WARNING("File {0} cannot be opened.".format(dictfile))
        return []
    VERBOSE("Adding dictionary: {0}".format(dictfile))
    with open(dictfile, "r") as fd:
        for line in fd:
            line = line.split(COMMENT_TAG)[0].strip()
            if not len(line):
                continue
            category_match = LIST_REGEX.match(line)
            if category_match:
                current = category_match.group(1).lower()
            elif not categories or current in categories:
                keywords += [line]
    return keywords

def init_keywords() -> dict:
    """Initialize keywords to look for, extracted from files and arguments.

    Associated options::

      --word=test OR --word=test1,test2
      --dict=my_dictionary

    Using the option ``word`` alone replace the default dictionary with words.
    Using the option ``dict`` alone replace the default dictionary with dict.
    Using both ``word`` and ``dict`` combines both.
    """
    if OPTIONS.sensitive:
        REGEX = lambda x: re_compile(x.replace(".", r"\.").replace("*", ".*"))
    else:
        REGEX = lambda x: re_compile(x.replace(".", r"\.").replace("*", ".*"),
                                     IGNORECASE)
    keywords = []
    k_regex = [] # keywords compiled regex
    categories = []
    # OPTION LIST
    if OPTIONS.list:
        categories += OPTIONS.list.split(",")
        VERBOSE("Using keywords from lists: {0}".format(", ".join(categories)))
    # OPTION WORD
    if OPTIONS.word:
        keywords += OPTIONS.word.split(",")
        k_regex += [REGEX(x) for x in keywords]
    # OPTION DICT
    if OPTIONS.dict:
        dictionaries = OPTIONS.dict.split(",")
        for dictfile in dictionaries:
            keywords += parse_dict(dictfile, categories)
            k_regex += [REGEX(x) for x in keywords]
    # DEFAULT DICTIONARY
    if not keywords:
        keywords += parse_dict(REALPATH(DEFAULT_DICTIONARY), categories)
        k_regex += [REGEX(x) for x in keywords]
    return keywords, k_regex

###############################################################################
# FILE PARSING                                                                #
###############################################################################

def init_path() -> list:
    """Set path to start the scan from.
    If no path specified, start from current working directory.

    Megagrep is recursive, if you choose a directory, everything inside
    (except the exclude list) will be scanned.
    """
    if not OPTIONS.path:
        return getcwd()
    path = realpath(OPTIONS.path)
    if not CHECKFILE(path):
        ERROR("File {0} cannot be opened.".format(path))
    return path

def init_include_exclude() -> (list, list):
    """Set the list of files or pattern to include and exclude.

    Relies on option ``--include`` and ``--exclude``.

    Include goes first: if both include and exclude patterns are specified,
    the exclude list will apply to the included one. Example::

      megagrep -i *.js -x *.min.js # Includes only .js files but no .min.js
      megagrep -x toto.py -i *.py # Includes all .py file except toto.py
      megagrep -x *.java -i *.java # Empty: included content is excluded
    """
    REGEX = lambda x: re_compile("^"+x.replace(".", r"\.").replace("*", ".*")+"$")
    include = [REGEX(x) for x in OPTIONS.include.split(",")] if OPTIONS.include else []
    exclude = [REGEX(x) for x in OPTIONS.exclude.split(",")] if OPTIONS.exclude else []
    return include, exclude

###############################################################################
# SEARCH                                                                      #
###############################################################################

#-----------------------------------------------------------------------------#
# Result object                                                               #
#-----------------------------------------------------------------------------#

class Result(object):
    """Object containing all the information associated to one line of results.

    This class also provides methods for reading and formatting results output.

    :param line_no: Line number associated to the result as an int
    :param line: Full line containing matching patterns as a string
    :param found: List of found keyword as tuples (index, keyword)
    :param path: Full path to the file containing the result line.
    """
    def __init__(self, line_no: int=0, line: str="", found: object=None,
                 path: str="") -> None:
        self.line_no = line_no
        self.line = line
        self.found = found
        self.path = path
        self.csv_dict = {
            "Filename": basename(self.path),
            "Line number": str(self.line_no),
            "Line": self.line,
            "Found": "|".join(self.keywords),
            "Status": "",
            "Walkthrough": "",
            "Full path": self.path
        }

    @property
    def keywords(self):
        """Returns a list of unique keywords found in result line."""
        return list(set([x[1] for x in self.found]))

    @property
    def csv_keys(self):
        """Returns the list of keys in a CSV line."""
        return CSV_TAG.join(self.csv_dict.keys())
    @property
    def csv(self):
        """Returns the result as CSV line."""
        return CSV_TAG.join(list(self.csv_dict.values()))

    def highlight(self) -> str:
        """Change color for all keywords found in line."""
        if not IS_TERMCOLOR:
            return self.line
        hlstr = []
        start = 0
        for idx, keyword in self.found:
            if start > idx:
                continue
            hlstr.append(self.line[start:idx])
            end_of_word = len(keyword) # May be improved later
            hlstr.append(colored(self.line[idx:idx+end_of_word], "red", attrs=["bold"]))
            start = idx + end_of_word
        hlstr.append(self.line[start:len(self.line)])
        return "".join(hlstr)

    def __str__(self):
        """Returns the result as a string with all megagrep info."""
        loc = "{0}:{1}".format(self.path, self.line_no)
        found = ", ".join(self.keywords)
        if IS_TERMCOLOR:
            return "{0}: {1} ({2})".format(colored(loc, "cyan"), self.highlight(),
                                           colored(found, "magenta"))
        return "{0}: {1} {2}".format(loc, self.line, found)

#-----------------------------------------------------------------------------#
# Stats object                                                                #
#-----------------------------------------------------------------------------#

class Stats(object):
    """Object containing all statistics about a megagrep scan.

    :param nb_file: Total number of scanned files.
    :param nb_line: Total number of scanned lines.
    TODO
    """
    def __init__(self) -> None:
        self.nb_file = 0
        self.nb_line = 0
        self.nb_resline = 0
        self.nb_result = 0

    def __str__(self) -> str:
        """Returns scans statistics as a nice string :)"""
        string = []
        string.append("* Total number of files: {0}".format(self.nb_file))
        string.append("* Total number of lines: {0}".format(self.nb_line))
        string.append("* Total number of results: {0}".format(self.nb_result))
        string.append("* Number of lines with results: {0}".format(self.nb_resline))
        return "\n".join(string)

#-----------------------------------------------------------------------------#
# Actual search                                                               #
#-----------------------------------------------------------------------------#

def is_included(filename: str) -> bool:
    """Check if filename should be scanned considering include/exclude lists."""
    # Exclude list
    for entry in EXCLUDE:
        if entry.match(filename):
            return False
    # Include list
    for entry in INCLUDE:
        if entry.match(filename):
            return True
    if not len(INCLUDE):
        return True
    return False

def code_generator(filename: str, stats: Stats):
    """Open a file and yield each line where at least one keyword was found.

    Returns a tuple with format::

      line_no, line, list of keyword found with indexes.

    Keyword list is a list of tuple with format (index, name). Example::

      [(2, passwd), (10, sql), (36, passwd)]
    """
    try:
        VERBOSE("Scanning file {0}...".format(filename))
        with open(filename, 'r') as fd:
            stats.nb_file += 1
            ct = 1
            for line in fd:
                stats.nb_line += 1
                line = line.strip()
                if not len(line):
                    continue
                # Look for keywords
                found = []
                for keyword, k_regex in zip(KEYWORDS, K_REGEX):
                    index = [m.start() for m in finditer(k_regex, line)]
                    if len(index):
                        for i in index:
                            stats.nb_result += 1
                            found.append((i, keyword))
                # Time to yield if keyword found
                if len(found):
                    stats.nb_resline += 1
                    yield ct, line, sorted(found)
                ct += 1
    except (IOError, UnicodeDecodeError):
        WARNING("Error while parsing file {0}.".format(filename))

def comment_generator(filename: str, stats: Stats):
    """TODO"""
    raise NotImplementedError("comment_generator")

def strings_generator(filename: str, stats: Stats):
    """TODO"""
    raise NotImplementedError("strings_generator")

def select_generator() -> object:
    """Return the appropriate generator function depending on the mode."""
    if OPTIONS.keyword or OPTIONS.stat:
        return code_generator
    elif OPTIONS.comment:
        return comment_generator
    elif OPTIONS.strings:
        return strings_generator
    ERROR("Unknown mode.")

def search(basepath: str) -> list:
    """Search keywords in all matching files from path."""
    stats = Stats()
    results = []
    generator = select_generator()
    for path, dirs, files in walk(basepath):
        # Ignore hidden
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for item in files:
            # Apply include and exclude list on item name
            if is_included(item):
                item_path = join(path, item)
                for nb, line, content in generator(item_path, stats):
                    results.append(Result(nb, line, content, item_path))
    return results, stats

###############################################################################
# RUN                                                                         #
###############################################################################

#--- Banner ------------------------------------------------------------------#

print("{0:-^79}".format(""))
if IS_PYFIGLET:
    print(figlet_format("Megagrep", font="script", justify="center"))
else:
    print("{0: ^79}".format(" MEGAGREP "))
print("{0:-^79}".format(""))

#--- Init -------------------------------------------------------------------#

OPTIONS = init_options()
VERBOSE("{0:-^69}".format(" Initialization "))
VERBOSE("Options: {0}".format(OPTIONS.__dict__))
KEYWORDS, K_REGEX = init_keywords()
VERBOSE("Keywords: {0}".format(KEYWORDS))
PATH = init_path()
VERBOSE("Path to scan (recursive): {0}".format(PATH))
INCLUDE, EXCLUDE = init_include_exclude()
VERBOSE("File included: {0}".format(OPTIONS.include))
VERBOSE("File excluded: {0}".format(OPTIONS.exclude))
VERBOSE("{0:-^69}".format(" Start scan "))

#--- Search -------------------------------------------------------------------#

RESULTS, STATS = search(PATH)

#--- Output -------------------------------------------------------------------#

VERBOSE("{0:-^69}".format(" Output "))

# CSV OUTPUT MODE
if OPTIONS.csv and len(RESULTS):
    print(RESULTS[0].csv_keys)
    for result in RESULTS:
        print(result.csv)
if OPTIONS.file:
    raise NotImplementedError("Option: Export to file.")

# REGULAR OUTPUT MODE
if not OPTIONS.stat and not OPTIONS.csv:
    for result in RESULTS:
        print(result)

# STAT OUTPUT MODE (printed to stdout anyway, at least for now)
print("{0:-^79}".format(" Summary "))
print(STATS)
