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

from build import *

if __name__ == "__main__":

    if not 1 <= len(sys.argv) <= 3 or "-h" in sys.argv[1:] or "--help" in sys.argv[1:]:
    
        sys.stderr.write("Usage: %s [<code ROM file> <loader ROM file>]\n" % sys.argv[0])
        sys.exit(1)
    
    if len(sys.argv) == 3:
        code_rom_file = sys.argv[1]
        loader_rom_file = sys.argv[2]
    else:
        code_rom_file = "junglecode.rom"
        loader_rom_file = "jungle.rom"
    
    # Memory map (code ROM)
    #
    # 8000 ROM header code
    #      CODE
    # A200 CHARS (0x1280 bytes of character sprites)
    # B480 SPRITES (0x360 bytes of tile sprites)
    # B7E0 space
    #
    # Memory map (loader ROM)
    #
    # 8000 ROM header code
    # 8400 title screen (0x1800 bytes including completion screen)
    
    system("ophis -o " + code_rom_file + " romcode.oph")
    
    romcode = open(code_rom_file, "rb").read()
    
    # Add padding before the data is appended to the code.
    romcode += (0x2200 - len(romcode))*"\x00"
    
    romcode += makesprites.read_sprites(makesprites.chars)
    romcode += makesprites.read_sprites(makesprites.tiles)
    
    # Add padding after the code to make a final image size of 16K.
    romcode += (0x4000 - len(romcode))*"\x00"
    open(code_rom_file, "wb").write(romcode)
    
    system("ophis -o " + loader_rom_file + " romloader.oph")
    
    romdata = open(loader_rom_file, "rb").read()
    
    # Add padding before the data is appended to the loader code.
    romdata += (0x400 - len(romdata))*"\x00"
    
    romdata += makesprites.read_sprites([makesprites.title])
    completed = makesprites.encode(makesprites.read_sprite(makesprites.completed))
    overlay = makesprites.read_sprite(makesprites.overlay)
    combined = makesprites.combine(completed, overlay)
    romdata += combined
    
    romdata += (0x4000 - len(romdata))*"\x00"
    
    open(loader_rom_file, "wb").write(romdata)
    
    # Exit
    sys.exit()
