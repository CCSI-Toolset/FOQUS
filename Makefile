# A simple makefile for creating the Simulation-Based Optimization
# distribution file

VERSION=$(shell git describe --tags --dirty)
PRODUCT=foqus
LICENSE=LICENSE.md
PACKAGE=CCSI_$(PRODUCT)_$(VERSION).zip

PAYLOAD = docs/*.pdf \
          *.py \
          *.bat \
          *.wxs *.wxi \
          dmf_lib \
          examples \
          foqus_lib \
          setup \
          test \
          turb_client \
          $(LICENSE)

DMF_LIB_EXCLUDES = dmf_lib/java/src\* \
                   dmf_lib/java/lib\* \
                   dmf_lib/java/bin\* \
                   dmf_lib/java/.ant\* \
                   dmf_lib/java/*.xml

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
$(PACKAGE): $(PAYLOAD) docs dmf
	@zip -qXr $(PACKAGE) $(PAYLOAD) -x $(DMF_LIB_EXCLUDES)
	@$(MD5BIN) $(PACKAGE)

docs:
	@$(MAKE) -C manual

dmf:
	@cd dmf_lib/java && ant

clean:
	@$(MAKE) -C manual clean
	@cd dmf_lib/java && ant clean
	@if [ -f turb_client/Makefile ]; then $(MAKE) -C turb_client clean; fi
	@rm -rf $(PACKAGE) $(DOCDIR) *~
