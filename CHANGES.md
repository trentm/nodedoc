# nodedoc Changelog

## 1.3.2 (not yet released)

(nothing yet)


## 1.3.1

- Fix `nodedoc --version` to report the correct version.


## 1.3.0

- Added v0.10 docs (new default).
- Updated docs to v0.8.22.
- Dropped 0.6 docs.


## 1.2.4

- Add 'doc/versions' to make `nodedoc -h` list the current versions
  accurately.


## 1.2.3

- Update docs to v0.8.8.


## 1.2.2

- <h4>


## 1.2.1

- Drop some cruft files from the updated docs (e.g. all.markdown).


## 1.2.0

- Update to node v0.6.20 and v0.8.5 docs. By default is shows v0.8 docs.
  Use `nodedoc -6 ...` to view the v0.6 docs. Also added '-8' switch to
  be explicit.


## 1.1.2

- Pipe the less (PAGER) to avoid the inclusion of the .nodedoc internal detail
  file in the less session.


## 1.1.1

- [issue #1] Use realpath to find deps and doc files relative to nodedoc
  script.


## 1.1.0

- Add support for searching the node.js doc headers for API method matches,
  e.g. `nodedoc fstat`, `nodedoc spawn`. See the README for more info.


## 1.0.3

- Fix `&gt;`, `&lt;` and `&amp;` escapes.


## 1.0.2

- Use "less -R" if no PAGER is set to not get this warning from less:

        ".../fs.nodedoc" may be a binary file.  See it anyway?


## 1.0.1

- Fix paths for npm-installed nodedoc.


## 1.0.0

First release.
