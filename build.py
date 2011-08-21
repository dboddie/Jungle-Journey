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
    # 3300 character table (0x24/6 = 6 entries)
    #   n   type (0 missing, 1 player, 2 projectile, 3 explosion,
    #             4 and higher enemy - bits 3,4,5 are enemy type)
    #   n+1 counter/direction
    #       (player: bits 1,2 are direction, bit 0 is animation
    #        enemy:  bits 2,3 are direction, bits 1,0 are animation
    #        emerging, explosion: bits 4,5,6 are enemy type for emerging,
    #                             bit 3 is type 0=emerge,1=explode,
    #                             bits 0,1 are animation)
    #   n+2 y room offset (0-10)
    #   n+3 dy (0-5)
    #   n+4 x room offset (0-10)
    #   n+5 dx (0-3)
    #
    #   first character is always the player
    #   second character is always the player's weapon
    #   new characters are added after these
    #
    # 3324 objects/treasure table (0xB4/5 = 36 entries)
    #   n   type
    #   n+1 i map offset
    #   n+2 j map offset
    #   n+3 y room offset
    #   n+4 x room offset
    #
    # 33F0 starting room (i, j)
    # 33F2 current room (i, j)
    # 33F4 lives
    # 33F6 score (four bytes)
    # 33FA level
    # 33FB palette workspace (enough for one 5 byte palette entry)
    #       33FE is also motion counter when in a room
    #       33FF is also enemy generation counter when in a room
    #
    # 3400 CHARS (character sprites)
    #       4 * 2 * 0x30 (player movement)
    #           4 * 0x30 (player demise)
    #       4 * 2 * 0x10 (projectile)
    #           4 * 0x10 (projectile explode)
    #   5 * 4 * 2 * 0x40 (enemies)          3700
    #           4 * 0x40 (enemy appear)
    #           4 * 0x40 (enemy demise)
    #           4 * 0x40 (weapons)
    #           4 * 0x40 (treasure)
    #           2 * 0x40 (exit)
    #           2 * 0x40 (final exit)
    #
    # 4*2*0x30 + 4*0x30 + 4*2*0x10 + 4*0x10 + 5*4*2*0x40 + 4*0x40 + 4*0x40 + 4*0x40 + 4*0x40 + 2*0x40 + 2*0x40 + 0x3400
    #
    # 4600 space
    # 4700 plot buffer (alternate unplot/plot entries terminating in 255)
    #   n       type
    #   n+1,n+2 source address
    #   n+3,n+4 destination address
    #
    #   4700 and every 12 bytes is unplot entries
    #   4706 and every 12 bytes is plot entries
    #   
    # 5300 SPRITES (map)
    # 5780 space
    # 579c room data (generated)
    # 5800 screen memory
    
    files = []
    
    system("ophis mapcode.oph CODE")
    code = open("CODE").read()
    code_start = 0x1900
    
    addresses = []
    i = 0
    while i < len(code):
        if ord(code[i]) == 0x60:
            if i + 1 < len(code):
                addresses.append(code_start + i + 1)
        i += 1
    
    files.append(("CODE", code_start, addresses[-1], code))
    
    data = makesprites.read_sprites(makesprites.chars)
    files.append(("CHARS", 0x3400, 0x3400, data))
    
    data = makesprites.read_sprites(makesprites.tiles)
    files.append(("SPRITES", 0x5300, 0x5300, data))
    
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
