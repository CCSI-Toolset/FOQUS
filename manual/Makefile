# A simple Makefile to generate a pdf from LaTeX sources

NAME=FOQUS_User_Manual
CCSI_DOC=../docs/$(NAME).pdf

.PHONY: all clean

all: $(NAME).pdf $(NAME).html

$(NAME).pdf: $(NAME).tex
	pdflatex $(NAME)
	bibtex $(NAME)
	pdflatex $(NAME)
	pdflatex $(NAME)
	cp -pf $(NAME).pdf $(CCSI_DOC)

$(NAME).html: $(NAME).tex
	python makehtml.py

TEMP_FILES = $(NAME).log \
             $(NAME).aux \
             $(NAME).lof \
             $(NAME).out \
             $(NAME).toc \
             $(NAME).4ct \
             $(NAME).4tc \
             $(NAME).bbl \
             $(NAME).blg \
             $(NAME).css \
             $(NAME).dvi \
             $(NAME).idv \
             $(NAME).lg \
             $(NAME).lot \
             $(NAME).tmp \
             $(NAME).xref

clean:
	@rm -rf $(CCSI_DOC) $(NAME).html $(NAME).pdf $(NAME)_HTML.zip $(TEMP_FILES)


