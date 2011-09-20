#!/usr/bin/env python

import os, sys
from PyQt4.QtCore import QSize
from PyQt4.QtGui import *


class Page:

    def __init__(self, size, objects):
    
        self.size = size
        self.objects = objects
    
    def render(self, image = None):
    
        if not image:
            image = QImage(QSize(*self.size), QImage.Format_RGB32)
            image.fill(qRgb(255,255,255))
        
        positions = [(0, 0)]
        for obj in self.objects:
        
            x, y = obj.render(image, positions)
            positions.append((x, y))
        
        return image

class TextBox:

    def __init__(self, bbox, text_items, follow = False, index = -1):
    
        self.bbox = bbox
        self.text_items = text_items
        self.follow = follow
        self.index = index
    
    def render(self, image, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        p = QPainter()
        p.begin(image)
        p.setRenderHint(QPainter.TextAntialiasing)
        
        for text_item in self.text_items:
        
            left_indent = text_item.font.get("left indent", 0)
            right_indent = text_item.font.get("right indent", 0)
            item_x = x + left_indent
            item_width = width - left_indent - right_indent
            
            for pieces, line_height in text_item.readline(item_width):
            
                for font, word_x, text in pieces:
                
                    p.setFont(font)
                    p.drawText(item_x + word_x, y, text)
                
                y += line_height
        
        p.end()
        
        return x, y

class Text:

    def __init__(self, font, text):
    
        self.font = font
        self.text = text
        
        self.parse_text()
    
    def parse_text(self):
    
        lines = self.text.split("\n")
        self.lines = []
        
        for line in lines:
        
            words = []
            for word in line.split():
            
                words.append(Word(self.font, word))
            
            self.lines.append(words)
    
    def readline(self, width):
    
        for line in self.lines:
        
            w = 0
            used = 0
            words = []
            
            while w < len(line):
            
                word = line[w]
                word_width = word.width()
                
                if used + word_width <= width:
                    # Add words while there is still space.
                    used += word_width + word.space()
                    words.append(word)
                    w += 1
                
                elif words:
                    # When out of space, yield the words on the line.
                    yield self.format(words, width), self.height(words)
                    
                    used = 0
                    words = []
                
                else:
                    # If no words will fit on the line, just add the first
                    # word to the list.
                    yield self.format([word], width), self.height(words)
                    
                    used = 0
                    w += 1
            
            if words:
                yield self.format(words, width, last = True), self.height(words)
            elif not line:
                yield [], self.line_height()/2
    
    def format(self, words, width, last = False):
    
        output = []
        x = 0
        
        if len(words) == 0:
            spacing = 0
        elif self.font.get("align", "left") == "justify" and not last:
            # Full justify the text.
            total_width = sum(map(lambda word: word.width(), words))
            spacing = (width - total_width)/float(len(words))
        elif self.font.get("align", "left") == "centre":
            # Centre the text.
            total_width = sum(map(lambda word: word.width(), words))
            total_space = sum(map(lambda word: word.space(), words)[:-1])
            x = width/2.0 - total_width/2.0 - total_space/2.0
            spacing = None
        else:
            spacing = None
        
        for word in words:
        
            output.append((word.font(), x, word.text))
            x += word.width()
            if spacing is not None:
                x += spacing
            else:
                x += word.space()
        
        return output
    
    def height(self, words):
    
        return max(map(lambda word: word.height(), words))
    
    def line_height(self):
    
        font = QFont(self.font.get("family"))
        font.setPixelSize(self.font.get("size"))
        if self.font.get("weight") == "bold":
            font.setWeight(QFont.Bold)
        if self.font.get("style") == "italic":
            font.setItalic(True)
        
        metrics = QFontMetrics(font)
        return metrics.height()

class Word:

    def __init__(self, font, text):
    
        self._font = font
        self.text = text
    
    def font(self):
    
        font = QFont(self._font.get("family"))
        font.setPixelSize(self._font.get("size"))
        if self._font.get("weight") == "bold":
            font.setWeight(QFont.Bold)
        if self._font.get("style") == "italic":
            font.setItalic(True)
        return font
    
    def width(self):
    
        metrics = QFontMetrics(self.font())
        return metrics.width(self.text)
    
    def height(self):
    
        metrics = QFontMetrics(self.font())
        return metrics.height()
    
    def space(self):
    
        metrics = QFontMetrics(self.font())
        return metrics.width(" ")


class Image:

    def __init__(self, bbox, path, scale = None, follow = False, index = -1):
    
        self.bbox = bbox
        self.path = path
        self.follow = follow
        self.index = index
        self.scale = scale
    
    def render(self, image, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        p = QPainter()
        p.begin(image)
        p.setRenderHint(QPainter.TextAntialiasing)
        
        im = QImage(self.path)
        if self.scale:
            im = im.scaled(self.scale * im.width(), self.scale * im.height())
        p.drawImage(x, y, im)
        
        p.end()
        
        return x + im.size().width(), y + im.size().height()


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if len(app.arguments()) != 2:
    
        sys.stderr.write("Usage: %s <output directory>\n" % app.arguments()[0])
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    regular = {"family": "FreeSerif",
               "size": 24,
               "align": "justify"}
    
    title = {"family": "FreeSerif",
             "size": 24,
             "weight": "bold"}
    
    italic_quote = {"family": "FreeSerif",
                    "size": 24,
                    "style": "italic",
                    "left indent": 40,
                    "right indent": 40}
    
    quote = {"family": "FreeSerif",
             "size": 22,
             "left indent": 40,
             "right indent": 40}
    
    monospace_quote = {"family": "FreeMono",
                       "size": 24,
                       "left indent": 40,
                       "right indent": 40}
    
    keys_quote = {"family": "FreeSerif",
                  "size": 24,
                  "left indent": 40,
                  "right indent": 40}
    
    key_descriptions_quote = {"family": "FreeSerif",
                              "size": 24,
                              "left indent": 160,
                              "right indent": 40}
    
    exclamation = {"family": "FreeSerif",
                   "size": 28,
                   "style": "italic",
                   "weight": "bold",
                   "align": "centre"}
    
    pages = [
        Page((750, 1000),
             [TextBox((50, 40, 650, 0), 
                      [Text(title, "Jungle Journey\n"),
                       Text(regular,
                            "The last flames of the campfire fade to glowing embers and I am alone. "
                            "My recent acquaintances, their packs and paraphernalia have gone, leaving "
                            "me stranded deep in the heart of this jungle realm. Clouds momentarily "
                            "sweep the cold face of the moon and I perceive the clicks, whistles and "
                            "cries of creatures in the hot air that cloaks this place. Desperately, I "
                            "try to stay my panic and remember those fragments of wilderness craft "
                            "learned and unlearned many years ago.\n\n"),
                       Text(italic_quote,
                            "Choose your weapon carefully,\n"
                            "Get ready for a fight.\n"
                            "The jungle can be dangerous\n"
                            "If you go there at night.\n"
                            "There's time to pick up treasure,\n"
                            "But no time to stop and stare.\n"
                            "If you don't find the hidden gate\n"
                            "You won't get out of there.\n\n"),
                       Text(regular,
                            "Hopeless, I scramble to my feet, reaching for any weapon still left to me. "
                            "Struggling through the dense undergrowth, I search for signs of a track or "
                            "trail. At first glance, paths that seemed to lead to safety turn out to be "
                            "impassable, overgrown by tangled and twisted vines. I remember the words of "
                            "an old teacher:\n\n"),
                       Text(quote,
                            u'\u201cDo not be tempted to use fire to make your way. '
                            'Many a traveller has strayed from the path, using fire to blaze a trail, '
                            'only to reach a dead end. Trying to return, they find that the jungle '
                            'has grown back. Those who are desperate enough will even seek out '
                            u'forgotten routes when the way home is in sight.\u201d\n\n'),
                       Text(regular,
                            "Sensing my presence, obscene creatures emerge from the darkness, hungry "
                            "for prey. Only through skill and luck am I able to dispatch them back "
                            "into the shadows. Even though I know I must journey deeper into this "
                            "uncharted land to find the way home, the thought of vengeance drives me on.")
                      ])
             ]),
        Page((750, 1000),
             [TextBox((50, 40, 650, 0),
                      [Text(title, "Loading the Game\n"),
                       Text(regular, "Insert the cassette or disk and type\n"),
                       Text(monospace_quote, "*RUN JUNGLE\n"),
                       Text(regular,
                            "then press Return. If you are loading the game from cassette, press play on the "
                            "cassette recorder. The game should now load.\n\n\n"),
                       Text(title, "Playing the Game\n"),
                       Text(regular,
                            "The player must help the character reach the exit for each level. However, the "
                            "player must first find a key to unlock the exit. On the final level, the exit "
                            "does not require a key but it may be obstructed. Enemies will appear in each "
                            "location and attack the player's character. These can be destroyed by "
                            "projectiles fired by the current weapon.\n\n"
                            "Your character can be moved around the screen by using four control keys:\n")]),
              TextBox((50, 0, 650, 0),
                      [Text(keys_quote,
                            "Z\n"
                            "X\n"
                            ":\n"
                            "/")], follow = True),
              TextBox((50, 0, 650, 0),
                      [Text(key_descriptions_quote,
                            "left\n"
                            "right\n"
                            "up\n"
                            "down\n"),
                       Text(regular,
                            "To fire a weapon, press the Return key. There are four different types of "
                            "weapon available in the game.\n\n"
                            "Alternatively, you may may using an analogue joystick connected to a Plus 1 "
                            "expansion interface. Select joystick controls by pressing the J key on the "
                            "title page. Press K to select keyboard controls again.\n\n"
                            "Other keys can be used to control the game:\n")],
                      follow = True, index = -2),
              TextBox((50, 0, 650, 0),
                      [Text(keys_quote,
                            "S\n"
                            "Q\n"
                            "P\n"
                            "O\n"
                            "Escape")], follow = True),
              TextBox((50, 0, 650, 0),
                      [Text(key_descriptions_quote,
                            "enable sound effects\n"
                            "disable sound effects\n"
                            "pause the game\n"
                            "resume the game\n"
                            "quit the game, returning to the title screen\n")],
                      follow = True, index = -2)
             ]),
        Page((750, 1000),
             [TextBox((50, 40, 650, 0),
                      [Text(title, "Treasure\n"),
                       Text(regular, "Items of treasure can be found throughout the jungle. "
                                     "Pick these up to increase your score.\n")]),
              Image((80, -8, 620, 0), "../images/key.xpm", scale = 4,
                    follow = True),
              TextBox((170, 20, 480, 0),
                      [Text(regular, "Find the key to open the door on all levels except the last. "
                                     "Each key is worth 50 points.")],
                      follow = True, index = -2),
              Image((80, 8, 620, 0), "../images/chest.xpm", scale = 4,
                    follow = True, index = -2),
              TextBox((170, 48, 480, 0),
                      [Text(regular, "Treasure chests are worth 20 points.")],
                      follow = True, index = -3),
              Image((80, 8, 620, 0), "../images/jewel.xpm", scale = 4,
                    follow = True, index = -2),
              TextBox((170, 48, 480, 0),
                      [Text(regular, "Jewels are worth 5 points.")],
                      follow = True, index = -3),
              Image((80, 8, 620, 0), "../images/statue.xpm", scale = 4,
                    follow = True, index = -2),
              TextBox((170, 48, 480, 0),
                      [Text(regular, "Statues are worth 10 points.")],
                      follow = True, index = -3),
              Image((80, 8, 620, 0), "../images/health.xpm", scale = 4,
                    follow = True, index = -2),
              TextBox((170, 36, 480, 0),
                      [Text(regular, "Presents are worth 40 points and boost your strength by 20 units.")],
                      follow = True, index = -3),
              TextBox((50, 48, 650, 0),
                      [Text(title, "Exits\n"),
                       Text(regular, "Each level has an exit that can be opened using a key. "
                                     "On the last level you will find a gate that leads to safety. "
                                     "This does not require a key, but it is well hidden.\n")],
                      follow = True),
              Image((112, -4, 620, 0), "../images/exit1.xpm", scale = 4,
                    follow = True),
              TextBox((240, 36, 410, 0),
                      [Text(regular, "The exit is initially locked. Find the key to unlock it.")],
                      follow = True, index = -2),
              Image((80, 8, 620, 0), "../images/finalexitl.xpm", scale = 4,
                    follow = True, index = -2),
              Image((144, 8, 620, 0), "../images/finalexitr.xpm", scale = 4,
                    follow = True, index = -3),
              TextBox((240, 48, 410, 0),
                      [Text(regular, "The final exit is hidden somewhere on the final level.")],
                      follow = True, index = -4),
              TextBox((50, 950, 650, 0),
                      [Text(exclamation, "Have a safe journey!")])
             ])
        ]
    
    i = 0
    for page in pages:
    
        path = os.path.join(output_dir, "page-%i.png" % i)
        image = page.render()
        image.save(path)
        i += 1
    
    sys.exit()
