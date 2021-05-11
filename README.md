Megagrep
========

> Or how to begin a code review

**Megagrep helps beginning a code review by looking at keywords in the code using
"grep", but this is not static analysis tool**. 

Megagrep and its keyword sets are built to search for places in the code that
require to be investigated manually. It will give you **locations** (where to
find vulnerabilities), not vulnerabilities directly.

If you want a grep-based static analysis tool (for vulnerability research), you
can check [Graudit](https://github.com/wireghoul/graudit).

Getting Started
---------------

Clone repository:

```
https://github.com/claire-lex/megagrep
```

(Optional) Install requirements to improve terminal output (nice text and colors):

```
pip install -r requirements.txt
```

Run with standard options and dictionary on a directory:
```
python megagrep.py /path/to/my/code
```

Usage
-----

```
$> python megagrep.py -h
-------------------------------------------------------------------------------
                  ,__ __                                      
                 /|  |  |                                     
                  |  |  |   _   __,  __,   __,  ,_    _    _  
                  |  |  |  |/  /  | /  |  /  | /  |  |/  |/ \_
                  |  |  |_/|__/\_/|/\_/|_/\_/|/   |_/|__/|__/ 
                                 /|         /|          /|    
                                 \|         \|          \|    

-------------------------------------------------------------------------------
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
  -A, --all             Run all scan modes successively.
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
```

Coming soon
-----------

* "String" mode: Look for strings in the source file.