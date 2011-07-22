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

sprites = [
        ("0000000000000000",)*24,
        ("0022200000000000",
         "0222220000222200",
         "2222220002222220",
         "2200222022220022",
         "2000022022200000",
         "2000002022200000",
         "0000002202000000",
         "0022202220000220",
         "0222222220022220",
         "0222202220222220",
         "2222002220222200",
         "2220002222222000",
         "2000000222000000",
         "0000220220002220",
         "0002222220022222",
         "0022002220222202",
         "2000000222222000",
         "2200000222200000",
         "0220220222002200",
         "0022220222002222",
         "2222200222022220",
         "2002000222020000",
         "0002000222020000",
         "0002200222200000"),
        ("0333000003330000",
         "3000300330003000",
         "0000033300000333",
         "0000000000000000",
         "0033300000333000",
         "0300330003000300",
         "3000003330000033",
         "0000000000000000",
         "0333000003330000",
         "3000300030003300",
         "0000033300000333",
         "0000000000000000",
         "3330000033300000",
         "0003003300030003",
         "0000333000003330",
         "0000000000000000",
         "0333000003330000",
         "3300300030003000",
         "0000033300000333",
         "0000000000000000",
         "0033300000333000",
         "0300030003300300",
         "3000003330000033",
         "0000000000000000"),
        ("0022000200000000",
         "0002202220002000",
         "0002222200020000",
         "0000220000220000",
         "0000220000022000",
         "0020222000002000",
         "0222022002002200",
         "2222022022200202",
         "0020022222220220",
         "0000002202000200",
         "0000002200002200",
         "0002002200000220",
         "0022222202002200",
         "0222022022002000",
         "0000022002202200",
         "0200022000022000",
         "2220022000220000",
         "0222222020022200",
         "0020222222202020",
         "0000220022020000",
         "0000220000022000",
         "0000220000202000",
         "0000220000002000",
         "0000220000002000")
    ]


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


def read_sprites():

    data = ""
    
    for lines in sprites:
        data += read_sprite(lines)
    
    return data
