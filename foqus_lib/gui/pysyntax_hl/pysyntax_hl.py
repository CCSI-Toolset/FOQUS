"""
Python syntax highlighter

This is based on the example code at:
https://wiki.python.org/moin/PyQt/Python%20syntax%20highlighting
from May 8, 2015
"""

import sys
from PyQt5.QtCore import QRegExp
from PyQt5.QtGui import QColor, QTextCharFormat, QFont, QSyntaxHighlighter

def format(color, style=''):
    """Return a QTextCharFormat with the given attributes.
    """
    _color = QColor()
    _color.setNamedColor(color)

    _format = QTextCharFormat()
    _format.setForeground(_color)
    if 'bold' in style:
        _format.setFontWeight(QFont.Bold)
    if 'italic' in style:
        _format.setFontItalic(True)
    return _format

# Syntax styles that can be shared by all languages
STYLES = {
    'keyword': format('blue'),
    'brace': format('darkGray'),
    'defclass': format('black', 'bold'),
    'string': format('darkOrange'),
    'string2': format('orange'),
    'comment': format('red', 'italic'),
    'self': format('black', 'italic'),
    'numbers': format('darkGreen'),
    'function': format('darkRed', 'bold'),
}

#class BlockData(QTextBlockUserData):
#    def __init__(self):
        # indexes
        # { = 1
        # [ = 2
        # ( = 3

#        openBrace = [[], [], []]
#        closeBrace = [[], [], []]

class PythonHighlighter (QSyntaxHighlighter):
    """Syntax highlighter for the Python language.
    """
    # Python keywords
    keywords = [
        'and', 'assert', 'break', 'class', 'continue', 'def',
        'del', 'elif', 'else', 'except', 'exec', 'finally',
        'for', 'from', 'global', 'if', 'import', 'in',
        'is', 'lambda', 'not', 'or', 'pass', 'print',
        'raise', 'return', 'try', 'while', 'yield',
        'None', 'True', 'False']
    # Python builtin functions
    functions = [
        'abs', 'divmod', 'input', 'open', 'staticmethod', 'all',
        'enumerate', 'int', 'ord', 'str', 'any', 'eval', 'isinstance',
        'pow', 'sum', 'basestring', 'execfile', 'issubclass', 'print',
        'super', 'bin', 'file', 'iter', 'property', 'tuple', 'bool',
        'filter', 'len', 'range', 'type', 'bytearray', 'float', 'list',
        'raw_input', 'unichr', 'callable', 'format', 'locals', 'reduce',
        'unicode', 'chr', 'frozenset', 'long', 'reload', 'vars',
        'classmethod', 'getattr', 'map', 'repr', 'xrange', 'cmp',
        'globals', 'max', 'reversed', 'zip', 'compile', 'hasattr',
        'memoryview', 'round', '__import__', 'complex', 'hash', 'min',
        'set', 'delattr', 'help', 'next', 'setattr', 'dict', 'hex',
        'object', 'slice', 'dir', 'id', 'oct', 'sorted']
    # Python braces
    obraces = ['\{', '\(', '\[']
    cbraces = ['\}', '\)', '\]']

    def __init__(self, document):
        QSyntaxHighlighter.__init__(self, document)
        # Multi-line strings (expression, flag, style)
        # FIXME: The triple-quotes in these two lines will mess up the
        # syntax highlighting from this point onward
        self.tri_single = (QRegExp("'''"), 1, STYLES['string2'])
        self.tri_double = (QRegExp('"""'), 2, STYLES['string2'])
        obraceRules = [(r'%s' % b, 0, STYLES['brace'])
            for b in PythonHighlighter.obraces]
        cbraceRules = [(r'%s' % b, 0, STYLES['brace'])
            for b in PythonHighlighter.cbraces]
        rules = []
        # Keyword, operator, and brace rules
        rules += [(r'\b%s\b' %f, 0, STYLES['function'])
            for f in PythonHighlighter.functions]
        rules += [(r'\b%s\b' % w, 0, STYLES['keyword'])
            for w in PythonHighlighter.keywords]
        # All other rules
        rules += [
            # 'self'
            (r'\bself\b', 0, STYLES['self']),

            # Double-quoted string, possibly containing escape sequences
            (r'"[^"\\]*(\\.[^"\\]*)*"', 0, STYLES['string']),
            # Single-quoted string, possibly containing escape sequences
            (r"'[^'\\]*(\\.[^'\\]*)*'", 0, STYLES['string']),

            # 'def' followed by an identifier
            (r'\bdef\b\s*(\w+)', 1, STYLES['defclass']),
            # 'class' followed by an identifier
            (r'\bclass\b\s*(\w+)', 1, STYLES['defclass']),

            # From '#' until a newline
            (r'#[^\n]*', 0, STYLES['comment']),

            # Numeric literals
            (r'\b[0-9]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b0[xX][0-9A-Fa-f]+[lL]?\b', 0, STYLES['numbers']),
            (r'\b[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?\b', 0, STYLES['numbers']),
        ]

        # Build a QRegExp for each pattern
        self.rules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in rules]
        self.obraceRules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in obraceRules]
        self.cbraceRules = [(QRegExp(pat), index, fmt)
            for (pat, index, fmt) in cbraceRules]

    def highlightBlock(self, text):
        """Apply syntax highlighting to the given block of text.
        """
        # Opening braces also waht to keep track of location for
        # matching sets
        for expression, nth, format in self.obraceRules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                #print "{0}, {1}, {2}".format(index, length, nth)
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        # Closing braces also waht to keep track of location for
        # matching sets
        for expression, nth, format in self.cbraceRules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        # Do other syntax formatting
        for expression, nth, format in self.rules:
            index = expression.indexIn(text, 0)
            while index >= 0:
                # We actually want the index of the nth match
                index = expression.pos(nth)
                length = len(expression.cap(nth))
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)
        self.setCurrentBlockState(0)

        # Do multi-line strings
        in_multiline = self.match_multiline(text, *self.tri_single)
        if not in_multiline:
            in_multiline = self.match_multiline(text, *self.tri_double)

    def match_multiline(self, text, delimiter, in_state, style):
        """Do highlighting of multi-line strings. ``delimiter`` should be a
        ``QRegExp`` for triple-single-quotes or triple-double-quotes, and
        ``in_state`` should be a unique integer to represent the corresponding
        state changes when inside those strings. Returns True if we're still
        inside a multi-line string when this function is finished.
        """
        # If inside triple-single quotes, start at 0
        if self.previousBlockState() == in_state:
            start = 0
            add = 0
        # Otherwise, look for the delimiter on this line
        else:
            start = delimiter.indexIn(text)
            # Move past this match
            add = delimiter.matchedLength()

        # As long as there's a delimiter match on this line...
        while start >= 0:
            # Look for the ending delimiter
            end = delimiter.indexIn(text, start + add)
            # Ending delimiter on this line?
            if end >= add:
                length = end - start + add + delimiter.matchedLength()
                self.setCurrentBlockState(0)
            # No; multi-line string
            else:
                self.setCurrentBlockState(in_state)
                length = len(text) - start + add
            # Apply formatting
            self.setFormat(start, length, style)
            # Look for the next match
            start = delimiter.indexIn(text, start + length)

        # Return True if still inside a multi-line string, False otherwise
        if self.currentBlockState() == in_state:
            return True
        else:
            return False
