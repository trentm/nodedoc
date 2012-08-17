#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""nodedoc -- fledgling perldoc for node.js

Usage:
    nodedoc SECTION         # view a node.js doc section
    nodedoc TERM            # search for matching API methods
    nodedoc SECTION TERM    # search API methods in that section

See <https://github.com/trentm/nodedoc> for more info.
"""

__version_info__ = (1, 2, 3)
__version__ = '.'.join(map(str, __version_info__))
__node_versions__ = list(sorted([(0,6,20), (0,8,5)]))

import re
import sys
import textwrap
import os
from os.path import dirname, join, exists, splitext, basename, realpath
import logging
import codecs
import optparse
import bisect
from glob import glob
from pprint import pprint

TOP = dirname(dirname(realpath(__file__)))
sys.path.insert(0, join(TOP, "deps"))
import markdown2
import appdirs



#---- globals

log = logging.getLogger("nodedoc")
CACHE_DIR = appdirs.user_cache_dir("nodedoc", "trentm")

# Default node version of docs: just the minor ver number (as a string).
DEFAULT_V = str(sorted(__node_versions__)[-1][1])



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

def h4(match):
    """bold red"""
    text = match.group(1)
    text = '\n' + bold(red('#### ' + text))
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
    content = re.compile('<h4>(.*?)</h4>', re.S).sub(h4, content)

    #TODO:XXX special case two adjacent h2's, e.g.:
    #
    #    <h2>fs.utimes(path, atime, mtime, [callback])</h2>
    #
    #    <h2>fs.utimesSync(path, atime, mtime)</h2>
    #
    #    <p>Change file timestamps of the file referenced by the supplied path.</p>

    # HTML escapes
    content = content \
        .replace('&gt;', '>') \
        .replace('&lt;', '<') \
        .replace('&amp;', '&')

    codecs.open(nodedoc_path, 'w', 'utf-8').write(content)

def ensure_nodedoc_built(markdown_path):
    if not exists(markdown_path):
        raise OSError("markdown path does not exist: '%s'" % markdown_path)

    section = splitext(basename(markdown_path))[0]
    html_path = join(CACHE_DIR, section + ".html")
    if not exists(html_path) or mtime(html_path) < mtime(markdown_path):
        generate_html_path(markdown_path, html_path)

    nodedoc_path = join(CACHE_DIR, "%s-%s.nodedoc" % (section, __version__))
    if not exists(nodedoc_path) or mtime(nodedoc_path) < mtime(html_path):
        generate_nodedoc_path(html_path, nodedoc_path)

    return nodedoc_path

def ensure_nodedocs_built(v=DEFAULT_V):
    """Ensure all .nodedoc files are built.

    @param v {str} Is the node version of the docs to build. This is just
        the single minor number digit, e.g. "8"."""
    for markdown_path in glob(join(TOP, "doc", "api"+v, "*.markdown")):
        ensure_nodedoc_built(markdown_path)

def calc_line_start_positions(text):
    line_start_positions = []
    lines = text.splitlines(True)
    pos = 0
    for line in lines:
        line_start_positions.append(pos)
        pos += len(line)
    return line_start_positions


def grep_file(regex, path):
    text = codecs.open(path, 'r', 'utf-8').read()
    line_start_positions = None  # lazily built
    for match in regex.finditer(text):
        if line_start_positions is None:
            line_start_positions = calc_line_start_positions(text)
        start = match.start()
        hit = {
            "path": path,
            "header": match.group("h").strip(),
            "start": start,
            "end": match.end(),
            "line": bisect.bisect_left(line_start_positions, start) + 1
        }
        yield hit

def grep_nodedoc_headers(term, nodedoc_paths=None):
    """Generate hits of the given term in the headers of the given
    nodedoc paths. If no paths are given, search all of them.
    """
    regex = re.compile(r"""
        ^
        (\033\[\d+m)*       # leading ansi escapes
        \#{2,3}             # #'s for h2 or h3
        (?P<h>.*?%s.*?)     # the header text
        (\033\[\d+m)*       # trailing ansi escapes
        $""" % re.escape(term), re.X | re.I | re.M)
    tail = "-%s.nodedoc" % __version__
    if nodedoc_paths is None:
        nodedoc_paths = glob(join(CACHE_DIR, "*" + tail))
    for nodedoc_path in nodedoc_paths:
        for hit in grep_file(regex, nodedoc_path):
            hit["section"] = basename(nodedoc_path[:-len(tail)])
            yield hit

def nodedoc(section, term=None, opts=None, v=DEFAULT_V):
    if term is None:
        # `nodedoc SECTION`
        markdown_path = join(TOP, "doc", "api"+v, section + ".markdown")
        if exists(markdown_path):
            return nodedoc_section(section, v=v)

    if term is not None:
        # `nodedoc SECTION TERM`
        markdown_path = join(TOP, "doc", "api"+v, section + ".markdown")
        if not exists(markdown_path):
            raise Error("no such section: '%s'" % section)
        nodedoc_path = ensure_nodedoc_built(markdown_path)
        hits = list(grep_nodedoc_headers(term, [nodedoc_path]))
    else:
        # `nodedoc TERM`
        term = section
        ensure_nodedocs_built(v=v)
        hits = list(grep_nodedoc_headers(term))

    if len(hits) == 0:
        raise Error("no such section or API method match: '%s'" % section)
    elif len(hits) == 1 and not opts.list:
        return page_nodedoc(hits[0]["path"], hits[0]["line"])
    else:
        exact_hits = []
        if not opts.list:
            # See if this is an "exact" match. If so, and is the only such
            # match, then page it instead of a list of all matches.
            # Re "exact": Take this example:
            #       ## fs.chown(path, uid, gid, [callback])
            # Here "fs.chown" or "chown" would be exact matches. Harder
            # example:
            #       ## assert(value, message), assert.ok(value, [message])
            # Here "ok" is an exact match. Note that "value" and "message"
            # are not exact matches: we care about function names, not args.
            arg_stripper = re.compile("\(.*?\)")
            for hit in hits:
                stripped = arg_stripper.sub("", hit["header"])
                if re.search(r'\b%s\b' % re.escape(term), stripped):
                    exact_hits.append(hit)
                    hit["exact"] = True
            #pprint(exact_hits)

        if len(exact_hits) == 1:
            return page_nodedoc(exact_hits[0]["path"], exact_hits[0]["line"])
        else:
            print "SECTION          API"
            for hit in hits:
                print "%(section)-15s  %(header)s" % hit

def page_nodedoc(path, line=None):
    # TODO: Windows
    pager = os.environ.get("PAGER", "less -R")
    if line:
        cmd = 'cat "%s" 2>/dev/null | %s "+%dG"' % (path, pager, line)
    else:
        cmd = 'cat "%s" 2>/dev/null | %s' % (path, pager)
    return os.system(cmd)

def nodedoc_section(section, v=DEFAULT_V):
    markdown_path = join(TOP, "doc", "api"+v, section + ".markdown")
    if not exists(markdown_path):
        raise Error("no such section: '%s'" % section)
    nodedoc_path = ensure_nodedoc_built(markdown_path)
    return page_nodedoc(nodedoc_path)

def nodedoc_sections(v=DEFAULT_V):
    markdown_paths = glob(join(TOP, "doc", "api"+v, "*.markdown"))
    for p in markdown_paths:
        first_line = codecs.open(p, 'r', 'utf-8').read(1024).split('\n', 1)[0]
        desc = first_line.lstrip(' #')
        yield {"name": splitext(basename(p))[0], "desc": desc}



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
        help="list all nodedoc sections or API hits (if args given)")
    v6 = ".".join(map(str, __node_versions__[0]))
    v8 = ".".join(map(str, __node_versions__[1]))
    vD = ".".join(map(str, __node_versions__[-1]))
    parser.add_option("-6", action="store_const", dest="v", const="6",
        help="use %s docs (default is %s)" % (v6, vD))
    parser.add_option("-8", action="store_const", dest="v", const="8",
        help="use %s docs (default is %s)" % (v8, vD))
    parser.set_defaults(log_level=logging.INFO, v=DEFAULT_V)
    opts, args = parser.parse_args()
    log.setLevel(opts.log_level)

    if not args and opts.list:
        print "SECTION          DESCRIPTION"
        for section in nodedoc_sections(v=opts.v):
            print "%(name)-15s  %(desc)s" % section
    elif len(args) not in (1, 2):
        parser.print_help()
    else:
        return nodedoc(*args, opts=opts, v=opts.v)


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
            if isinstance(exc, Error):
                log.error(exc_info[1])
            elif not skip_it:
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
