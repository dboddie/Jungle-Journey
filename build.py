#!/usr/bin/env python

"""
Copyright (C) 2011 David Boddie <david@boddie.org.uk>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, sys
import UEFfile
import makesprites

version = "0.1"

def system(command):

    if os.system(command):
        sys.exit(1)

def read_basic(path):

    t = open(path).read()
    t = t.replace("\n", "\r")
    lines = t.rstrip().split("\r")
    t = "\r".join(lines) + "\r"
    return t


if __name__ == "__main__":

    if len(sys.argv) != 2:
    
        sys.stderr.write("Usage: %s <new UEF file>\n" % sys.argv[0])
        sys.exit(1)
    
    out_uef_file = sys.argv[1]
    
    # Planned memory map
    # 1900 CODE (map)
    # 1x00 space
    # 4E00 character table (256/4 entries)
    #   n   type
    #   n+1 counter/direction
    #   n+2 x position (0-19, top bit 0-1)
    #   n+3 y position (0-27, top bit 0-1)
    # 5000 CHARS (character sprites)
    # 5600 SPRITES (map)
    # 5780 space
    # 579c room data (generated)
    # 5800 screen memory
    
    files = []
    
    system("ophis mapcode.oph CODE")
    code = open("CODE").read()
    code_start = 0x1900
    files.append(("CODE", code_start, code_start, code))
    
    addresses = []
    i = 0
    while i < len(code):
        if ord(code[i]) == 0x60:
            if i + 1 < len(code):
                addresses.append(code_start + i + 1)
        i += 1
    
    data = makesprites.read_sprites(makesprites.chars)
    files.append(("CHARS", 0x5000, 0x5000, data))
    
    data = makesprites.read_sprites(makesprites.tiles)
    files.append(("SPRITES", 0x5600, 0x5600, data))
    
    t = read_basic("LOADER").replace("{addr}", "%X" % addresses[-4])
    
    files.append(("LOADER", 0xffff0e00, 0xffff802b, t))
    
    t = read_basic("TESTSPRITES")
    t = t.replace("{plot0}", "%X" % addresses[-3]
        ).replace("{key_input}", "%X" % addresses[-1]
        ).replace("{plot1}", "%X" % addresses[-2])
    files.append(("TEST", 0xffff0e00, 0xffff802b, t))
    
    u = UEFfile.UEFfile(creator = 'build.py '+version)
    u.minor = 6
    u.import_files(0, files)
    
    # Write the new UEF file.
    try:
        u.write(out_uef_file, write_emulator_info = False)
    except UEFfile.UEFfile_error:
        sys.stderr.write("Couldn't write the new executable to %s.\n" % out_uef_file)
        sys.exit(1)

    # Exit
    sys.exit()
