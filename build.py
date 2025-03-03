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

import os, struct, sys
import UEFfile
from tools import makedfs, makesprites

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

def encode_text(text):

    words = text.split(" ")
    word_dict = {}
    
    # Count the number of occurrences of each word.
    for word in words:
        word_dict.setdefault(word, 0)
        word_dict[word] += 1
    
    # Sort the words in order of decreasing frequency.
    frequencies = map(lambda x: (x[1], x[0]), word_dict.items())
    frequencies.sort()
    frequencies.reverse()
    
    # Create encoding and decoding look up tables.
    decoding_lookup = {}
    encoding_lookup = {}
    
    i = 0
    for count, word in frequencies:
    
        if i >= 128:
            j = 1 + i * 2
        else:
            j = i * 2
        
        encoding_lookup[word] = j
        decoding_lookup[j] = word
        
        i += 1
    
    # Encode the text.
    encoded = []
    for word in words:
    
        encoded.append(encoding_lookup[word])
    
    encoded_string = ""
    for value in encoded:
    
        if value & 1 == 0:
            encoded_string += chr(value)
        else:
            encoded_string += struct.pack("<H", value)
    
    return decoding_lookup, encoded_string

def decode_text(data, lookup):

    words = ""
    i = 0
    while i < len(data):
    
        value = ord(data[i])
        if value & 1 != 0:
            value += ord(data[i+1]) << 8
            i += 2
        else:
            i += 1
        
        words += lookup[value]
        words += " "
    
    return words[:-1]

def build_uef(files):

    u = UEFfile.UEFfile(creator = 'build.py '+version)
    u.minor = 6
    u.target_machine = "Electron"
    
    u.import_files(0, files)
    
    # Insert a gap before each file.
    offset = 0
    for f in u.contents:
    
        # Insert a gap and some padding before the file.
        gap_padding = [(0x112, "\xdc\x05"), (0x110, "\xdc\x05"), (0x100, "\xdc")]
        u.chunks = u.chunks[:f["position"] + offset] + \
                   gap_padding + u.chunks[f["position"] + offset:]

        # Each time we insert a gap, the position of the file changes, so we
        # need to update its position and last position. This isn't really
        # necessary because we won't read the contents list again.
        offset += len(gap_padding)
        f["position"] += offset
        f["last position"] += offset

    u.chunks += [(0x110, "\xdc\x05")]

    return u


