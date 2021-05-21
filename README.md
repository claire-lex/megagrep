```
-------------------------------------------------------------------------------
                  ,__ __                                      
                 /|  |  |                                     
                  |  |  |   _   __,  __,   __,  ,_    _    _  
                  |  |  |  |/  /  | /  |  /  | /  |  |/  |/ \_
                  |  |  |_/|__/\_/|/\_/|_/\_/|/   |_/|__/|__/ 
                                 /|         /|          /|    
                                 \|         \|          \|    

-------------------------------------------------------------------------------
```

Megagrep helps beginning a code review by searching for patterns in the code
using "grep". **It does not search for vulnerabilities directly but for places
where you could manually find some**.

Megagrep searches for patterns in the code that require to be investigated
manually for security issues. It uses several search modes (keyword-based,
strings or comments extraction) and outputs either detailed results or global
information to discover the code and locate interesting pieces of code (most
frequent keywords, files with the most results, etc.).

This is not *really* a security-focused static analysis tool. Patterns are
intentionally not too restrictive and will probably trigger false positives, but
to figure it out you have to... review all suspicious pieces of code :). In
other words, Megagrep will give you **locations** (where you could find
vulnerabilities), not vulnerabilities directly.

If you want a grep-based static analysis tool for direct vulnerability research,
you can check [Graudit](https://github.com/wireghoul/graudit).

![GitHub release (latest by date)](https://img.shields.io/github/v/release/claire-lex/megagrep)
![GitHub](https://img.shields.io/github/license/claire-lex/megagrep)
![Help wanted](https://img.shields.io/badge/Help%20me-New%20dictionaries-brightgreen)
![Useful statistics](https://img.shields.io/badge/Help%20me-Useful%20statistics-brightgreen)

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

Run with standard options and default dictionary on a directory:
```
python megagrep.py /path/to/my/code
```

Store results to a file:
```
python megagrep.py my_directory -f megagrep.out
```

Print help:
```
python megagrep.py -h
```

Usage
-----

### Run scans

Default scan (one line per result, with color if termcolor is installed):
```
$> python megagrep.py .
[...]
classes/Login.php:51: public static function checkAuth($bank_id, $password) { (auth*, passw*d)
classes/Login.php:52: $conn = new PDO(DB_DSN, DB_USERNAME, DB_PASSWORD); (passw*d)
classes/Login.php:53: $sql = "SELECT * FROM users WHERE bank_id='".$bank_id; (sql)
classes/Login.php:54: $sql = $sql."' AND password='".md5($password)."';"; (sql, md5, passw*d)
classes/Login.php:56: $st = $conn->prepare($sql); (sql)
classes/Login.php:57: $st->execute(); (exec)
[...]
```

Extended scan (print lines before and after matching line):
```
$> python megagrep.py -e .
[...]
-------------------------------------------------------------------------------
classes/Login.php:52: $conn = new PDO(DB_DSN, DB_USERNAME, DB_PASSWORD);
classes/Login.php:53: $sql = "SELECT * FROM users WHERE bank_id='".$bank_id; (sql)
classes/Login.php:54: $sql = $sql."' AND password='".md5($password)."';";
-------------------------------------------------------------------------------
classes/Login.php:53: $sql = "SELECT * FROM users WHERE bank_id='".$bank_id;
classes/Login.php:54: $sql = $sql."' AND password='".md5($password)."';"; (md5, passw*d, sql)
classes/Login.php:55: 
-------------------------------------------------------------------------------
classes/Login.php:55: 
classes/Login.php:56: $st = $conn->prepare($sql); (sql)
classes/Login.php:57: $st->execute();
-------------------------------------------------------------------------------
[...]
```

Stat scan (only display global scan information), excluding `.js` files:
```
$> python -S -x "*.js"
[...]
--------------------------- Most frequent keywords ----------------------------
  1. login (21)
  2. passw*d (11)
  3. session (9)
  4. sql (8)
  5. auth* (4)
  6. upload (3)
  7. sha*1 (3)
  8. download (3)
  9. md5 (2)
 10. exec (2)
--------------------------- Files with most results ---------------------------
  1. /path/to/index.php (20)
  2. /path/to/classes/Login.php (14)
  3. /path/to/templates/fonts/fontawesome-webfont.svg (12)
  4. /path/to/templates/loginform.php (8)
  5. /path/to/config.php (3)
  6. /path/to/templates/logged.php (1)
  7. /path/to/templates/include/header.php (1)
  8. /path/to/templates/edit.php (1)
[...]
```

Strings mode (Search for one-line strings), including only `.php` files:
```
$> python megagrep.py -T -i "*.php"
[...]
config.php:6: define("DB_DSN", "mysql:host=localhost;dbname=testo"); (mysql:host=localhost;dbname=testo, DB_DSN)
config.php:7: define("DB_USERNAME", "root"); (DB_USERNAME, root)
config.php:8: define("DB_PASSWORD", "P@$$w0rd"); (DB_PASSWORD, P@$$w0rd)
config.php:9: define("CLASS_PATH", "classes"); (classes, CLASS_PATH)
config.php:10: define("TEMPLATE_PATH", "templates"); (TEMPLATE_PATH, templates)
[...]
```

Output to format mode (add `-f file.csv` to also export to a CSV file):
```
$> python megagrep.py -c -i "*.php" 
[...]
Login.php,51,public static function checkAuth($bank_id, $password) {,auth*,,,/path/to/classes/Login.php
Login.php,53,$sql = "SELECT * FROM users WHERE bank_id='".$bank_id;,sql,,,/path/to/classes/Login.php
Login.php,54,$sql = $sql."' AND password='".md5($password)."';";,sql|md5,,,/path/to/classes/Login.php
Login.php,56,$st = $conn->prepare($sql);,sql,,,/path/to/classes/Login.php
Login.php,57,$st->execute();,exec,,,/path/to/classes/Login.php
[...]
```

Ls mode (outputs details about directory tree), including only `.php` files:
```
[...]
|-- .
|-- config.php
|   <  2 results | Top: sql, login >
|-- index.php
|   <  20 results | Top: login, session, auth* >
|-- classes
|   | -- Login.php
|   |    <  12 results | Top: sql, login, exec >
|-- templates
|   | -- logged.php
|   |    <  1 results | Top: md5 >
|   | -- loginform.php
|   |    <  4 results | Top: login, auth* >
|   | -- css
|   | -- fonts
|   | -- images
|   | -- include
|   |    | -- header.php
|   |    |    <  1 results | Top: query >
|   | -- js
[...]
```

### Use/write dictionaries

You can use default dictionaries in ``dicts/`` and also use your own:

```
python megagrep.py -d path/to/dictionary
```

A dictionary has the following format:

```
# Comment line

[list_name]
keyword1
keyword2 # Comment at the end
matching_keyw*d
```

Example:

```
# Global keywords

[authentication]
auth* # authentication and authorization stuff
login
passw*d
pwd
session
admin*
```

You can choose to use only part of a dictionary with ``-l``:

```
python megagrep.py -l authentication
```

Option `-w` can be used to search specific words directly (alone or combined
with a dictionary):

```
$> python megagrep.py -w bad,wrong # Search for words "bad" and "wrong" only
$> python megagrep.py -w bad -d my_dict # Search for "bad" and the content of my_dict
```

Coming soon
-----------

* Add direct regex support in dictionaries with prefix `regex:`
* Export results as HTML
* Add better dictionaries (help welcome!)
* Improve "stat" mode content (ideas welcome!)
* Improve "string" mode: Look for strings on multiple lines in source files.
* Improve "comment" mode: Extract comments on multiple lines from source files.
* Improve "ls" mode: Find keywords in filenames, locate specific files.