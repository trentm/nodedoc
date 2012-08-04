A fledgling `perldoc` for node.js.

![nodedoc screenshot](https://raw.github.com/trentm/nodedoc/master/tools/screenshot.png)

To be clear, by "perldoc for node.js" I'm talking about **a tool to view
node.js docs on the command-line**. I am **not** suggesting POD (embedded or
otherwise) or other similar doc format for node.js code.


# Installation

1. Get [node](http://nodejs.org).

2. `npm install -g nodedoc`

You should now have "nodedoc" on your PATH:

    $ nodedoc --version
    nodedoc 1.0.0


# Status

I think this is currently pretty useful. However, it is a quick hack
(Markdown -> HTML -> ANSI escape-colored text, regex for parsing) so
there are some less-than-rigorous limitations. Among them:

- nested lists aren't handled properly
- `<ol>` aren't handled properly



# Usage Examples

List all nodedoc sections:

    $ nodedoc -l
    SECTION          DESCRIPTION
    addons           Addons
    appendix_1       Appendix 1 - Third Party Modules
    assert           Assert
    buffer           Buffer
    child_process    Child Process
    ...

This will render and color the "fs.markdown" core document and page through
it (using your `PAGER` environment setting, if any, else `less -R`):

    $ nodedoc fs
    ... open 'fs' section in PAGER ...

If the given argument is not a section name, it will search all doc headers
(in the node.js docs the headers are typically API names). Here we use '-l'
to explicitly request a list of hits:

    $ nodedoc -l stat
    SECTION          API
    fs               fs.stat(path, [callback])
    fs               fs.lstat(path, [callback])
    fs               fs.fstat(fd, [callback])
    fs               fs.statSync(path)
    fs               fs.lstatSync(path)
    fs               fs.fstatSync(fd)
    fs               Class: fs.Stats
    http             response.writeHead(statusCode, [reasonPhrase], [headers])
    http             response.statusCode
    http             response.statusCode

You can limit the search to a specific section:

    $ nodedoc -l http stat
    http             response.writeHead(statusCode, [reasonPhrase], [headers])
    http             response.statusCode
    http             response.statusCode

If there is a single "exact" match (e.g. here "stat" matches the "fs.stat"
method), then it will automatically open that document to the appropriate
line:

    $ nodedoc stat
    ... open 'fs.stat' section in PAGER ...
    $ nodedoc spawn
    ... open 'child_process.spawn' section in PAGER ...



# TODO

- Find the terminal height in lines and if the *list* output will exceed that
  then page (a la git output).
