# -*- coding: utf-8 -*-
'''
Smarty extension for Python-Markdown
====================================

Adds conversion of ASCII dashes, quotes and ellipses to their HTML
entity equivalents.

See <https://pythonhosted.org/Markdown/extensions/smarty.html>
for documentation.

Author: 2013, Dmitry Shachnev <mitya57@gmail.com>

All changes Copyright 2013-2014 The Python Markdown Project

License: [BSD](http://www.opensource.org/licenses/bsd-license.php)

SmartyPants license:

   Copyright (c) 2003 John Gruber <http://daringfireball.net/>
   All rights reserved.

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are
   met:

   *  Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

   *  Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in
      the documentation and/or other materials provided with the
      distribution.

   *  Neither the name "SmartyPants" nor the names of its contributors
      may be used to endorse or promote products derived from this
      software without specific prior written permission.

   This software is provided by the copyright holders and contributors "as
   is" and any express or implied warranties, including, but not limited
   to, the implied warranties of merchantability and fitness for a
   particular purpose are disclaimed. In no event shall the copyright
   owner or contributors be liable for any direct, indirect, incidental,
   special, exemplary, or consequential damages (including, but not
   limited to, procurement of substitute goods or services; loss of use,
   data, or profits; or business interruption) however caused and on any
   theory of liability, whether in contract, strict liability, or tort
   (including negligence or otherwise) arising in any way out of the use
   of this software, even if advised of the possibility of such damage.


smartypants.py license:

   smartypants.py is a derivative work of SmartyPants.
   Copyright (c) 2004, 2007 Chad Miller <http://web.chad.org/>

   Redistribution and use in source and binary forms, with or without
   modification, are permitted provided that the following conditions are
   met:

   *  Redistributions of source code must retain the above copyright
      notice, this list of conditions and the following disclaimer.

   *  Redistributions in binary form must reproduce the above copyright
      notice, this list of conditions and the following disclaimer in
      the documentation and/or other materials provided with the
      distribution.

   This software is provided by the copyright holders and contributors "as
   is" and any express or implied warranties, including, but not limited
   to, the implied warranties of merchantability and fitness for a
   particular purpose are disclaimed. In no event shall the copyright
   owner or contributors be liable for any direct, indirect, incidental,
   special, exemplary, or consequential damages (including, but not
   limited to, procurement of substitute goods or services; loss of use,
   data, or profits; or business interruption) however caused and on any
   theory of liability, whether in contract, strict liability, or tort
   (including negligence or otherwise) arising in any way out of the use
   of this software, even if advised of the possibility of such damage.

'''


from __future__ import unicode_literals
from . import Extension
from ..inlinepatterns import HtmlPattern, HTML_RE
from ..treeprocessors import InlineProcessor
from ..util import Registry


# Constants for quote education.
punctClass = r"""[!"#\$\%'()*+,-.\/:;<=>?\@\[\\\]\^_`{|}~]"""
endOfWordClass = r"[\s.,;:!?)]"
closeClass = "[^\ \t\r\n\[\{\(\-\u0002\u0003]"

openingQuotesBase = (
    '(\s'               # a  whitespace char
    '|&nbsp;'           # or a non-breaking space entity
    '|--'               # or dashes
    '|–|—'              # or unicode
    '|&[mn]dash;'       # or named dash entities
    '|&#8211;|&#8212;'  # or decimal entities
    ')'
)

substitutions = {
    'mdash': '&mdash;',
    'ndash': '&ndash;',
    'ellipsis': '&hellip;',
    'left-angle-quote': '&laquo;',
    'right-angle-quote': '&raquo;',
    'left-single-quote': '&lsquo;',
    'right-single-quote': '&rsquo;',
    'left-double-quote': '&ldquo;',
    'right-double-quote': '&rdquo;',
}


# Special case if the very first character is a quote
# followed by punctuation at a non-word-break. Close the quotes by brute force:
singleQuoteStartRe = r"^'(?=%s\B)" % punctClass
doubleQuoteStartRe = r'^"(?=%s\B)' % punctClass

# Special case for double sets of quotes, e.g.:
#   <p>He said, "'Quoted' words in a larger quote."</p>
doubleQuoteSetsRe = r""""'(?=\w)"""
singleQuoteSetsRe = r"""'"(?=\w)"""

# Special case for decade abbreviations (the '80s):
decadeAbbrRe = r"(?<!\w)'(?=\d{2}s)"

# Get most opening double quotes:
openingDoubleQuotesRegex = r'%s"(?=\w)' % openingQuotesBase

# Double closing quotes:
closingDoubleQuotesRegex = r'"(?=\s)'
closingDoubleQuotesRegex2 = '(?<=%s)"' % closeClass

# Get most opening single quotes:
openingSingleQuotesRegex = r"%s'(?=\w)" % openingQuotesBase

# Single closing quotes:
closingSingleQuotesRegex = r"(?<=%s)'(?!\s|s\b|\d)" % closeClass
closingSingleQuotesRegex2 = r"(?<=%s)'(\s|s\b)" % closeClass

