# Megagrep
# Locate critical areas and keywords in code
#
# Lex @ https://github.com/claire-lex/megagrep - 2022
#
# pylint: disable=invalid-name,anomalous-backslash-in-string

"""
usage: megagrep.py [-h] [-v] [-s] [-n] [-K] [-S] [-L] [-C] [-T] [-N]
                   [-i files)] [-x file(s)] [-w word(s)] [-d file(s)]
                   [-l list(s] [-t comment tag] [-c] [-e] [-f filename]
                   [path]

Megagrep helps beginning a code review by looking at keywords using "grep".
This is not a static analysis tool, it just searches for places in the code
that require to be investigated manually.

positional arguments:
  path                  Path to files to (mega)grep.

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         Verbose mode.
  -s, --sensitive       Enable case-sensitive mode (default: insensitive).
  -n, --nocolor         Remove colors from output (e.g. for parsing).
  -K, --keyword         Search by keywords from a dictionary file (default
                        mode).
  -S, --stat            Give only statistics about the code (rely on other
                        modes).
  -L, --ls              Give results statistics on the source directory tree.
  -C, --comment         Search comments in the code.
  -T, --strings         Search strings in the code.
  -N, --names           Search for keywords in file names only.
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
  -t comment tag, --tag comment tag
                        Use a custom tag for one-line comments (ex: ;, ::).
  -c, --csv             Output in CSV format (default is colored ASCII).
  -e, --extended        Print extended output with previous and next lines.
  -f filename, --file filename
                        Output to file.
"""

from os import access, R_OK, getcwd, walk
from os.path import dirname, join, realpath, relpath, exists, isfile, basename
from textwrap import fill, shorten
from argparse import ArgumentParser
from importlib.util import find_spec
from re import finditer, IGNORECASE
from re import compile as re_compile, escape as re_escape

###############################################################################
# CONFIGURATION                                                               #
###############################################################################

#--- Dictionary --------------------------------------------------------------#

# Default dictionary is dict/global.mg in megagrep.py's directory
DEFAULT_DICTIONARY = join(dirname(realpath(__file__)), join("dicts", "global.mg"))
# Comment tag set in dictionary files. Everything after this tag in a line is ignored.
DICT_COMMENT_TAG = "#"
# Category header in dictionary files. Currently between brackets: [category]
LIST_REGEX = re_compile(r"^\[([\w\-\_\+]*)\]$")

#--- File handling -----------------------------------------------------------#

# Default files not to read
DEFAULT_EXCLUDE = ("*.min.js,*.css")

#--- Search -----------------------------------------------------------#

# Strings

STRING_ONELINE_REGEX = re_compile("[^{0}]*{0}([^{0}]+){0}[^{0}]*".format("\""))

# Comments

# Basic, one-line comments starting with // or #
COMMENT_DEFAULT_REGEX = re_compile("(?://|#)(.*)")
# One-line and multi line C-style regex (/* ... */)
COMMENT_CSTYLE_REGEX = re_compile("\/\*(\*[?!\/]|[^*]*)\*\/")
# One-line and multi-line Docstrings (Python regex)
COMMENT_PYDOC_REGEX = re_compile("[\"]{3}([\w\W]*?)[\"]{3}")

COMMENT_REGEX_LIST = [
    COMMENT_DEFAULT_REGEX,
    COMMENT_CSTYLE_REGEX,
    COMMENT_PYDOC_REGEX
]

#--- Output ------------------------------------------------------------------#

# Separator between columns for CSV output
CSV_TAG = ","
# Replacement separator to concatenate list in CSV output. Must not be CSV_TAG.
REPLACECOMMA_CSV_TAG = "|"
# Maximum length of line to output, the rest is truncated with [...] after.
MAX_LEN = 200
# Default value for Top X in stat mode
TOP_VALUE = 10

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
    print("[WARNING] Megagrep requires \"pyfiglet\" to print beautiful text. " \
            "(pip install pyfiglet)")
if IS_TERMCOLOR:
    from termcolor import colored
else:
    print("[WARNING] Megagrep requires \"termcolor\" to color the output. " \
            "(pip install termcolor)")

