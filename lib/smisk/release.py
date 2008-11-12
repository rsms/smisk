'''Release information.
'''
__all__ = ['version','author','email','copyright','license','version_info']

version = "1.1.0" # Major.Minor.Build (see tag_build in setup.cfg)
author = "Rasmus Andersson"
email = "rasmus@flajm.com"
copyright = "Copyright 2007-2008 Rasmus Andersson and contributors"
license = r'''Copyright (c) 2007-2008 Rasmus Andersson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.'''

import re
version_info = list(re.match(r'([0-9]+)\.([0-9]+)(?:\.([0-9]+)|)(.*)', version).groups())
if version_info[2] is None:
  version_info[2] = '0'
version_info = tuple(version_info)
