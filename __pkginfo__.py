# Copyright (C) 2018-2022 Rocky Bernstein <rocky@gnu.org>
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
"""decompyle3 packaging information"""

# To the extent possible we make this file look more like a
# configuration file rather than code like setup.py. I find putting
# configuration stuff in the middle of a function call in setup.py,
# which for example requires commas in between parameters, is a little
# less elegant than having it here with reduced code, albeit there
# still is some room for improvement.

# Things that change more often go here.
copyright = """
Copyright (C) 2015-2021 Rocky Bernstein <rb@dustyfeet.com>.
"""

classifiers = [
    "Development Status :: 5 - Production/Stable",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    "Operating System :: OS Independent",
    "Programming Language :: Python :: 3.7",
    "Programming Language :: Python :: 3.8",
    "Topic :: Software Development :: Debuggers",
    "Topic :: Software Development :: Libraries :: Python Modules",
]

# The rest in alphabetic order
author = "Rocky Bernstein, Hartmut Goebel, John Aycock, and others"
author_email = "rb@dustyfeet.com"
entry_points = {
    "console_scripts": [
        "decompyle3=decompyle3.bin.decompile:main_bin",
        "decompyle3-code=decompyle3.bin.decompile_code_type:main",
        "py3disassemble=decompyle3.bin.py3disassemble:main",
    ]
}
ftp_url = None
install_requires = ["click", "spark-parser >= 1.8.9, < 1.9.0", "xdis >= 6.0.4,<6.1.0"]

license = "GPL3"
mailing_list = "python-debugger@googlegroups.com"
modname = "decompyle3"
py_modules = None
short_desc = "Python cross-version byte-code decompiler"
web = "https://github.com/rocky/python-decompile3/"

# tracebacks in zip files are funky and not debuggable
zip_safe = True


import os.path


def get_srcdir():
    filename = os.path.normcase(os.path.dirname(os.path.abspath(__file__)))
    return os.path.realpath(filename)


srcdir = get_srcdir()


def read(*rnames):
    return open(os.path.join(srcdir, *rnames)).read()


# Get info from files; set: long_description and VERSION
long_description = read("README.rst") + "\n"
exec(read("decompyle3/version.py"))