#--- Messages ----------------------------------------------------------------#

def VERBOSE(message: str) -> None:
    """Prints additional information to stdout if ``verbose`` option is set."""
    if not OPTIONS.verbose:
        return
    if IS_TERMCOLOR and not OPTIONS.nocolor:
        print(colored(fill("[INFO]    {0}".format(message), width=80), "cyan"))
    else:
        print(fill("[INFO]    {0}".format(message), width=80))

def WARNING(message: str) -> None:
    """Prints warning messages (non-blocking errors) to stdout."""
    if IS_TERMCOLOR and not OPTIONS.nocolor:
        print(colored(fill("[WARNING] {0}".format(message), width=80), "red"))
    else:
        print(fill("[WARNING] {0}".format(message), width=80))

def ERROR(message: str) -> None:
    """Prints error messages to stdout and exits."""
    if IS_TERMCOLOR and not OPTIONS.nocolor:
        print(colored(fill("[ERROR]   {0}".format(message), width=80), "red",
                      attrs=["bold"]))
    else:
        print(fill("[ERROR]   {0}".format(message), width=80))
    exit(-1)

#-----------------------------------------------------------------------------#
# File management                                                             #
#-----------------------------------------------------------------------------#

def CHECKFILE(filename: str, force_file=False) -> bool:
    """Check if source file exists. Returns True or False"""
    fullarg = realpath(filename)
    if not exists(fullarg) or not access(fullarg, R_OK):
        return False
    if force_file and not isfile(fullarg):
        return False
    return True

#-----------------------------------------------------------------------------#
# Result output                                                               #
#-----------------------------------------------------------------------------#

def PRINT(message: str, out: str=None) -> None:
    """Print message to standard output and to a file if option set.
    If TERMCOLOR is installed, the message will be printed with color codes
    to stdout, and without color codes to file.
    """
    print(message)
    if out:
        try:
            if isinstance(message, Result):
                message = message.result
            with open(out, "a") as fd:
                fd.write(str(message)+"\n")
        except IOError:
            # Megagrep continues but will not save results to file.
            ERROR("Cannot write to file {0}".format(OUTPUT_FILE))

def PRINT_TOP(summary: list, top: int=TOP_VALUE, out: str=None):
    """Print top with values from summary to stdout and to a file if option set.
    Summary is a list of tuples (number of occurrences, values).
    """
    ct = 1
    for occur, value in summary:
        PRINT("{0: >3}. {1} ({2})".format(ct, value, occur), out)
        if ct == top:
            break
        ct += 1

def PRINT_TREE(path: str, message: str="", out: str=None) -> None:
    """Print directory tree with a syntax close to the `tree` command."""
    if OPTIONS.ls:
        rel = relpath(path)
        level = len(rel.split("/"))
        pre = "   < " if message else "--"
        end = " >" if message else ""
        message = message if message else basename(rel)
        PRINT("|{0}{1} {2}{3}".format("   | "* (level-1), pre, message, end), out)

###############################################################################
# OPTIONS                                                                     #
###############################################################################

#-----------------------------------------------------------------------------#
# Constants                                                                   #
#-----------------------------------------------------------------------------#

# Default values
D_VERBOSE = False
D_SENSITIVE = False
D_NOCOLOR = False
D_KEYWORD = True
D_STAT = False
D_LS = False
D_COMMENT = False
D_STRINGS = False
D_NAMES = False
D_INCLUDE = None
D_EXCLUDE = DEFAULT_EXCLUDE
D_WORD = None
D_DICT = None
D_LIST = None
D_TAG = None
D_CSV = False
D_EXTENDED = False
D_FILE = None

