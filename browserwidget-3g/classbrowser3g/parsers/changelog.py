# -*- coding: utf-8 -*-

#  Copyright © 2013  B. Clausius <barcc@gmx.de>
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import print_function, division

from . import ClassParserInterface, register_parser


class ChangelogParser (ClassParserInterface):
    def parse(self, doc, location, model):
        uri = location and location.get_uri()
        start, end = doc.get_bounds()
        lines = doc.get_text(start, end, True).splitlines()
        
        for lineno, line in enumerate(lines):
            if not line or line[0].isspace():
                continue
            model.append(None, line, None, uri, lineno+1)
            
            
register_parser(ChangelogParser.__name__, ChangelogParser, ['changelog'], 'Changelog Parser')

