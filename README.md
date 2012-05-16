A fledgling `perldoc` for node.js.

# Installation

1. Get [node](http://nodejs.org).

2. `npm install -g nodedoc`

You should now have "nodedoc" on your PATH:

    $ nodedoc --version
    nodedoc 1.0.0

# Status

This really is a quick hack. There are a number of limitations in the current
Markdown -> HTML -> ANSI escape-colored text. Among them:

- nested lists aren't handled properly
- `<ol>` aren't handled properly

The current version of the node.js docs is a snapshot of the
<https://github.com/joyent/node> master.


# Examples

This will render and color the fs.markdown core docs and page through them
(using your `PAGER` environment setting, if any):

    $ nodedoc fs

List all nodedoc sections:

    $ nodedoc -l


# TODO

- Some way to not have to re-release nodedoc for a new node release. Perhaps
  support multiple versions of the node docs and perhaps have a `nodedoc
  --update` to pull in recent release docs.
