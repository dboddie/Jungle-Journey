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
from tools import makesprites

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
    
    # Memory map
    # 1F00 CODE
    # 3?00 space
    # 3D00 character table (0x24/6 = 6 entries + 1 special entry)
    #   n   type (0 missing, 1 player, 2 projectile, 3 explosion,
    #             4 item,
    #             8 and higher enemy - bits 4,5,6 are enemy type)
    #   n+1 counter/direction
    #       (player: bits 1,2 are direction, bit 0 is animation
    #        projectile: bits 4,5 are direction, bits 1,2 are type,
    #                    bit 0 is animation
    #        enemy:  bits 2,3 are direction, bits 1,0 are animation
    #        emerging, explosion: bits 4,5,6 are enemy type for emerging,
    #                             bit 3 is type 0=emerge,1=explode,
    #                             bits 0,1 are animation
    #        item: bits 0,1,2,3 are type, bit 2 is weapon/treasure
    #              0-3 weapons, 4 key, 5-8 treasure)
    #   n+2 y room offset (0-10)
    #   n+3 dy (0-5)
    #   n+4 x room offset (0-10)
    #   n+5 dx (0-3)
    #
    #   first character is always the player
    #   second character is always the player's weapon
    #   new characters are added after these
    #
    # 3D2A space
    # 3DF0 item/player flags (128=leave level, bits 4,5,6=enemy limit,
    #                         2=player demise, 1=has key)
    # 3DF1 weapon/enemy limit (the highest weapon/enemy possible on a level)
    # 3DF2 current room (i, j)
    # 3DF4 lives (strength)
    # 3DF5 delay counter
    # 3DF6 score (three bytes)
    # 3DF9 projectile type
    # 3DFA level
    # 3DFB palette workspace (enough for one 5 byte palette entry)
    #       3DFD is also projectile counter when in a room
    #       3DFE is also motion counter when in a room
    #       3DFF is also enemy generation counter when in a room
    #
    # 3E00 CHARS (character sprites)
    #       4 * 2 * 0x30 (player movement)
    #           4 * 0x30 (player demise)
    #       4 * 2 * 0x10 (projectile)
    #   5 * 4 * 2 * 0x40 (enemies)          36C0
    #           4 * 0x40 (enemy appear)
    #           4 * 0x40 (enemy demise)
    #           4 * 0x40 (weapons)          42C0
    #           5 * 0x40 (treasure)
    #           2 * 0x60 (exit)             4500
    #           2 * 0x60 (final exit)
    #
    # 4*2*0x30 + 4*0x30 + 4*2*0x10 + 5*4*2*0x40 + 4*0x40 + 4*0x40 + 4*0x40 + 5*0x40 + 2*0x60 + 2*0x60 + 0x3400
    #
    # 5080 space
    # 5100 objects/treasure table (121 entries)
    #   n   type
    #
    # 51F2 space
    # 5200 plot buffer (alternate unplot/plot entries terminating in 255)
    #   n       type
    #   n+1,n+2 source address
    #   n+3,n+4 destination address
    #
    #   5200 and every 12 bytes is unplot entries
    #   5206 and every 12 bytes is plot entries
    #   
    # 5300 SPRITES (map)
    #   3 * (1 * 0x60 (flowers)
    #        1 * 0x60 (tree)
    #        1 * 0x60 (tree))
    # 5780 space
    # 579C room data (generated)
    #   0 blank
    #   1 flowers/decoration
    #   2 tree/wall
    #   3 tree/wall
    #   4 exit
    #   5 open exit
    #   6 final exit (left)
    #   7 final exit (right)
    #
    # 5800 screen memory
    
    files = []
    
    system("ophis mapcode.oph CODE")
    code = open("CODE").read()
    code_start = 0x1f00
    
    addresses = []
    i = 0
    while i < len(code):
        if ord(code[i]) == 0x60:
            if i + 1 < len(code):
                addresses.append(code_start + i + 1)
        i += 1
    
    files.append(("CODE", code_start, code_start, code))
    
    data = makesprites.read_sprites(makesprites.tiles)
    files.append(("SPRITES", 0x5300, 0x5300, data))
    
    data = makesprites.read_sprites(makesprites.chars)
    files.append(("CHARS", 0x3400, 0x3400, data))

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
