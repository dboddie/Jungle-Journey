#!/usr/bin/env python

import os, sys
import Image
import series
from tileimages import blank, tile_size, leaf1, leaf2, visited, flowers, \
                       flowers2, leaf4, leaf6, flowers3, leaf5, leaf3, \
                       exit, final_exit1, final_exit2, item_size, player, \
                       treasure_images

image_sets = {
    100: [blank, flowers, leaf1, leaf2, exit],
    239: [blank, flowers2, leaf6, leaf4, exit],
    183: [blank, flowers2, leaf6, leaf4, exit],
    144: [blank, flowers3, leaf5, leaf3, exit, final_exit1, final_exit2]
    }

default_image_set = [blank, flowers, leaf1, leaf2]

tile_values_map = [0, 1, 0, 0, 0, 0, 2, 3, 4, 5, 6]

class Mapper:

    start_rooms = {100: (5, 5), 36: (0, 0), 44: (9, 7), 4: (7, 0), 5: (5, 10),
                     8: (0, 8), 10: (0, 10), 17: (7, 10), 26: (0, 9),
                    33: (10, 0), 127: (0, 0), 144: (10, 8), 183: (5, 1),
                   239: (3, 8)}
    exit_rooms  = {100: (7, 0), 36: (7, 0),             4: (5, 10), 5: (9, 6),
                     8: (3, 0), 10: (10, 2), 17: (9, 0), 26: (10, 4),
                    33: (2, 10), 144: (0, 10), 183: (3, 9), 239: (9, 0)}
    key_rooms   = {100: (1, 0), 17: (0, 0), 26: (9, 0), 33: (10, 6), 144: (1, 4),
                   183: (10, 6), 239: (5, 2)}
    extra_life_rooms = {17: (2, 0), 26: (9, 4)}
    
    levels = {100: 0, 183: 1, 239: 2, 144: 3}
    
    treasure_table = [6, 5, 7, 1, 1, 5, 2, 7, 6, 2, 1, 7, 1, 7, 8, 7,
                      0, 7, 6, 7, 7, 7, 5, 0, 6, 3, 7, 7, 5, 7, 5, 0]

    treasure_x = [3, 2, 4, 8, 2, 5, 4, 1, 3, 8, 6, 5, 7, 1, 7, 6]
    treasure_y = [1, 3, 7, 7, 2, 3, 6, 1, 4, 6, 8, 5, 5, 4, 8, 2]
    
    exit_room_offsets = [35, 66, 63, 56, 34, 44, 64, 33, 36, 55, 65, 53,
                         45, 46, 54, 43]
    
    def __init__(self, map_width, map_height, room_width, room_height, seed,
                       image, images, wall_tile, floor_tiles):
    
        self.map_width = map_width
        self.map_height = map_height
        self.room_width = room_width
        self.room_height = room_height
        self.rooms = {}
        self.exits = {}
        self.visited = set()
        self.seed = seed
        self.image = image
        self.images = images
        self.wall_tile = wall_tile
        self.floor_tiles = floor_tiles
        
        self.add_objects()
    
    def add_objects(self):
    
        self.objects = []
        
        first = (self.seed + 1) & 31
        second = (self.seed + 2) & 31
        gen = series.unlimited_values(first, second)
        
        # Find the level associated with the seed used for the map.
        level = self.levels.get(self.seed, 0)
        
        k = 0
        for i in range(self.map_height):
        
            for j in range(self.map_width):
            
                if self.key_rooms.get(self.seed, ()) == (j, i):
                
                    self.objects.append(5)
                
                else:
                
                    item = gen.next() & 15
                    if item == 0:
                        self.objects.append(0)
                    else:
                        treasure = self.treasure_table[(item + k) & 31]
                        if 0 <= treasure <= 3:
                            if treasure <= level + 1:
                                self.objects.append(treasure + 1)
                            else:
                                self.objects.append(0)
                        else:
                            self.objects.append(treasure + 1)
                    
                k += 1
    
    def make_room(self, i, j):
    
        first = j
        second = self.seed - i
        
        gen = series.unlimited_values(first, second)
        for k in range(10):
            gen.next()
        
        special_rooms = {self.start_rooms.get(self.seed, ()): 7,
                         self.exit_rooms.get(self.seed, ()): 7,
                         self.key_rooms.get(self.seed, ()): 1}
        
        if (j, i) in special_rooms:
        
            x = y = 1
            while True:
                if (x, y) in [(1, 1), (1, 8), (8, 1), (8, 8)]:
                    yield special_rooms[(j, i)]
                
                elif (j, i) == self.exit_rooms.get(self.seed, ()):
                    position = self.exit_room_offsets[(i ^ j) & 15]
                    if x == position % 10 and y == position / 10:
                        yield 8
                    else:
                        yield 0
                
                else:
                    yield 0
                
                x += 1
                if x == 9:
                    x = 1
                    y += 1
        
        else:
            while True:
                yield (gen.next() % 9) & 7
    
    def top_exit(self, i, j):
    
        if i == 0:
            return True
        elif i & 7 == j & 7:
            return False
        
        return ((i ^ j) + i) == j
    
    def right_exit(self, i, j):
    
        if j == self.map_width - 1:
            return True
        
        return self.left_exit(i, j + 1)
    
    def bottom_exit(self, i, j):
    
        if i == self.map_height - 1:
            return True
        
        return self.top_exit(i + 1, j)
    
    def left_exit(self, i, j):
    
        if j == 0:
            return True
        elif i & 3 == j & 3:
            return False
        
        return ((i | j) ^ j) == i
    
    def make_room_image(self, i, j):
    
        im = Image.new("P", (self.room_width * tile_size[0],
                             self.room_height * tile_size[1]), 0)
        
        rows, exits = self.read_room((j, i))
        
        for y in range(0, self.room_height):
            for x in range(0, self.room_width):
            
                value = rows[y][x]
                im.paste(self.images[value], (x * tile_size[0], y * tile_size[1]))
        
        item, x, y = self.item_for_room(rows, i, j)
        if item is not None:
        
            im.paste(treasure_images[item],
                     (x * tile_size[0],
                      y * tile_size[1] + (tile_size[1] - item_size[1])/2))
        
        return im
    
    def item_for_room(self, rows, i, j):
    
        item = self.objects[i * self.map_height + j]
        if item != 0:
        
            item -= 1
            k = ((i ^ j) + item) & 15
            a = 15
            while a >= 0:
            
                x, y = self.treasure_x[k], self.treasure_y[k]
                
                if rows[y][x] & 0x7f == 0:
                
                    return item, x, y
                    break
                
                if k > 0:
                    k -= 1
                else:
                    k = 15
                a -= 1
        
        return None, 0, 0
    
    def read_room(self, room):
    
        gen = self.make_room(room[1], room[0])
        
        if self.rooms.has_key(room):
            rows = self.rooms[room]
            exits = self.exits[room]
        else:
            exits = []
            exits.append(self.top_exit(room[1], room[0]))
            exits.append(self.right_exit(room[1], room[0]))
            exits.append(self.bottom_exit(room[1], room[0]))
            exits.append(self.left_exit(room[1], room[0]))
            
            rows = []
            cx = self.room_width/2 - 2
            cy = self.room_height/2 - 2
            
            if exits[0]:
                rows.append([self.wall_tile]*self.room_width)
            else:
                rows.append([self.wall_tile]*cx + [0]*(self.room_width - 2*cx) + [self.wall_tile]*cx)
            
            if self.levels.get(self.seed) == 3 and room == (2, 0):
            
                rows[-1][4] = 5
                rows[-1][5] = 6
            
            for ry in range(1, self.room_height - 1):
                row = []
                if exits[3] or ry < cy or ry > self.room_height - cy - 1:
                    row.append(self.wall_tile)
                else:
                    row.append(0)
                
                for rx in range(1, self.room_width - 1):
                    row.append(tile_values_map[gen.next()])
                
                if exits[1] or ry < cy or ry > self.room_height - cy - 1:
                    row.append(self.wall_tile)
                else:
                    row.append(0)
                rows.append(row)
            
            if exits[2]:
                rows.append([self.wall_tile]*self.room_width)
            else:
                rows.append([self.wall_tile]*cx + [0]*(self.room_width - 2*cx) + [self.wall_tile]*cx)
            
            self.rooms[room] = rows
            self.exits[room] = exits
        
        return rows, exits
    
    def find_map_extent(self, room, x = None, y = None):
    
        rows, exits = self.read_room(room)
        
        if x is None:
            x = self.room_width/2 - 1
            y = self.room_height/2 - 1
        
        places = [(x, y)]
        
        # Use a recursive algorithm to explore the room, but don't recursively
        # call this function until we leave the room.
        
        while places:
        
            x, y = places.pop()
            
            if rows[y][x] not in self.floor_tiles:
                # The square has already been visited, so backtrack.
                continue
            else:
                # Mark this room as visited.
                self.visited.add(room)
                #self.image.paste(visited,
                #    ((room[0] * self.room_width + x) * tile_size[0] + room[0] + 3 * tile_size[0]/8,
                #     (room[1] * self.room_height + y) * tile_size[1] + room[1] + 3 * tile_size[1]/8))
            
            # Mark this square as visited.
            rows[y][x] = rows[y][x] | 0x80
            
            # Try to move to adjacent squares.
            if x > 0:
                if rows[y][x-1] in self.floor_tiles:
                    places.append((x - 1, y))
            elif room[0] > 0:
                self.find_map_extent((room[0] - 1, room[1]),
                                     self.room_width - 1, y)
            
            if x < self.room_width - 1:
                if rows[y][x+1] in self.floor_tiles:
                    places.append((x + 1, y))
            elif room[0] < self.map_width - 1:
                self.find_map_extent((room[0] + 1, room[1]), 0, y)
            
            if y > 0:
                if rows[y-1][x] in self.floor_tiles:
                    places.append((x, y - 1))
            elif room[1] > 0:
                self.find_map_extent((room[0], room[1] - 1),
                                     x, self.room_height - 1)
            
            if y < self.room_height - 1:
                if rows[y+1][x] in self.floor_tiles:
                    places.append((x, y + 1))
            elif room[1] < self.map_height - 1:
                self.find_map_extent((room[0], room[1] + 1), x, 0)