# All remaining quotes should be opening ones
remainingSingleQuotesRegex = "'"
remainingDoubleQuotesRegex = '"'

HTML_STRICT_RE = HTML_RE + r'(?!\>)'


class SubstituteTextPattern(HtmlPattern):
    def __init__(self, pattern, replace, md):
        """ Replaces matches with some text. """
        HtmlPattern.__init__(self, pattern)
        self.replace = replace
        self.md = md

    def handleMatch(self, m):
        result = ''
        for part in self.replace:
            if isinstance(part, int):
                result += m.group(part)
            else:
                result += self.md.htmlStash.store(part)
        return result


class SmartyExtension(Extension):
    def __init__(self, **kwargs):
        self.config = {
            'smart_quotes': [True, 'Educate quotes'],
            'smart_angled_quotes': [False, 'Educate angled quotes'],
            'smart_dashes': [True, 'Educate dashes'],
            'smart_ellipses': [True, 'Educate ellipses'],
            'substitutions': [{}, 'Overwrite default substitutions'],
        }
        super(SmartyExtension, self).__init__(**kwargs)
        self.substitutions = dict(substitutions)
        self.substitutions.update(self.getConfig('substitutions', default={}))

    def _addPatterns(self, md, patterns, serie, priority):
        for ind, pattern in enumerate(patterns):
            pattern += (md,)
            pattern = SubstituteTextPattern(*pattern)
            name = 'smarty-%s-%d' % (serie, ind)
            self.inlinePatterns.register(pattern, name, priority-ind)

    def educateDashes(self, md):
        emDashesPattern = SubstituteTextPattern(
            r'(?<!-)---(?!-)', (self.substitutions['mdash'],), md
        )
        enDashesPattern = SubstituteTextPattern(
            r'(?<!-)--(?!-)', (self.substitutions['ndash'],), md
        )
        self.inlinePatterns.register(emDashesPattern, 'smarty-em-dashes', 50)
        self.inlinePatterns.register(enDashesPattern, 'smarty-en-dashes', 45)

    def educateEllipses(self, md):
        ellipsesPattern = SubstituteTextPattern(
            r'(?<!\.)\.{3}(?!\.)', (self.substitutions['ellipsis'],), md
        )
        self.inlinePatterns.register(ellipsesPattern, 'smarty-ellipses', 10)

    def educateAngledQuotes(self, md):
        leftAngledQuotePattern = SubstituteTextPattern(
            r'\<\<', (self.substitutions['left-angle-quote'],), md
        )
        rightAngledQuotePattern = SubstituteTextPattern(
            r'\>\>', (self.substitutions['right-angle-quote'],), md
        )
        self.inlinePatterns.register(leftAngledQuotePattern, 'smarty-left-angle-quotes', 40)
        self.inlinePatterns.register(rightAngledQuotePattern, 'smarty-right-angle-quotes', 35)

    def educateQuotes(self, md):
        lsquo = self.substitutions['left-single-quote']
        rsquo = self.substitutions['right-single-quote']
        ldquo = self.substitutions['left-double-quote']
        rdquo = self.substitutions['right-double-quote']
        patterns = (
            (singleQuoteStartRe, (rsquo,)),
            (doubleQuoteStartRe, (rdquo,)),
            (doubleQuoteSetsRe, (ldquo + lsquo,)),
            (singleQuoteSetsRe, (lsquo + ldquo,)),
            (decadeAbbrRe, (rsquo,)),
            (openingSingleQuotesRegex, (2, lsquo)),
            (closingSingleQuotesRegex, (rsquo,)),
            (closingSingleQuotesRegex2, (rsquo, 2)),
            (remainingSingleQuotesRegex, (lsquo,)),
            (openingDoubleQuotesRegex, (2, ldquo)),
            (closingDoubleQuotesRegex, (rdquo,)),
            (closingDoubleQuotesRegex2, (rdquo,)),
            (remainingDoubleQuotesRegex, (ldquo,))
        )
        self._addPatterns(md, patterns, 'quotes', 30)

    def extendMarkdown(self, md):
        configs = self.getConfigs()
        self.inlinePatterns = Registry()
        if configs['smart_ellipses']:
            self.educateEllipses(md)
        if configs['smart_quotes']:
            self.educateQuotes(md)
        if configs['smart_angled_quotes']:
            self.educateAngledQuotes(md)
            # Override HTML_RE from inlinepatterns.py so that it does not
            # process tags with duplicate closing quotes.
            md.inlinePatterns.register(HtmlPattern(HTML_STRICT_RE, md), 'html', 90)
        if configs['smart_dashes']:
            self.educateDashes(md)
        inlineProcessor = InlineProcessor(md)
        inlineProcessor.inlinePatterns = self.inlinePatterns
        md.treeprocessors.register(inlineProcessor, 'smarty', 2)
        md.ESCAPED_CHARS.extend(['"', "'"])


def makeExtension(*args, **kwargs):
    return SmartyExtension(*args, **kwargs)