# Help messages
H_MEGAGREP = "Megagrep helps beginning a code review by looking at keywords \
using \"grep\". This is not a static analysis tool, it just searches for \
places in the code that require to be investigated manually."
H_VERBOSE = "Verbose mode."
H_SENSITIVE = "Enable case-sensitive mode (default: insensitive)."
H_NOCOLOR = "Remove colors from output (e.g. for parsing)."
H_KEYWORD = "Search by keywords from a dictionary file (default mode)."
H_STAT = "Give only statistics about the code (rely on other modes)."
H_LS = "Give results statistics on the source directory tree."
H_COMMENT = "Search comments in the code."
H_STRINGS = "Search strings in the code."
H_NAMES = "Search for keywords in file names only."
H_INCLUDE = "Files to include in search (ex: *.java)."
H_EXCLUDE = "Files to exclude from search (ex: *.min.js)."
H_WORD = "Search for specific word(s)."
H_DICT = "Use other dictionary file(s)."
H_LIST = "Use specific list from dictionary file(s)."
H_TAG = "Use a custom tag for one-line comments (ex: ;, ::)."
H_CSV = "Output in CSV format (default is colored ASCII)."
H_EXTENDED = "Print extended output with previous and next lines."
H_FILE = "Output to file."

# Meta text
M_FILE = "file(s)"
M_WORD = "word(s)"
M_LIST = "list(s)"
M_TAG = "comment tag"
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
    ("-n", "--nocolor", H_NOCOLOR, D_NOCOLOR, None),
    # Mode
    ("-K", "--keyword", H_KEYWORD, D_KEYWORD, None),
    ("-S", "--stat", H_STAT, D_STAT, None),
    ("-L", "--ls", H_LS, D_LS, None),
    ("-C", "--comment", H_COMMENT, D_COMMENT, None),
    ("-T", "--strings", H_STRINGS, D_STRINGS, None),
    ("-N", "--names", H_NAMES, D_NAMES, None),
    # Input
    ("-i", "--include", H_INCLUDE, D_INCLUDE, M_FILE),
    ("-x", "--exclude", H_EXCLUDE, D_EXCLUDE, M_FILE),
    # Parsing
    ("-w", "--word", H_WORD, D_WORD, M_WORD),
    ("-d", "--dict", H_DICT, D_DICT, M_FILE),
    ("-l", "--list", H_LIST, D_LIST, M_LIST),
    # Comments
    ("-t", "--tag", H_TAG, D_TAG, M_TAG),
    # Output
    ("-c", "--csv", H_CSV, D_CSV, None),
    ("-e", "--extended", H_EXTENDED, D_EXTENDED, None),
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
            line = line.split(DICT_COMMENT_TAG)[0].strip()
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
        REGEX = lambda x: re_compile(re_escape(x).replace("*", r".*"))
    else:
        REGEX = lambda x: re_compile(re_escape(x).replace("*", r".*"), IGNORECASE)
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
        VERBOSE("No keyword found, using default dictionary.")
        keywords += parse_dict(DEFAULT_DICTIONARY, categories)
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
                 path: str="", before: str="", after: str="") -> None:
        self.line_no = line_no
        self.line = line
        self.found = found
        self.path = path
        self.csv_dict = {
            "Filename": basename(self.path),
            "Line number": str(self.line_no),
            "Line": self.line,
            "Found": REPLACECOMMA_CSV_TAG.join(self.keywords),
            "Status": "",
            "Walkthrough": "",
            "Full path": self.path
        }
        # FOR EXTENDED MODE ONLY
        self.before = before
        self.after = after

    @property
    def keywords(self):
        """Returns a list of unique keywords found in result line."""
        return list(set([x[1] for x in self.found]))
    @property
    def all_keywords(self):
        """Returns the list of keywords with all occurrences found in line."""
        return [x[1] for x in self.found]
    @property
    def result(self):
        """Returns the result as a regular string with absolute path.
        This property is used to write results to files.
        """
        loc = "{0}:{1}".format(self.path, self.line_no)
        line = shorten(self.line, width=MAX_LEN)
        found = ", ".join(self.keywords)
        return "{0}: {1} ({2})".format(loc, line, found)
    @property
    def csv_keys(self):
        """Returns the list of keys in a CSV line."""
        return CSV_TAG.join(self.csv_dict.keys())
    @property
    def csv(self):
        """Returns the result as CSV line."""
        return CSV_TAG.join(list(self.csv_dict.values()))
    @property
    def relpath(self):
        """Returns the relative path instead of absolute one."""
        return relpath(self.path)
    @property
    def previous_line(self):
        """Returns the previous line with output format."""
        before = shorten(self.before, width=MAX_LEN)
        return "{0}:{1}: {2}".format(self.relpath, self.line_no-1, before)
    @property
    def next_line(self):
        """Returns the next line with output format."""
        after = shorten(self.after, width=MAX_LEN)
        return "{0}:{1}: {2}".format(self.relpath, self.line_no+1, after)

    def highlight(self) -> str:
        """Change color for all keywords found in line."""
        if not IS_TERMCOLOR or OPTIONS.nocolor:
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
        loc = "{0}:{1}".format(self.relpath, self.line_no)
        line = shorten(self.highlight(), width=MAX_LEN)
        found = ", ".join(self.keywords)
        if IS_TERMCOLOR and not OPTIONS.nocolor:
            return "{0}: {1} ({2})".format(colored(loc, "cyan"), line, colored(found, "magenta"))
        return "{0}: {1} ({2})".format(loc, line, found)