def fade(image, x0, y0, w, h):

    for i in range(h):
    
        y = y0 + i
        x = x0 + y % 2
        while x < x0 + w:
            image.putpixel((x, y), 0)
            x += 2

def select_images(seed):

    images = image_sets.get(seed, default_image_set)
    wall_tile = 2
    floor_tiles = []
    
    for i in range(len(images)):
        if images[i] in (blank,):
            floor_tiles.append(i)
    
    return images, wall_tile, floor_tiles

def make_map(name, width, height, room_width, room_height, seed):

    images, wall_tile, floor_tiles = select_images(seed)
    
    im = Image.new("P", (width * room_width * tile_size[0] + (width - 1),
                         height * room_height * tile_size[1] + (height - 1)), 7)
    #im.putpalette((0,0,0, 255,0,0, 0,255,0, 255,255,0, 0,0,255, 255,0,255, 0,255,255, 255,255,255))
    black = (0,0,0)
    red = (255,0,0)
    green = (0,255,0)
    yellow = (255,255,0)
    blue = (0,0,255)
    magenta = (255,0,255)
    cyan = (0,255,255)
    white = (255,255,255)
    im.putpalette(black + red + green + yellow + blue + magenta + cyan + white)
    room_palettes = [1, 6, 5, 7]
    
    mapper = Mapper(width, height, room_width, room_height, seed, im, images,
                    wall_tile, floor_tiles)
    
    for i in range(height):
        for j in range(width):
        
            room_image = mapper.make_room_image(i, j)
            
            # Change the palette for this room.
            room_string = room_image.tostring()
            
            # Replace logical colour 1 with 1, 3, 5 or 7.
            new_colour = room_palettes[(i ^ j) & 3]
            if new_colour != 1:
                room_string = room_string.replace("\x01", chr(new_colour))
            
            room_image = Image.fromstring("P", (room_width * tile_size[0],
                                                room_height * tile_size[1]),
                                          room_string)
            
            im.paste(room_image, (j * room_width * tile_size[0] + j,
                                  i * room_height * tile_size[1] + i))
    
    start_room = mapper.start_rooms.get(seed)
    
    if start_room:
    
        mapper.find_map_extent(start_room)
        
        mapper.image.paste(player,
            (int((start_room[0] + 0.5) * mapper.room_width * tile_size[0]) + start_room[0] - tile_size[0]/4,
             int((start_room[1] + 0.5) * mapper.room_height * tile_size[1]) + start_room[1] - tile_size[1]/2))
        
        for i in range(height):
            for j in range(width):
            
                if (j,i) not in mapper.visited:
                
                    fade(im, j * room_width * tile_size[0] + j,
                             i * room_height * tile_size[1] + i,
                             room_width * tile_size[0],
                             room_height * tile_size[1])
    
    im.save(name)


if __name__ == "__main__":

    if len(sys.argv) != 5:
    
        sys.stderr.write("Usage: %s <width> <height> <seed> <file name>\n\n" % sys.argv[0])
        sys.stderr.write("For the release version of Jungle Journey, use a value of 11\n"
                         "for both width and height, and one of 100, 239, 183 or 144\n"
                         "for the seed value.\n")
        sys.exit(1)
    
    width = int(sys.argv[1])
    height = int(sys.argv[2])
    seed = int(sys.argv[3])
    name = sys.argv[4]
    room_width = 10
    room_height = 10
    
    start_room = (width/2, height/2)
    stem, suffix = os.path.splitext(name)
    
    make_map("%s-%02x%s" % (stem, seed, suffix),
             width, height, room_width, room_height, seed)
    
    print "Created %s-%02x%s" % (stem, seed, suffix)
    
    sys.exit()
