#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""nodedoc -- fledgling perldoc for node.js

Usage:
    nodedoc SECTION

See <https://github.com/trentm/nodedoc> for more info.
"""

__version_info__ = (1, 0, 1)
__version__ = '.'.join(map(str, __version_info__))

import re
import sys
import textwrap
import os
from os.path import dirname, abspath, join, exists
import logging
import codecs
import optparse
from glob import glob

TOP = dirname(dirname(abspath(__file__)))
if not exists(join(TOP, "tools", "cutarelease.py")):  # installed layout
    TOP = join(TOP, "lib", "node_modules", "nodedoc")
sys.path.insert(0, join(TOP, "deps"))
import markdown2
import appdirs



#---- globals

log = logging.getLogger("nodedoc")
CACHE_DIR = appdirs.user_cache_dir("nodedoc", "trentm")



#---- exceptions

class Error(Exception):
    pass



#---- stylers

def red(text):
    return '\033[31m' + text + '\033[39m'
def green(text):
    return '\033[32m' + text + '\033[39m'
def cyan(text):
    return '\033[36m' + text + '\033[39m'
def grey(text):
    return '\033[90m' + text + '\033[39m'

def bold(text):
    return '\033[1m' + text + '\033[22m'
def italic(text):
    return '\033[3m' + text + '\033[23m'
def inverse(text):
    return '\033[7m' + text + '\033[27m'



#---- re.sub transformers

def indent(match):
    INDENT = '    '
    text = match.group(1)
    after = INDENT + INDENT.join(text.splitlines(True))
    #print "XXX hit: after=%r" % after
    return after

def code(match):
    """green. Special case grey for "Stability: ..." pre-blocks."""
    text = match.group(1)
    styler = green
    if text.startswith("Stability:"):
        styler = grey
    lines = [
        styler(line)
        for line in text.splitlines(False)
    ]
    return '\n'.join(lines)

def wrap(match, width=80):
    """XXX TODO: somehow make the ANSI escapes zero-length for width
    calculation."""
    text = match.group(1)
    text = '\n'.join(textwrap.wrap(text, width=width))
    return text

def h1(match):
    """bold red"""
    text = match.group(1)
    return bold(red('# ' + text))
    return '\n'.join(lines)

def h2(match):
    """bold red, extra leading space"""
    text = match.group(1)
    text = '\n' + bold(red('## ' + text))
    return text

def h3(match):
    """bold red"""
    text = match.group(1)
    text = '\n' + bold(red('### ' + text))
    return text

def a(match):
    """blue"""
    text = match.group(1)
    lines = [
        '\033[34m' + line + '\033[39m'
        for line in text.splitlines(False)
    ]
    return '\n'.join(lines)

def em(match):
    """cyan"""
    text = match.group(1)
    lines = [cyan(line) for line in text.splitlines(False)]
    return cyan('*') + '\n'.join(lines) + cyan('*')

def strong(match):
    """bold cyan"""
    text = match.group(1)
    lines = [bold(cyan(line)) for line in text.splitlines(False)]
    return bold(cyan('**')) + '\n'.join(lines) + bold(cyan('**'))

def li(match):
    """bullet and indent and reflow"""
    text = match.group(1)
    text = '\n'.join(textwrap.wrap(text, width=78))
    INDENT = '  '
    text = INDENT + INDENT.join(text.splitlines(True))
    text = '-' + text[1:]
    return text

def noop(match):
    return match.group(1)



#---- main nodedoc functionality

def generate_html_path(markdown_path, html_path):
    if not exists(dirname(html_path)):
        os.makedirs(dirname(html_path))
    html = markdown2.markdown_path(markdown_path)
    codecs.open(html_path, 'w', 'utf-8').write(html)

def generate_nodedoc_path(html_path, nodedoc_path):
    if not exists(dirname(nodedoc_path)):
        os.makedirs(dirname(nodedoc_path))

    content = codecs.open(html_path, 'r', 'utf-8').read()

    # html comments: drop
    content = re.compile('\n?<!--(.*?)-->\n', re.S).sub('', content)

    # code:
    content = re.compile('<code>(.*?)</code>', re.S).sub(code, content)

    # pre: indent
    content = re.compile('<pre>(.*?)</pre>', re.S).sub(indent, content)

    # li: bullet
    # XXX how to know in ol? AFAICT only one <ol> in node.js docs, so ignoring for now.
    # XXX does this mess up multi-para li?
    content = re.compile('<li>(?:<p>)?(.*?)(?:</p>)?</li>', re.S).sub(li, content)
    # ol, ul: ignore
    content = re.compile('\n?<ul>(.*?)</ul>\n', re.S).sub(noop, content)
    content = re.compile('\n?<ol>(.*?)</ol>\n', re.S).sub(noop, content)

    # p: wrap content at 80 columns
    content = re.compile('<p>(.*?)</p>', re.S).sub(wrap, content)

    # a: drop attrs (until/unless have a way to follow those links)
    content = re.compile('<a[^>]*>(.*?)</a>', re.S).sub(a, content)

    content = re.compile('<em>(.*?)</em>', re.S).sub(em, content)
    content = re.compile('<strong>(.*?)</strong>', re.S).sub(strong, content)

    # hN: highlight, but how to highlight different levels?
    content = re.compile('<h1>(.*?)</h1>', re.S).sub(h1, content)
    content = re.compile('<h2>(.*?)</h2>', re.S).sub(h2, content)
    content = re.compile('<h3>(.*?)</h3>', re.S).sub(h3, content)

    #TODO:XXX special case two adjacent h2's, e.g.:
    #
    #    <h2>fs.utimes(path, atime, mtime, [callback])</h2>
    #
    #    <h2>fs.utimesSync(path, atime, mtime)</h2>
    #
    #    <p>Change file timestamps of the file referenced by the supplied path.</p>

    codecs.open(nodedoc_path, 'w', 'utf-8').write(content)


def nodedoc(section):
    markdown_path = join(TOP, "doc", "api", section + ".markdown")
    if not exists(markdown_path):
        raise Error("no such section: '%s'" % section)

    html_path = join(CACHE_DIR, section + ".html")
    if not exists(html_path) or mtime(html_path) < mtime(markdown_path):
        generate_html_path(markdown_path, html_path)

    nodedoc_path = join(CACHE_DIR, section + ".nodedoc")
    if not exists(nodedoc_path) or mtime(nodedoc_path) < mtime(html_path):
        generate_nodedoc_path(html_path, nodedoc_path)

    pager = os.environ.get("PAGER", "less")
    cmd = '%s "%s"' % (pager, nodedoc_path)
    return os.system(cmd)

def nodedoc_sections():
    markdown_paths = glob(join(TOP, "doc", "api", "*.markdown"))
    for p in markdown_paths:
        yield os.path.splitext(os.path.basename(p))[0]



#---- other internal support stuff

class _LowerLevelNameFormatter(logging.Formatter):
    def format(self, record):
        record.lowerlevelname = record.levelname.lower()
        return logging.Formatter.format(self, record)

def _setup_logging():
    hdlr = logging.StreamHandler(sys.stdout)
    fmt = "%(name)s: %(lowerlevelname)s: %(message)s"
    fmtr = _LowerLevelNameFormatter(fmt=fmt)
    hdlr.setFormatter(fmtr)
    logging.root.addHandler(hdlr)

class _NoReflowFormatter(optparse.IndentedHelpFormatter):
    """An optparse formatter that does NOT reflow the description."""
    def format_description(self, description):
        return description or ""

def mtime(path):
    return os.stat(path).st_mtime



#---- mainline

def main(argv=sys.argv):
    _setup_logging()
    log.setLevel(logging.INFO)

    # Parse options.
    parser = optparse.OptionParser(prog="nodedoc", usage='',
        version="%prog " + __version__, description=__doc__,
        formatter=_NoReflowFormatter())
    parser.add_option("-v", "--verbose", dest="log_level",
        action="store_const", const=logging.DEBUG,
        help="more verbose output")
    parser.add_option("-q", "--quiet", dest="log_level",
        action="store_const", const=logging.WARNING,
        help="quieter output (just warnings and errors)")
    parser.add_option("-l", "--list", action="store_true",
        help="list all nodedoc sections")
    parser.set_defaults(log_level=logging.INFO)
    opts, sections = parser.parse_args()
    log.setLevel(opts.log_level)

    if opts.list:
        print '\n'.join(nodedoc_sections())
    elif len(sections) == 0:
        parser.print_help()
    elif len(sections) > 1:
        log.error("too many arguments: %s", ' '.join(sections))
    else:
        return nodedoc(sections[0])


## {{{ http://code.activestate.com/recipes/577258/ (r4)
if __name__ == "__main__":
    try:
        retval = main(sys.argv)
    except KeyboardInterrupt:
        sys.exit(1)
    except SystemExit:
        raise
    except:
        import traceback, logging
        if not log.handlers and not logging.root.handlers:
            logging.basicConfig()
        skip_it = False
        exc_info = sys.exc_info()
        if hasattr(exc_info[0], "__name__"):
            exc_class, exc, tb = exc_info
            if isinstance(exc, IOError) and exc.args[0] == 32:
                # Skip 'IOError: [Errno 32] Broken pipe': often a cancelling of `less`.
                skip_it = True
            if not skip_it:
                tb_path, tb_lineno, tb_func = traceback.extract_tb(tb)[-1][:3]
                log.error("%s (%s:%s in %s)", exc_info[1], tb_path,
                    tb_lineno, tb_func)
        else:  # string exception
            log.error(exc_info[0])
        if not skip_it:
            if log.isEnabledFor(logging.DEBUG):
                print()
                traceback.print_exception(*exc_info)
            sys.exit(1)
    else:
        sys.exit(retval)
## end of http://code.activestate.com/recipes/577258/ }}}