#-----------------------------------------------------------------------------#
# Stats object                                                                #
#-----------------------------------------------------------------------------#

class Stats(object):
    """Object containing all statistics about a megagrep scan.

    :param nb_file: Total number of scanned files.
    :param nb_line: Total number of scanned lines.
    :param nb_result: Total number of results.
.    :param nb_resline: Total number of lines with at least one result.
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

def pattern_keyword(line: str) -> list:
    """Keyword-based mode."""
    found = []
    for keyword, k_regex in zip(KEYWORDS, K_REGEX):
        index = [m.start() for m in finditer(k_regex, line)]
        if len(index):
            for i in index:
                found.append((i, keyword))
    return found

def pattern_comment(line: str) -> list:
    """One-line comments extraction mode."""
    found = []
    if OPTIONS.tag:
        regex_list = [re_compile("(?:{0})(.*)".format(OPTIONS.tag))]
    else:
        regex_list = COMMENT_REGEX_LIST
    for regex in regex_list:
        index = finditer(regex, line)
        for i in index:
            found.append((i.start(1), i.group(1)))
    return found

def pattern_strings(line: str) -> list:
    """One-line strings extraction mode."""
    found = []
    index = finditer(STRING_ONELINE_REGEX, line)
    for i in index:
        found.append((i.start(1), i.group(1)))
    return found

def select_pattern() -> object:
    """Return the appropriate search function depending on the mode."""
    if OPTIONS.comment:
        return pattern_comment
    elif OPTIONS.strings:
        return pattern_strings
    return pattern_keyword


def megagenerator(filename: str, stats: Stats) -> None:
    """Generator function searching for mode-defined patterns in lines.

    Returns a tuple with format::

      (line_no, line, found patterns, previous, next line)

    "Found pattern" is a list of tuple with format (index, name). Example::

      [(2, passwd), (10, sql), (36, passwd)]
    """
    try:
        pattern_search = select_pattern()
        with open(filename, 'r') as fd:
            ct = -1
            VERBOSE("Scanning file {0}...".format(filename))
            lines = fd.readlines()
            for line in lines:
                ct += 1
                line = line.strip()
                if not len(line):
                    continue
                # Look for pattern
                found = pattern_search(line)
                # Time to yield if keyword found
                if len(found):
                    before = lines[ct-1].strip() if ct > 0 else ""
                    after = lines[ct+1].strip() if ct < len(lines)-1 else ""
                    # Ct start at 0, we increment for actual line number starting at 1
                    yield ct+1, line, sorted(found), before, after
                    # STAT: Number of lines with result, total number of results
                    stats.nb_result += len(found)
                    stats.nb_resline += 1
                # STAT: Number of lines read
                stats.nb_line += 1
            # STAT: Number of files read
            stats.nb_file += 1
    except (IOError, UnicodeDecodeError):
        VERBOSE("Error while parsing file {0}.".format(filename))

def name_search(filename: str, path: str) -> list:
    """Search for keywords directly in filenames.

    Returns a list containing Result object, or empty list if no pattern
    was found.
    """
    found = pattern_keyword(filename)
    if len(found):
        out = " - ".join((filename, path))
        return [Result(0, out, sorted(found), path, "", "")]
    return []

def content_search(path: str, stats: Stats, out:str = None) -> list:
    """Search depending on the mode in the content of all matching files
    from path.

    Returns a list of a results for each file (or empty list).
    """
    file_results = []
    for nb, line, content, before, after in megagenerator(path, stats):
        file_results.append(Result(nb, line, content, path, before, after))
        if len(file_results):
            top = [y for x, y in top_keywords(file_results)]
            PRINT_TREE(path, out=out)
            PRINT_TREE(path, "{0} results | Top: {1}".format(
                len(file_results), ", ".join(top[:3])), out=out)
    return file_results

def search(basepath: str, out:str = None) -> list:
    """Search keywords in all matching files from path."""
    stats = Stats()
    results = []
    for path, dirs, files in walk(basepath):
        PRINT_TREE(path, out=out)
        # Ignore hidden
        files = [f for f in files if not f[0] == '.']
        dirs[:] = [d for d in dirs if not d[0] == '.']
        for item in files:
            # Apply include and exclude list on item name
            if is_included(item):
                file_results = []
                item_path = join(path, item)
                if OPTIONS.names:
                    file_results += name_search(item, item_path)
                else:
                    file_results += content_search(item_path, stats, out)
                results += file_results
    return results, stats

###############################################################################
# ANALYSIS                                                                    #
###############################################################################

def top_counter(full_list: list) -> list:
    """Returns list of tuple (number of occurrences, value) from full_list."""
    unique = set(full_list)
    summary = []
    for value in unique:
        summary.append((full_list.count(value), value))
    return sorted(summary, reverse=True)

def top_keywords(results: list) -> list:
    """Returns most frequently found keywords."""
    all_keywords = []
    for result in results:
        all_keywords += result.all_keywords
    return top_counter(all_keywords)

def top_files(results: list) -> list:
    """Returns files with the most results."""
    all_files = [relpath(x.path) for x in results]
    return top_counter(all_files)

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

# FILE OUTPUT MODE
OUTPUT_FILE = None
if OPTIONS.file:
    if CHECKFILE(OPTIONS.file): # File exists
        WARNING("File {0} cannot be opened for writing.".format(OPTIONS.file))
        WARNING("If the file already exists, Megagrep will not overwrite it.")
    else:
        OUTPUT_FILE = realpath(OPTIONS.file)
        VERBOSE("Output will be written to file: {0}".format(OUTPUT_FILE))

#--- Search -------------------------------------------------------------------#

VERBOSE("{0:-^69}".format(" Start scan "))
RESULTS, STATS = search(PATH, OUTPUT_FILE)

#--- Output -------------------------------------------------------------------#

VERBOSE("{0:-^69}".format(" Output "))

# CSV OUTPUT MODE
if OPTIONS.csv and len(RESULTS):
    print(RESULTS[0].csv_keys)
    for result in RESULTS:
        PRINT(result.csv, OUTPUT_FILE)

# EXTENDED OUTPUT MODE
elif OPTIONS.extended:
    for result in RESULTS:
        print("{0:-^79}".format(""))
        PRINT(result.previous_line, OUTPUT_FILE)
        PRINT(result, OUTPUT_FILE)
        PRINT(result.next_line, OUTPUT_FILE)

# STAT OUTPUT MODE
elif OPTIONS.stat:
    PRINT("{0:-^79}".format(" Most frequent keywords "), OUTPUT_FILE)
    PRINT_TOP(top_keywords(RESULTS), TOP_VALUE, OUTPUT_FILE)
    PRINT("{0:-^79}".format(" Files with most results "), OUTPUT_FILE)
    PRINT_TOP(top_files(RESULTS), TOP_VALUE, OUTPUT_FILE)

# REGULAR OUTPUT MODE
elif not OPTIONS.ls:
    for result in RESULTS:
        PRINT(result, OUTPUT_FILE)

PRINT("{0:-^79}".format(" Summary "), OUTPUT_FILE)
PRINT(STATS, OUTPUT_FILE)

if OUTPUT_FILE:
    print("{0:-^79}".format(" Results written to file "))
    print("{0: ^79}".format(OUTPUT_FILE))
