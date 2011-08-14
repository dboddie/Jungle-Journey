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

def read_xpm(path, symbols = None):

    lines = open(path).readlines()
    char_lines = filter(lambda line: line.startswith('"'), lines)
    strings = map(lambda line: line.strip()[1:-2], char_lines)
    strings[-1] = strings[-1][:-1]
    
    width, height, colours = map(int, strings[0].split()[:3])
    strings = strings[-height:]
    
    if not symbols:
        symbols = [(".", 0), ("+", 2), ("@", 3)]
    
    data = []
    
    for s in strings:
    
        for symbol, value in symbols:
            s = s.replace(symbol, str(value))
        
        data.append(s)
    
    return data


tiles = [read_xpm("images/flowers.xpm", [(".", "0"), ("@", "1"), ("+", "2")]),
         read_xpm("images/leaf1.xpm"),
         read_xpm("images/leaf2.xpm"),
         read_xpm("images/stones.xpm", [(".", "2"), ("#", "1"), ("+", "0"), ("@", "3")]),
         read_xpm("images/rock1.xpm"),
         read_xpm("images/rock2.xpm", [(" ", "0"), ("#", "1"), ("@", "2"), ("+", "3")]),
         read_xpm("images/bricks.xpm", [(".", "0"), ("#", "1"), ("+", "2"), ("@", "3")]),
         read_xpm("images/wall1.xpm"),
         read_xpm("images/wall2.xpm")]

chars = [read_xpm("images/left1.xpm"),
         read_xpm("images/left2.xpm"),
         read_xpm("images/right1.xpm"),
         read_xpm("images/right2.xpm"),
         read_xpm("images/up1.xpm"),
         read_xpm("images/up2.xpm"),
         read_xpm("images/down1.xpm"),
         read_xpm("images/down2.xpm")]


def read_sprite(lines):

    data = ""
    
    # Read 8 rows at a time.
    for row in range(0, len(lines), 8):

        # Read 4 columns at a time.
        for column in range(0, len(lines[0]), 4):

            # Read the rows.
            for line in lines[row:row + 8]:

                shift = 3
                byte = 0
                for pixel in line[column:column + 4]:

                    if pixel == "1":
                        byte = byte | (0x01 << shift)
                    elif pixel == "2":
                        byte = byte | (0x10 << shift)
                    elif pixel == "3":
                        byte = byte | (0x11 << shift)

                    shift -= 1

                data += chr(byte)
    
    return data


def read_sprites(sprites):

    data = ""
    
    for lines in sprites:
        data += read_sprite(lines)
    
    return data
