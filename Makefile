#
# Copyright (c) 2012 Trent Mick
#

all:

.PHONY: cutarelease
cutarelease:
	./tools/cutarelease.py -p nodedoc -f package.json -f bin/nodedoc.py

.PHONY: test
test:
	@echo "No tests yet. :("

