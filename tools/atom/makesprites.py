#!/usr/bin/env python

"""
Copyright (C) 2012 David Boddie <david@boddie.org.uk>

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

""" Information provided by Kees van Oss:

                 BBC            ATOM
TILES          16 x 24   ->   12 x 16
PLAYER          8 x 24   ->    8 x 16
PROJECTILE      8 x  8   ->    8 x  8
ENEMIES        16 x 16   ->   12 x 12
WEAPONS        16 x 16   ->   12 x 12
TREASURE       16 x 16   ->   12 x 12
EXIT           16 x 24   ->   12 x 16

Hex:    $a0     ,     $80     ,     $aa 
Bin:%10 10 00 00, %10 00 00 00, %10 10 10 10
Col: BL BL GR GR   BL GR GR GR   BL BL BL BL

00 = GR = GREEN, 01 = YE = YELLOW, 10 = BL = BLUE, 11 = RE = RED
"""

import os, sys
import Image

# Map RGB values to the appropriate values for the Atom palette.
palette = {"\x00\x00\x00": 2, "\xff\x00\x00": 3,
           "\x00\x80\x00": 0, "\xff\xff\x00": 2}

if __name__ == "__main__":

    this_dir = os.path.split(os.path.abspath(__file__))[0]
    image_dir = os.path.join(this_dir, os.path.pardir, os.path.pardir, "images", "atom")
    
    sprites = ""
    
    for file_name in os.listdir(image_dir):
    
        if file_name.endswith(".png"):
        
            im = Image.open(os.path.join(image_dir, file_name))
            im = im.convert("RGB")
            data = im.tostring()
            k = 0
            
            sprite = ""
            
            for i in range(im.size[1]):
            
                # Initialise the byte value for insertion into the sprite data.
                byte = 0
                # The offset into the byte for each pixel starts at the highest
                # two bits.
                offset = 6
                
                for j in range(im.size[0]):
                
                    rgb = data[k:k+3]
                    v = palette[rgb]
                    byte = byte | (v << offset)
                    
                    if offset == 0:
                        # For the last pixel in a byte, insert it into the sprite
                        # data, and reset the offset and byte values.
                        sprite += chr(byte)
                        offset = 6
                    else:
                        # Otherwise, decrease the offset into the byte to accept
                        # data for the next pixel.
                        offset -= 2
                    
                    k += 3
                
                if offset != 6:
                    # If the current byte has not been added to the sprite data,
                    # add it now.
                    sprite += chr(byte)
            
            # Add the sprite data to the collection.
            sprites += sprite
    
    # Write the sprite data to a file.
    open("sprites.data", "w").write(sprites)
    
    sys.exit()