if __name__ == "__main__":

    args = sys.argv[:]
    
    # Quiet mode turns off sound while loading and hides text. This is useful
    # when reusing the cassette version in a ROM image.
    quiet = "-q" in args
    if quiet:
        args.remove("-q")

    if len(args) != 2:
    
        sys.stderr.write("Usage: %s <new UEF file>\n" % sys.argv[0])
        sys.exit(1)
    
    out_uef_file = args[1]
    
    # Memory map
    # 0EE0 enemy x locations in the current room
    # 0EF0 enemy x locations in the current room
    # 0F00 completion screen
    # 1800 title screen
    # 1E00 CODE
    #
    # 3F00 CHARS (character sprites)
    #       4 * 2 * 0x30 (player movement)
    #           4 * 0x30 (player demise)
    #       4 * 2 * 0x10 (projectile)
    #   5 * 4 * 2 * 0x40 (enemies)          41C0
    #           4 * 0x40 (enemy appear)
    #           4 * 0x40 (enemy demise)
    #           4 * 0x40 (weapons)          4dC0
    #           5 * 0x40 (treasure)
    #           2 * 0x60 (exit)             5000
    #           2 * 0x60 (final exit)
    #
    # 0x3f00 + 4*2*0x30 + 4*0x30 + 4*2*0x10 + 5*4*2*0x40 + 4*0x40 + 4*0x40 + 4*0x40 + 5*0x40 + 2*0x60 + 2*0x60
    #
    # 5180 high scores (8 * 12 = 0xe0)
    #   n   3 bytes score + 9 bytes ASCII
    #
    # 5200 objects/treasure table (121 entries)
    #   n   type
    #
    # 5279 space
    # 5280 character table (0x24/6 = 6 entries + 1 special entry)
    #   n   type (0 missing, 1 player, 2 projectile, 3 explosion,
    #             4 item,
    #             8 and higher enemy - bits 4,5,6 are enemy type)
    #   n+1 counter/direction
    #       (player: bits 1,2 are direction, bit 0 is animation
    #        projectile: bits 4,5 are direction, bits 1,2 are type,
    #                    bit 0 is animation
    #        enemy:  bits 2,3 are direction, bits 1,0 are animation
    #                bits 4,5,6,7 are counter for non-homing enemies
    #        emerging, explosion: bits 4,5,6 are enemy type for emerging,
    #                             bit 2 is type 0=emerge,1=explode,
    #                             bits 0,1 are animation
    #        item: bits 0,1,2,3 are type, bit 2 is weapon/treasure
    #              0-3 weapons, 4 key, 5-8 treasure)
    #   n+2 y room offset (0-10)
    #   n+3 dy (0-3)
    #   n+4 x room offset (0-10)
    #   n+5 dx (0-3)
    #
    #   first character is always the player
    #   second character is always the player's weapon
    #   new characters are added after these
    #
    # 5300 plot buffer (alternate unplot/plot entries terminating in 255)
    #   n       type
    #   n+1,n+2 source address
    #   n+3,n+4 destination address
    #
    #   5300 and every 12 bytes is unplot entries
    #   5306 and every 12 bytes is plot entries
    #
    # 53C0 space (assuming 8 unplot and 8 plot operations)
    #
    # 5400 SPRITES (map)
    #   3 * (1 * 0x60 (flowers)
    #        1 * 0x60 (tree)
    #        1 * 0x60 (tree))
    #
    # 5760 note data (8 bytes)
    #
    # 577E joystick support (0=off; 1=on)
    # 577F weapon counter (0=fire one subtile below; 1=fire two subtiles below)
    # 5780 item/player flags (128=leave level, 64=player demise,
    #                         bits 4,5,6=enemy limit, 2=complete game,
    #                         1=has key)
    # 5781 weapon/enemy limit (the highest weapon/enemy possible on a level)
    # 5782 current room (i, j)
    # 5784 lives (strength)
    # 5785 delay counter
    # 5786 score (three bytes)
    # 5789 projectile type
    # 578A level
    # 578B palette workspace (enough for one 5 byte palette entry)
    #       578D is also projectile counter when in a room
    #       578E is also motion counter when in a room
    #       578F is also enemy generation counter when in a room
    #
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

    files.append(("RETRO", 0x1900, 0x8023, open("resources/loader_U5D", "rb").read()))
    
    # Prepare any code to be included before and after loading.
    preload = postload = ""
    
    if quiet:
        preload = (
            "lda #210\n"
            "ldx #1\n"      # disable sound
            "ldy #0\n"
            "jsr $fff4\n"
            "lda #17\n"
            "jsr $ffee\n"
            "lda #0\n"      # COLOUR 0
            "jsr $ffee\n"
            )
        postload = (
            "lda #210\n"
            "ldx #0\n"      # enable sound
            "ldy #0\n"
            "jsr $fff4\n"
            )
    
    open("preload.oph", "w").write(preload)
    open("postload.oph", "w").write(postload)
    
    system("ophis loader.oph -o JUNGLE")
    code = open("JUNGLE").read()
    code_start = 0x5180
    files.append(("JUNGLE", code_start, code_start, code))
    
    data = makesprites.read_sprites([makesprites.title])
    completed = makesprites.encode(makesprites.read_sprite(makesprites.completed))
    overlay = makesprites.read_sprite(makesprites.overlay)
    combined = makesprites.combine(completed, overlay)
    data += combined
    files.append(("TITLE", 0x5AA0, 0x5AA0, data))

    data = makesprites.read_sprites(makesprites.tiles)
    files.append(("SPRITES", 0x5400, 0x5400, data))
    
    data = makesprites.read_sprites(makesprites.chars)
    files.append(("CHARS", 0x3f00, 0x3f00, data))

    system("ophis tapecode.oph -o CODE")
    code = open("CODE").read()
    code_start = 0x1e00
    files.append(("CODE", code_start, code_start, code))
    
    u = build_uef(files)
    
    # Write the new UEF file.
    try:
        u.write(out_uef_file, write_emulator_info = False)
    except UEFfile.UEFfile_error:
        sys.stderr.write("Couldn't write the new executable to %s.\n" % out_uef_file)
        sys.exit(1)
    
    # Write a UEF file for transfer to ADFS.

    # Replace the loader and insert a boot file.
    files.pop(0)
    files.insert(0, ("RETRO", 0x1d00, 0x8023, open("resources/loader_U3A", "rb").read()))
    files.insert(0, ("!BOOT", 0x0, 0x0, 'CHAIN "RETRO"\r'))
    
    u = build_uef(files)
    out_uef_adf_file = out_uef_file.replace(".uef", "-for-ADFS.uef")
    try:
        u.write(out_uef_adf_file, write_emulator_info = False)
    except UEFfile.UEFfile_error:
        sys.stderr.write("Couldn't write the new executable to %s.\n" % out_uef_adf_file)
        sys.exit(1)
    
    print
    print "Written", out_uef_adf_file
    
    # Write an SSD file.
    
    disk = makedfs.Disk()
    disk.new()
    
    catalogue = disk.catalogue()
    catalogue.boot_option = 3

    # Replace the loader.
    files[1] = ("RETRO", 0x1900, 0x8023, open("resources/loader_U5D", "rb").read())
    disk_files = []
    for name, load, exec_, data in files:
        disk_files.append(makedfs.File("$." + name, data, load, exec_, len(data)))
    
    COPYING = open("COPYING").read().replace("\n", "\r\n")
    disk_files.append(makedfs.File("$.COPYING", COPYING, 0x0000, 0x0000, len(COPYING)))
    
    catalogue.write("Journey", disk_files)
    
    disk.file.seek(0, 0)
    disk_data = disk.file.read()
    out_ssd_file = out_uef_file.replace(".uef", ".ssd")
    open(out_ssd_file, "w").write(disk_data)
    
    print "Written", out_ssd_file

    # Exit
    sys.exit()
