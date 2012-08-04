#
# Copyright (c) 2012 Trent Mick
#

all:

.PHONY: check
check: check-cruft

# Check for accidental cruft files in doc/api*/ after upgrades.
.PHONY: check-cruft
check-cruft:
	test ! -f doc/api8/index.markdown
	test ! -f doc/api8/_toc.markdown
	test ! -f doc/api8/all.markdown
	test ! -f doc/api6/index.markdown
	test ! -f doc/api6/_toc.markdown
	test ! -f doc/api6/all.markdown

.PHONY: cutarelease
cutarelease: check
	./tools/cutarelease.py -p nodedoc -f package.json -f bin/nodedoc.py

.PHONY: test
test:
	@echo "No tests yet. :("
