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

![GitHub](https://img.shields.io/github/license/claire-lex/megagrep)

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

**More usage examples below!**

Status
------

So far, only the basic scan based on keywords with output on terminal works.

Coming soon:

* "Comment" mode: Extract comments from source files.
* "String" mode: Look for strings in source files.
* Add direct regex support in dictionaries with prefix `regex:`
* Directory tree analysis (find interesting source files in tree)
* Improve "stat" mode content (ideas welcome!)

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

Stat scan (only display global informaiton in scan):
```
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
  1. DUMMY_PATH/index.php (20)
  2. DUMMY_PATH/classes/Login.php (14)
  3. DUMMY_PATH/templates/fonts/fontawesome-webfont.svg (12)
  4. DUMMY_PATH/templates/loginform.php (8)
  5. DUMMY_PATH/config.php (3)
  6. DUMMY_PATH/templates/logged.php (1)
  7. DUMMY_PATH/templates/include/header.php (1)
  8. DUMMY_PATH/templates/edit.php (1)
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
