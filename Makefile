# A simple makefile for creating the Simulation-Based Optimization
# distribution file

VERSION=2015.03.00
PRODUCT=foqus
LICENSE=CCSI_TE_LICENSE_$(PRODUCT).txt
PACKAGE=CCSI_$(PRODUCT).zip

# Where Jenkins should checkout ^/projects/common/trunk/
COMMON=.ccsi_common
LEGAL_DOCS=LEGAL \
           CCSI_TE_LICENSE.txt

PAYLOAD = docs/*.pdf \
          *.py \
          *.bat \
          *.wxs *.wxi \
          dmf_lib \
          examples \
          foqus_lib \
          setup \
          test \
          turbine_client \
          $(LICENSE)

DMF_LIB_EXCLUDES = dmf_lib/java/src\* \
                   dmf_lib/java/lib\* \
                   dmf_lib/java/bin\* \
                   dmf_lib/java/.ant\* \
                   dmf_lib/java/*.xml

.PHONY: all docs dmf clean

all: $(PACKAGE)

# Make zip file without extra file attributes (-X) so md5sum doesn't
# change if the payload hasn't
$(PACKAGE): $(PAYLOAD) docs dmf
	@zip -qXr $(PACKAGE) $(PAYLOAD) -x $(DMF_LIB_EXCLUDES)
	@md5sum $(PACKAGE)

$(LICENSE): CCSI_TE_LICENSE.txt
	@sed "s/\[SOFTWARE NAME \& VERSION\]/$(PRODUCT) v.$(VERSION)/" < CCSI_TE_LICENSE.txt > $(LICENSE)

$(LEGAL_DOCS):
	@if [ -d $(COMMON) ]; then \
	  cp $(COMMON)/$@ .; \
	else \
	  svn -q export ^/projects/common/trunk/$@; \
	fi

turbine_client:
	@svn -q export ^/projects/turb_client/trunk turbine_client

docs:
	@$(MAKE) -C manual

dmf:
	@cd dmf_lib/java && ant

clean:
	@$(MAKE) -C manual clean
	@cd dmf_lib/java && ant clean
	@if [ -f turbine_client/Makefile ]; then $(MAKE) -C turbine_client clean; fi
	@rm -rf $(PACKAGE) $(LICENSE) $(DOCDIR) $(LEGAL_DOCS) *~
