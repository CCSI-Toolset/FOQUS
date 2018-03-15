# A simple makefile for creating the Simulation-Based Optimization
# distribution file

VERSION=$(shell git describe --tags --dirty)
PRODUCT=foqus
LICENSE=LICENSE.md
PACKAGE=CCSI_$(PRODUCT)_$(VERSION).zip

PAYLOAD = docs/*.pdf \
          *.py \
          examples \
          foqus_lib \
          test \
          $(LICENSE)

# OS detection & changes
UNAME := $(shell uname)
ifeq ($(UNAME), Linux)
  MD5BIN=md5sum
endif
ifeq ($(UNAME), Darwin)
  MD5BIN=md5
endif
ifeq ($(UNAME), FreeBSD)
  MD5BIN=md5
endif

.PHONY: all docs dmf clean

all: $(PACKAGE)

# Make zip file without extra file attributes (-X) so md5sum doesn't
# change if the payload hasn't
$(PACKAGE): $(PAYLOAD) docs
	@zip -qXr $(PACKAGE) $(PAYLOAD)
	@$(MD5BIN) $(PACKAGE)

docs:
	@$(MAKE) -C manual

clean:
	@$(MAKE) -C manual clean
	@rm -rf $(PACKAGE) $(DOCDIR) *~
