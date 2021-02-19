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

from PIL import Image

tile_size = (16, 24)

blank = Image.new("P", tile_size, 0)
visited = Image.new("P", (tile_size[0]/4, tile_size[1]/4), 1)

def read_xpm(path, symbols = None):

    lines = open(path).readlines()
    char_lines = filter(lambda line: line.startswith('"'), lines)
    strings = map(lambda line: line.strip()[1:-2], char_lines)
    strings[-1] = strings[-1][:-1]
    
    width, height, colours = map(int, strings[0].split()[:3])
    strings = strings[-height:]
    
    if not symbols:
        symbols = [(".", "\x00"), ("+", "\x02"), ("@", "\x03")]

    # Fix the symbol replacement table if necessary.    
    for i in range(len(symbols)):
    
        old, new = symbols[i]
        if 48 <= ord(new) <= 57:
            symbols[i] = (old, chr(ord(new) - 48))
    
    data = []
    
    for s in strings:
    
        for symbol, value in symbols:
            s = s.replace(symbol, value)
        
        data.append(s)
    
    return data

flowers = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/flowers.xpm",
                           [(".", "\x00"), ("@", "\x01"), ("+", "\x02")])))
leaf1 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/leaf1.xpm")))
leaf2 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/leaf2.xpm")))

flowers2 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/flowers2.xpm",
                            [(".", "\x00"), ("@", "\x01"), ("+", "\x02")])))
leaf6 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/leaf6.xpm")))
leaf4 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/leaf4.xpm")))

flowers3 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/flowers3.xpm",
                            [(".", "\x00"), ("@", "\x01"), ("+", "\x02"), ("#", "\x03")])))
leaf5 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/leaf5.xpm")))
leaf3 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/leaf3.xpm")))

exit = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/exit1.xpm",
                        [("+", "\x00"), ("#", "\x01"), (".", "\x02"), ("@", "\x03")])))

final_exit1 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/finalexitl.xpm",
                               [(".", "\x00"), ("#", "\x01"), ("+", "\x02"), ("@", "\x03")])))
final_exit2 = Image.frombytes("P", tile_size, "".join(read_xpm("../../images/finalexitr.xpm",
                               [(".", "\x00"), ("#", "\x01"), ("+", "\x02"), ("@", "\x03")])))

player_size = (8, 24)

player = Image.frombytes("P", player_size, "".join(read_xpm("../../images/down1.xpm")))

item_size = (16, 16)

treasure_images = [
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/weapon1.xpm", [(".", "\x00"), ("+", "\x01"), ("@", "\x03")]))),
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/weapon2.xpm", [(".", "\x00"), ("@", "\x01"), ("+", "\x02")]))),
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/weapon3.xpm", [(".", "\x00"), ("#", "\x01"), ("+", "\x02"), ("@", "\x03")]))),
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/weapon4.xpm", [(".", "\x00"), ("@", "\x01"), ("+", "\x03")]))),

    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/key.xpm", [(".", "\x00"), ("+", "\x01"), ("@", "\x03")]))),
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/chest.xpm", [(".", "\x00"), ("+", "\x01"), ("@", "\x03")]))),
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/statue.xpm", [(".", "\x00"), ("+", "\x02"), ("@", "\x03")]))),
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/jewel.xpm", [(".", "\x00"), ("@", "\x01"), ("+", "\x02"), ("#", "\x03")]))),
    Image.frombytes("P", item_size, "".join(
         read_xpm("../../images/health.xpm", [(".", "\x00"), ("#", "\x01"), ("+", "\x02"), ("@", "\x03")])))
    ]
