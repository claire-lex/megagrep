# Changelog

## [?.?.?] ????-??-??
### Added
- Option `-N` to search for keywords in filenames
- Option `-n` to remove colors from output (for parsing purposes)
### Changed
- Details on supported languages and limitations in README

## [1.2.0] 2021-11-02
### Added
- Comments mode improved with C-style multi-line comment support
- Option `--tag` added, to choose a specific starting tag for one-line comments
### Changed
- Dictionaries improved using OWASP code review guide and code review
  repositories

## [1.1.0] 2021-06-02
### Added
- "Strings" search mode for strings on one line starting and ending with `"`
- "Comments" search mode for comments on one line starting with `#` or `//`
- "Ls" search mode to display statistics about directory tree
### Changed
- README now explains how to begin a code review with Megagrep

## [1.0.0] 2021-05-18
### Added
- "Stat" mode with basic "top 10" results
- "Keyword" search mode to search for keywords in code from a dictionary
  or a list of words given in command line arguments.
- Print to standard output with color (termcolor) or as CSV
- Export results to files
- Basic default dictionary
