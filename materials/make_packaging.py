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
        
        x, y = 0, 0
        for obj in self.objects:
        
            x, y = obj.render(image, x, y)
        
        return image

class TextBox:

    def __init__(self, bbox, text_items, follow = False):
    
        self.bbox = bbox
        self.text_items = text_items
        self.follow = follow
    
    def render(self, image, previous_x, previous_y):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y += previous_y
        
        p = QPainter()
        p.begin(image)
        p.setRenderHint(QPainter.TextAntialiasing)
        
        for text_item in self.text_items:
        
            for pieces, line_height in text_item.readline(width):
            
                for font, word_x, text in pieces:
                
                    p.setFont(font)
                    p.drawText(x + word_x, y, text)
                
                y += line_height
        
        p.end()
        
        return x, y

class Text:

    def __init__(self, font, font_size, text, align = "left", style = None,
                       weight = None):
    
        self.font = {"family": font, "size": font_size, "weight": weight,
                     "style": style}
        self.text = text
        self.align = align
        
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
                yield self.format(words, width), self.height(words)
            elif not line:
                yield [], self.line_height()/2
    
    def format(self, words, width):
    
        output = []
        
        if len(words) == 0:
            spacing = 0
        elif self.align == "justify":
            # Full justify the text.
            total_width = sum(map(lambda word: word.width(), words))
            spacing = (width - total_width)/float(len(words))
        else:
            spacing = None
        
        x = 0
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
    
        font = QFont(self.font["family"])
        font.setPixelSize(self.font["size"])
        if self.font["weight"] == "bold":
            font.setWeight(QFont.Bold)
        if self.font["style"] == "italic":
            font.setItalic(True)
        
        metrics = QFontMetrics(font)
        return metrics.height()

class Word:

    def __init__(self, font, text):
    
        self._font = font
        self.text = text
    
    def font(self):
    
        font = QFont(self._font["family"])
        font.setPixelSize(self._font["size"])
        if self._font["weight"] == "bold":
            font.setWeight(QFont.Bold)
        if self._font["style"] == "italic":
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


if __name__ == "__main__":

    app = QApplication(sys.argv)
    
    if len(app.arguments()) != 2:
    
        sys.stderr.write("Usage: %s <output directory>\n" % app.arguments()[0])
        sys.exit(1)
    
    output_dir = sys.argv[1]
    
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    
    pages = [
        Page((800, 1000),
             [TextBox((80, 40, 640, 1120), 
                      [Text("FreeSerif", 24, "Jungle Journey\n", weight = "bold"),
                       Text("FreeSerif", 24,
                            "The last flames of the campfire fade to glowing embers and I am alone. "
                            "My recent acquaintances, their packs and paraphernalia have gone, leaving "
                            "me stranded deep in the heart of this jungle realm. Clouds momentarily "
                            "sweep the cold face of the moon and I perceive the clicks, whistles and "
                            "cries of creatures in the hot air that cloaks this place. Desperately, I "
                            "try to stay my panic and remember those fragments of wilderness craft "
                            "learned and unlearned many years ago.\n")]),
              TextBox((120, 0, 560, 0),
                      [Text("FreeSerif", 24,
                            "Choose your weapon carefully,\n"
                            "Get ready for a fight.\n"
                            "The jungle can be dangerous\n"
                            "If you go there at night.\n"
                            "There's time to pick up treasure,\n"
                            "But no time to stop and stare.\n"
                            "If you don't find the hidden gate\n"
                            "You won't get out of there.\n", style = "italic")],
                      follow = True),
              TextBox((80, 0, 640, 0),
                      [Text("FreeSerif", 24,
                            "Hopeless, I scramble to my feet, reaching for any weapon still left to me. "
                            "Struggling through the dense undergrowth, I search for signs of a track or "
                            "trail. At first glance, paths that seemed to lead to safety turn out to be "
                            "impassable, overgrown by tangled and twisted vines. I remember the words of "
                            "an old teacher:\n")],
                      follow = True),
              TextBox((120, 0, 560, 0),
                      [Text("FreeSerif", 22,
                            u'\u201cDo not be tempted to use fire to make your way. '
                            'Many a traveller has strayed from the path, using fire to blaze a trail, '
                            'only to reach a dead end. Trying to return, they find that the jungle '
                            'has grown back. Those who are desperate enough will even seek out '
                            u'forgotten routes when the way home is in sight.\u201d\n')],
                      follow = True),
              TextBox((80, 0, 640, 0),
                      [Text("FreeSerif", 24,
                            "Sensing my presence, obscene creatures emerge from the darkness, hungry "
                            "for prey. Only through skill and luck am I able to dispatch them back "
                            "into the shadows. Even though I know I must journey deeper into this "
                            "uncharted land to find the way home, the thought of vengeance drives me on.")],
                      follow = True)
              ])]
    
    i = 0
    for page in pages:
    
        path = os.path.join(output_dir, "page-%i.png" % i)
        image = page.render()
        image.save(path)
    
    sys.exit()
