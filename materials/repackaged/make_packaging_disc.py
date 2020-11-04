#!/usr/bin/env python

"""
Copyright (C) 2020 David Boddie <david@boddie.org.uk>

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

import codecs, os, sys
from PyQt4.QtCore import QSize
from PyQt4.QtGui import *

def relpath(source, destination):

    source = os.path.abspath(source)
    destination = os.path.abspath(destination)
    
    src_pieces = source.split(os.sep)
    dest_pieces = destination.split(os.sep)
    
    if not os.path.exists(source) or os.path.isfile(source):
        src_pieces.pop()
    
    common = []
    for i in range(min(len(src_pieces), len(dest_pieces))):
    
        if src_pieces[i] == dest_pieces[i]:
            common.append(src_pieces[i])
            i -= 1
        else:
            break
    
    to_common = [os.pardir]*(len(src_pieces)-len(common))
    rel_pieces = to_common + dest_pieces[len(common):]
    return os.sep.join(rel_pieces)


class SVG:

    def __init__(self, path):
    
        self.path = path
        self.ox = self.oy = 0
        self.defs = ""
    
    def _escape(self, text):
    
        for s, r in (("&", "&amp;"), ("<", "&lt;"), (">", "&gt;")):
            text = text.replace(s, r)
        
        return text
    
    def open(self):
    
        self.text = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                     '<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n'
                     '  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n')
    
    def add_defs(self, defs):
    
        self.defs = defs
    
    def add_page(self, width, height):
    
        self.text += ('<svg version="1.1"\n'
                      '     xmlns="http://www.w3.org/2000/svg"\n'
                      '     xmlns:xlink="http://www.w3.org/1999/xlink"\n'
                      '     width="%fcm" height="%fcm"\n'
                      '     viewBox="0 0 %i %i">\n') % (width/100.0, height/100.0, width, height)
        
        self.text += '<defs>\n' + defs + '\n</defs>\n'
    
    def add_image(self, x, y, width, height, path):
    
        path = os.path.join(relpath(self.path, os.curdir), path)
        self.text += '<image x="%f" y="%f" width="%f" height="%f"\n' % (x, y, width, height)
        self.text += '       xlink:href="%s" />\n' % path
        
    def add_text(self, x, y, font, text):
    
        self.text += '<text x="%f" y="%f"\n' % (x, y)
        self.text += ('      font-family="%s"\n'
                      '      font-size="%i"\n') % (font["family"], font["size"])
        if font.has_key("weight"):
            self.text += '      font-weight="%s"\n' % font["weight"]
        if font.has_key("style"):
            self.text += '      font-style="%s"\n' % font["style"]
        if font.has_key("colour"):
            self.text += '      fill="%s"\n' % font["colour"]
        self.text += '>\n'
        self.text += self._escape(text)
        self.text += '</text>\n'
    
    def close(self):
    
        self.text += "</svg>\n"
        codecs.open(self.path, "w", "utf-8").write(self.text)


class Inlay(SVG):

    def __init__(self, path, page_rects, total_size):
    
        SVG.__init__(self, path)
        
        self.page_rects = page_rects
        self.total_size = total_size
        self.page_number = 0
        self.reverse = False
    
    def open(self):
    
        SVG.open(self)
        self.text += ('<svg version="1.1"\n'
                      '     xmlns="http://www.w3.org/2000/svg"\n'
                      '     xmlns:xlink="http://www.w3.org/1999/xlink"\n')
        
        w, h = self.total_size
        self.text += ('     width="%fcm" height="%fcm"\n'
                      '     viewBox="0 0 %i %i">\n' % (w/100.0, h/100.0, w, h))
        
        self.text += '<defs>\n' + defs + '\n</defs>\n'
    
    def add_page(self, width, height):
    
        if self.page_number > 0:
        
            rect, reverse = self.page_rects[self.page_number - 1]
        
            if reverse:
                self.text += '</g>\n'
        
        rect, self.reverse = self.page_rects[self.page_number]
        self.ox, self.oy, w, h = rect
        self.page_number += 1
        
        if self.reverse:
            self.text += '<g transform="rotate(180) translate(%f, %f)">\n' % \
                         (-(self.ox*2 + w), -(self.oy*2 + h))
    
    def add_image(self, x, y, width, height, path):
    
        SVG.add_image(self, self.ox + x, self.oy + y, width, height, path)
    
    def add_text(self, x, y, font, text):
    
        SVG.add_text(self, self.ox + x, self.oy + y, font, text)
    
    def close(self):
    
        if self.page_number > 0:
        
            rect, reverse = self.page_rects[self.page_number - 1]
            
            if self.reverse:
                self.text += '</g>\n'
        
        self.text += self.crop_marks(rect)
        
        SVG.close(self)
    
    def crop_marks(self, rect):
    
        return ('<path d="M 150,0 L 150,100 M 0,150 L 100,150\n'
                'M 3290,150 L 3390,150 M 3240,0 L 3240,100\n'
                'M 150,2460 L 150,2360 M 0,2310 L 100,2310\n'
                'M 3290,2310 L 3390,2310 M 3240,2360 L 3240,2460"\n'
                'stroke="black" fill="none" stroke-width="1" />\n')


class Page:

    def __init__(self, size, objects):
    
        self.size = size
        self.objects = objects
    
    def render(self, svg):
    
        svg.add_page(self.size[0], self.size[1])
        
        positions = [(0, 0)]
        for obj in self.objects:
        
            x, y = obj.render(svg, positions)
            positions.append((x, y))
        
        return svg


class TextBox:

    def __init__(self, bbox, text_items, line_spacing = 1.0, follow = False, index = -1):
    
        self.bbox = bbox
        self.text_items = text_items
        self.line_spacing = line_spacing
        self.follow = follow
        self.index = index
    
    def render(self, svg, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        for text_item in self.text_items:
        
            left_indent = text_item.font.get("left indent", 0)
            right_indent = text_item.font.get("right indent", 0)
            item_x = x + left_indent
            item_width = width - left_indent - right_indent
            
            for pieces, line_height in text_item.readline(item_width):
            
                for font, word_x, text in pieces:
                
                    svg.add_text(item_x + word_x, y, font, text)
                
                y += line_height * self.line_spacing
        
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
                    yield self.format([word], width), self.height([word])
                    
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
            spacing = (width - total_width)/float(len(words) - 1)
        
        elif self.font.get("align", "left") == "centre":
            # Centre the text.
            total_width = sum(map(lambda word: word.width(), words))
            total_space = sum(map(lambda word: word.space(), words)[:-1])
            x = width/2.0 - total_width/2.0 - total_space/2.0
            spacing = None
        
        else:
            spacing = None
        
        for word in words:
        
            output.append((word._font, x, word.text))
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
    
    def render(self, svg, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        im = QImage(self.path)
        width = im.size().width()
        height = im.size().height()
        
        if self.scale:
            width = width * self.scale
            height = height * self.scale
        
        svg.add_image(x, y, width, height, self.path)
        
        return x + width, y + height


class Path:

    def __init__(self, bbox, elements, attributes = None, follow = False,
                 index = -1):
    
        self.bbox = bbox
        self.elements = elements
        self.attributes = attributes
        self.follow = follow
        self.index = index
    
    def render(self, svg, positions):
    
        x, y, width, height = self.bbox
        
        if self.follow:
            y = y + positions[self.index][1]
        
        svg.text += "<path "
        path = []
        
        for element in self.elements:
        
            path.append(element[0])
            absolute = element[0] == element[0].upper()
            
            for i in range(1, len(element)):
                if absolute:
                    if i % 2 == 1:
                        path.append(svg.ox + x + element[i])
                    else:
                        path.append(svg.oy + y + element[i])
                else:
                    path.append(element[i])
        
        svg.text += 'd="' + " ".join(map(str, path)) + '"'
        
        if self.attributes:
            for key, value in self.attributes.items():
                svg.text += ' %s="%s"' % (key, value)
        
        svg.text += " />\n"
        
        return x + width, y + height


class Clip:

    def __init__(self, rule, clip_path, elements):
    
        self.rule = rule
        self.clip_path = clip_path
        self.elements = elements
    
    def render(self, svg, positions):
    
        svg.text += '<g clip-rule="%s">\n' % self.rule
        svg.text += '<clipPath id="%s">\n' % id(self)
        x, y = self.clip_path.render(svg, positions)
        svg.text += '</clipPath>\n'
        
        for element in self.elements:
            element.attributes["clip-path"] = "url(#%s)" % id(self)
            element.render(svg, positions)
        
        svg.text += '</g>\n'
        
        return x, y


class Transform:

    def __init__(self, transformation, elements):
    
        self.transformation = transformation
        self.elements = elements
    
    def render(self, svg, positions):
    
        svg.text += '<g transform="translate(%f,%f) ' % (svg.ox, svg.oy)
        svg.text += ' '.join(map(lambda (k,v): '%s(%s)' % (k, v), self.transformation))
        svg.text += '">\n'
        
        ox, oy = svg.ox, svg.oy
        svg.ox, svg.oy = 0, 0
        
        for element in self.elements:
        
            x, y = element.render(svg, positions)
        
        svg.text += '</g>\n'
        svg.ox, svg.oy = ox, oy
        return x, y

# Font definitions

#sans = "FreeSans"
sans = "Futura Md BT"

regular = {"family": "FreeSans",
           "size": 25,
           "align": "justify"}

key_symbol = {"family": "FreeSans",
              "size": 27,
              "align": "centre"}

title = {"family": sans,
         "size": 30,
         "weight": "bold"}

subtitle = {"family": "FreeSans",
         "size": 25,
         "weight": "bold"}

italic_quote = {"family": "FreeSerif",
                "size": 28,
                "style": "italic",
                "left indent": 40,
                "right indent": 40}

quote = {"family": "FreeSerif",
         "size": 25,
         "style": "italic",
         "left indent": 10,
         "right indent": 10}

monospace_quote = {"family": "FreeMono",
                   "size": 25,
                   "left indent": 40,
                   "right indent": 40}

keys_quote = {"family": "FreeSans",
              "size": regular["size"],
              "left indent": 40,
              "right indent": 40}

key_descriptions_quote = {"family": "FreeSans",
                          "size": regular["size"],
                          "left indent": 160,
                          "right indent": 0}

exclamation = {"family": "FreeSerif",
               "size": 28,
               "style": "italic",
               "weight": "bold",
               "align": "centre"}

back_cover_title = {"family": "FreeSerif",
                    "size": 36,
                    "weight": "bold",
                    "align": "centre"}

back_cover_subtitle = {"family": "FreeSerif",
                       "size": 28,
                       "weight": "bold",
                       "align": "centre"}

back_cover_centred = {"family": sans,
                      "size": 40,
                      "align": "centre"}

back_cover_regular = {"family": sans,
                      "size": 40}

back_cover_small = {"family": sans,
                     "size": 24}

back_cover_publisher1 = {"family": sans, "size": 46,
                         "weight": "bold", "align": "centre",
                         "colour": "#202020"}

back_cover_publisher2 = {"family": sans, "size": 46,
                         "weight": "bold", "align": "centre",
                         "colour": "#ffffc0"}

front_cover_publisher1 = {"family": sans, "size": 34,
                          "weight": "bold", "align": "centre",
                          "colour": "#202020"}

front_cover_publisher2 = {"family": sans, "size": 34,
                          "weight": "bold", "align": "centre",
                          "colour": "#ffffc0"}

spine_publisher1 = {"family": sans, "size": 20,
                    "weight": "bold", "align": "centre",
                    "colour": "#202020"}

spine_publisher2 = {"family": sans, "size": 20,
                    "weight": "bold", "align": "centre",
                    "colour": "#ffffc0"}

front_cover_platforms = {"family": sans, "size": 36,
                         "weight": "bold", "align": "centre"}

front_cover_title = {"family": sans, "size": 56,
                     "weight": "bold", "align": "centre"}

spine_title = {"family": sans, "size": 42,
               "weight": "bold", "align": "centre"}

back_flap_text = {"family": "FreeSerif", "size": 32, "align": "centre"}

back_flap_bold_text = {"family": "FreeSerif", "size": 32,
                       "weight": "bold", "align": "centre"}

# Functions to generate common elements

def curved_box(x, y, w, h, style):

    r = w/10.0
    hr = r/2.0
    ll = w - (4 * r)
    
    return Path((x, y, w, h),
                 [("M",r,0), ("l",ll,0), ("c",hr,0,r,hr,r,r),
                  ("l",0,ll), ("c",0,hr,-hr,r,-r,r),
                  ("l",-ll,0), ("c",-hr,0,-r,-hr,-r,-r),
                  ("l",0,-ll), ("c",0,-hr,hr,-r,r,-r)], style)

def make_checkered(w, h, sx, sy, background = "#ffdd77"):

    checkered = []
    x = sx
    while x < w:
        checkered += [("M",x,0), ("l",0,h)]
        x += 20
    
    y = sy
    while y < h:
        checkered += [("M",0,y), ("l",w,0)]
        y += 20
    
    components = [int(background[1:][:2], 16),
                  int(background[1:][2:4], 16),
                  int(background[1:][4:], 16)]
    c = (min(components)/16) * 8
    line_colour = "#%02x%02x%02x" % (c, c, c)
    return Path((0, 0, w, h), checkered, {"stroke": line_colour, "stroke-width": 1})

def make_logo(cx, y, w, h, font1, font2):

    logo = []
    x = cx - (len("RETRO") * w)/2.0
    lr = h/10.0
    lhr = lr/2.0
    
    font2 = font2.copy()
    font2["colour"] = logo_background
    
    for ch in "RETRO":
        logo.append(curved_box(x - lhr, y + lr + lhr, w, h,
                               {"fill": logo_shadow, "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(curved_box(x + lr, y, w, h,
                               {"fill": logo_background, "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(TextBox((x + lr, y + lr + h/2 + 2, w - (lr * 2), h),
                            [Text(font1, ch)]))
        x += w
    
    x = cx - (len("SOFTWARE") * w)/2.0
    y += h
    
    for ch in "SOFTWARE":
        logo.append(curved_box(x - lhr, y + lr + lhr, w, h,
                               {"fill": logo_shadow, "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(curved_box(x + lr, y, w, h,
                               {"fill": "#202020", "stroke": "#000000",
                                "stroke-width": 2}))
        logo.append(TextBox((x + lr, y + lr + h/2 + 1, w - (lr * 2), h),
                            [Text(font2, ch)]))
        x += w
    
    return logo

def make_back_flap(r, hr, o, background):

    sbx = 200
    sbw = 600
    sbh = 200
    
    return Page((200, inlay_height),
                [Path((0, 0, 200, inlay_height),
                      [("M",0,0), ("l",670,0), ("l",0,inlay_height), ("l",-670,0), ("l",0,-inlay_height)],
                      {"fill": background, "stroke": "#000000", "stroke-width": 1}),
                 make_checkered(200, inlay_height, 10, 10, background),
                 Path((0, 0, 200, inlay_height),
                      [("M",200,0), ("l",-200,200), ("l",0,600), ("l",200,200), ("z",)],
                      {"fill": "white", "stroke": "#000000", "stroke-width": 1}),

                 Transform([("rotate", 90)],
                     [Transform([("translate", "0,-200")],
                          [TextBox((sbx - 20, 56, sbw + 40, sbh),
                               [Text(back_flap_text,
                                     u"Copyright \u00a9 2014 David Boddie"),
                                Text(back_flap_text,
                                     u"Licensed under the GNU GPL version 3 or later"),
                                Text(back_flap_text,
                                     u"An Infukor production for Retro Software"),
                                Text(back_flap_bold_text,
                                     u"http://www.retrosoftware.co.uk/")])
                          ])
                     ]),
                ])

def make_spine(w, r, hr, o, background):

    sbx = 10
    sby = -13
    sbw = inlay_height
    sbh = spine_width
    
    return Page((w, inlay_height), [
                Path((0, 0, w, inlay_height),
                     [("M",0,0), ("l",w,0),
                      ("l",0,inlay_height), ("l",-w,0),
                      ("l",0,-inlay_height)],
                      {"fill": background, "stroke": "none"}),
#                 make_checkered(w, inlay_height/2.0, 10, 10, background),

                Transform([("rotate", 90)],
                    [Transform([("translate", "0,0")], [
                        TextBox((sbx, sby, sbw, sbh), [
                            Text(spine_title, u"JUNGLE JOURNEY \u2013 B.B.C. MODEL B / ACORN ELECTRON")])
                        ])
                    ]),
                ])

def make_title_box(bx, by, bw, bh, r, hr, o, background = None):

    if not background:
        background = box_background
    
    return [Path((bx, by, bw, bh),
                 [("M",r,0), ("l",bw-(r*2),0), ("c",hr,0,r,r-hr,r,r),
                  ("l",0,bh-(r*2)), ("c",0,hr,-r+hr,r,-r,r),
                  ("l",-(bw-(r*2)),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                  ("l",0,-(bh-(r*2))), ("c",0,-hr,r-hr,-r,r,-r)],
                 {"fill": background, "stroke": "#000000", "stroke-width": 8})]

def make_vines(fx, fy, bw, bh):

    vines = []
    
    initials = [
        [["M",-100,250], ["q",100,-100,110,-190], ["q",10,-90,50,-140],
         ["q",40,-50,50,-100],["l",-10,0], ["q",-5,50,-50,100],
         ["q",-45,50,-50,140], ["q",-5,90,-120,180], ["z",]],
        [["M",bw-100,250], ["q",-90,-95,-105,-180], ["q",-10,-90,-50,-140],
         ["q",-40,-50,-50,-100],["l",10,0], ["q",5,50,50,100],
         ["q",45,50,50,140], ["q",5,90,120,180], ["z",]],
        ]

    ys = [245, 259]
    fs = [1.0, 1.1]
    level = 48
    
    while ys[0] > -50 and ys[1] > -50:
    
        for i, (y, f) in enumerate(zip(ys, fs)):
        
            path = initials[i][:]

            for element in path:
                t = element[0]
                if t == "M":
                    element[2] = y - 35
                elif t == "q":
                    element[1] = float(element[1]) * f + ((y % 10) - 5)
                    element[3] = float(element[3]) * f + ((y % 14) - 7)
                elif t == "l":
                    element[1] = float(element[1])

            red_level = ((level * 3.5) + 24) % 64

            vines.insert(0,
                Path((fx, fy - 50, bw, bh), map(tuple, path),
                     {"stroke": "#00%02x00" % (level/2), "stroke-width": 1,
                      "fill": "#%02x%02x00" % (red_level, level)}),
                )

            dy = (y % 63)
            y -= dy + 31
            f += 0.01 + (dy * 0.02)
            if f > 3.0: f -= 1.5
            ys[i] = y
            fs[i] = f
        
        level = max(0, level - 6)
    
    return vines

def make_eyes(bx, by, bw, bh):

    eyes = []

    c1 = "#604000"
    c2 = "#482800"
    c3 = "#503000"
    cx = bx + bw/2
    pos = [(cx, by + 115, 10, 5, c1),
           (cx - 120, by + 90, 8, 4, c2),
           (cx + 200, by + 15, 8, 4, c2),
           (cx - 330, by + 70, 8, 4, c1),
           (cx - 250, by + 180, 8, 4, c3),
           (cx + 110, by + 195, 8, 4, c3)]

    for (x, y, sx, sy, c) in pos:

        eyes.append(Path((bx, by, bw, bh),
            [("M",x,y), ("q",-sx,0,-sx,-sy), ("z",),
             ("m",sx*2,0), ("q",sx,0,sx,-sy), ("z",)],
            {"stroke": c, "stroke-width": 1, "fill": c}))

    return eyes

def make_front_cover(bx, bw, bh, title_by, title_bh, py, r, hr, o, background):

    # The imported fire paths need to be displaced.
    fx = bx + 100
    fy = py + 180

    # Front cover width
    fw = 1515

    ly1 = -20
    lh = 100
    lw = bw
    
    # Cave entrance position
    cy = (ly1 + (lh * 1.1)) + 180
    
    patterns = []
    
    for lx1, lx2, colour in ((0, lw/2, "#808040"), (lw/4, lw/2.5, "#804020")):
    
        points = []
        
        for i in range(1, 17):
        
            lx = bx - bw/2
            ly = ly1 + lh * (1.1 ** i)
            
            if i % 2 == 0:
                points.append((lx1 * ((16 - i)/16.0)**0.25, ly))
            else:
                points.append((lx2 - (((i/16.0)**3) * (lx2 - lx1)), ly))
        
        style = {"fill": "black", "fill-opacity": "0.4",
                 "stroke": "none"}
        
        patterns.append(Path((bx, fy, bw, bh),
                             [("M",) + points[0]] + \
                             map(lambda p: ("L",) + p, points[1:]) + \
                             [("L",points[-1][0], points[0][1]), ("z",)], style))
        patterns.append(Path((bx, fy, bw, bh),
                             [("M",lw - points[0][0], points[0][1])] + \
                             map(lambda p: ("L",lw-p[0],p[1]), points[1:]) + \
                             [("L",lw-points[-1][0], points[0][1]), ("z",)], style))
    
    # Eyes
    eyes = make_eyes(bx, py - 120, bw, bh)
    
    # Vines
    vines = make_vines(fx, fy, bw, bh)
    
    border = Path((bx, py, bw, bh),
                  [("M",r,0), ("l",bw-(r*2),0), ("c",hr,0,r,r-hr,r,r),
                   ("l",0,bh-(r*2)), ("c",0,hr,-r+hr,r,-r,r),
                   ("l",-(bw-(r*2)),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                   ("l",0,-(bh-(r*2))), ("c",0,-hr,r-hr,-r,r,-r)],
                  {"fill": "none", "stroke": "#000000", "stroke-width": 8})
    
    return Page((fw, inlay_height), [Transform([("scale", "2.0,2.0")],
                [Path((0, 0, fw/2.0, inlay_height/2.0),
                      [("M",0,0), ("l",fw/2.0,0), ("l",0,inlay_height/2.0),
                       ("l",-fw/2.0,0), ("l",0,-inlay_height/2.0)],
                      {"fill": background, "stroke": "none"}),
                 make_checkered(fw/2.0, inlay_height/2.0, 10, 10, background)

                ] + make_title_box(bx, title_by, bw, title_bh, r, hr, o) + [

                 TextBox((bx, title_by + 44, bw, title_bh-(r*2)),
                     [Text(front_cover_platforms, "%s" % platform.upper()),
                      Text(front_cover_title, "JUNGLE JOURNEY")],
                      line_spacing = 1.25)

                ] + make_logo(bx + bw/2.0, 40, 50, 50, front_cover_publisher1, front_cover_publisher2) + \

                [Path((bx, py, bw, bh),
                      [("M",r,0), ("l",bw-(r*2),0), ("c",hr,0,r,r-hr,r,r),
                       ("l",0,bh-(r*2)), ("c",0,hr,-r+hr,r,-r,r),
                       ("l",-(bw-(r*2)),0), ("c",-hr,0,-r,-r+hr,-r,-r),
                       ("l",0,-(bh-(r*2))), ("c",0,-hr,r-hr,-r,r,-r)],
                      {"fill": "url(#box-background)", "stroke": "none", "stroke-width": 4}),

                 Path((bx, py, bw, bh),
                      [("M",bw/4.0,cy), ("l",bw/2.0,0), ("c",0,-cy/3.0,-bw/8.0,-cy/2.0,-bw/4.0,-cy/2.0),
                       ("c",-bw/8.0,0,-bw/4.0,cy/6.0,-bw/4.0,cy/2.0)],
                      {"fill": "black", "stroke": "none", "stroke-width": 4}),

                 Clip('nonzero', border, patterns + eyes + vines),

                 # Imported from fire.svg:
                 Path((fx, fy, bw, bh),
                      [("M",88.707259,238.30335),
                       ("c",0,35.27777,70.555561,52.91666,122.972231,53.41666),
                       ("c",53.41667,-0.5,123.97223,-18.13889,123.97223,-53.41666),
                       ("c",0,-35.27778,-88.19445,-35.27778,-123.97223,-34.77779),
                       ("c", -34.77778,-0.49999,-122.972231,-0.49999,-122.972231,34.77779),
                       ("z",)],
                      {"fill": "url(#inside-bowl)", "stroke": "black", "stroke-width": "1px"}),

                 Path((fx, fy, bw, bh),
                      [("M",123.98504,229.4839),
                       ("c",9.27886,-8.36003,18.801,-19.11629,17.63889,-35.27778),
                       ("c",-1.16211,-16.16149,-4.22518,-33.04545,-17.63889,-44.09722),
                       ("c",-13.41372,-11.05176,-26.077061,-11.77625,-26.458341,-26.45833),
                       ("c",-0.38128,-14.68209,2.22203,-20.00822,8.819451,-35.277783),
                       ("c",6.59742,-15.26955,16.63157,-25.19739,26.45833,-35.27778),
                       ("c",0,0,-11.20933,17.34542,-8.81944,35.27778),
                       ("c",2.38989,17.932363,5.82121,31.773373,17.63889,44.097223),
                       ("c",9.46579,11.11291,21.17809,24.85942,26.45833,35.27778),
                       ("c",5.28025,10.41837,7.34955,17.57612,8.81945,26.45833),
                       ("c",1.4699,8.8822,0,16.57939,0,26.45834),
                       ("c",9.79149,-11.69237,18.67431,-28.17019,17.63889,-44.09723),
                       ("c",-1.03542,-15.92704,-5.22817,-15.5927,-8.81945,-17.63889),
                       ("c",-3.59127,-2.04619,-21.08966,-11.78716,-26.45833,-26.45833),
                       ("c",-5.36867,-14.67116,0,-26.45833,0,-26.45833),
                       ("c",4.61918,9.65974,7.69986,20.34516,17.63889,26.45833),
                       ("c",7.59563,6.6955,17.3504,12.04578,26.45833,17.63889),
                       ("c",9.10793,5.59311,9.12086,16.55848,8.81945,26.45833),
                       ("c",-0.779,9.89986,-7.49133,16.49486,-8.81945,26.45834),
                       ("c",-1.32812,9.96348,-0.56603,17.01802,8.81945,17.63889),
                       ("c",22.84497,-15.36624,26.60192,-37.30921,17.63889,-52.91667),
                       ("c",-8.89136,-15.48267,-34.53864,-42.66715,-17.63889,-61.73611),
                       ("c",7.98886,-9.014303,-11.90155,-14.556783,-17.63889,-17.638893),
                       ("c",-17.63889,-8.81944,-17.63889,-8.81944,-26.45834,-17.63889),
                       ("c",-8.16124,-8.16124,-8.71343,-17.63732,-8.81944,-26.45833),
                       ("c",-0.14163,-11.78491,8.81944,-26.45834,17.63889,-26.45834),
                       ("c",0,0,-13.22917,13.22917,-8.81945,26.45834),
                       ("c",4.40972,13.22917,3.80985,18.73765,17.63889,26.45833),
                       ("c",11.15938,6.23023,25.14634,4.20201,35.27778,8.81945),
                       ("c",8.13619,3.70809,15.21989,13.65462,17.63889,26.458333),
                       ("c",1.75448,9.28642,-7.39757,17.63136,-8.81944,26.45833),
                       ("c",-1.86192,11.55879,10.48406,19.1867,17.63889,26.45833),
                       ("c",14.2667,14.4996,15.90342,39.49975,17.63889,61.73612),
                       ("c",10.7132,-13.24901,29.29354,-30.27928,17.63889,-44.09723),
                       ("c",-6.78584,-8.0454,-16.16045,-10.06706,-17.63889,-17.63889),
                       ("c",-3.47873,-17.81629,7.93617,-31.38135,17.63889,-44.09721),
                       ("c",5.42085,-7.10427,2.48458,-13.06114,0,-17.638893),
                       ("c",-6.8881,-12.69106,-17.63889,-17.85113,-26.45834,-26.45834),
                       ("c",14.69908,6.62336,29.62411,10.72836,44.09723,26.45834),
                       ("c",6.42668,6.984783,15.61508,19.208523,8.81944,26.458333),
                       ("c",-13.18207,14.06303,-17.71378,33.50413,-8.81944,52.91666),
                       ("c",5.03027,10.97893,16.73498,18.5428,8.81944,44.09723),
                       ("c",11.35952,6.2666,16.44766,11.35474,16.44766,21.53102),
                       ("c",-5.08814,25.44071,-28.60399,38.56265,-42.90599,57.84398),
                       ("l",-70.55556,8.81944),
                       ("l",-70.55556,-17.63889),
                       ("l",-35.27778,-26.45833),
                       ("l",0,-17.63889),
                       ("l",17.63889,-17.63889), ("z",)],
                      {"fill": "url(#linearGradient10534)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",132.92609,220.66446),
                       ("c",26.3046,-41.5837,-29.51506,-48.52596,-26.45833,-79.375),
                       ("c",-0.38128,-14.68208,13.70473,-17.9216,35.27778,-35.27777),
                       ("c",21.57305,-17.356173,16.34196,-27.539123,8.81944,-44.097233),
                       ("c",48.48092,40.077823,-61.989181,63.707373,17.63889,105.833333),
                       ("c",17.62222,13.98537,0,17.63889,17.63889,44.09723),
                       ("c",-18.46211,-49.82078,26.51469,-55.59628,8.81945,-88.19444),
                       ("c",-12.64518,-18.04369,-16.89662,-23.60165,-26.45834,-35.277783),
                       ("c",-9.56172,-11.67614,35.27778,-52.91667,35.27778,-52.91667),
                       ("c",-8.81944,17.63889,-27.57792,37.98404,-17.63889,44.09722),
                       ("c",7.59563,6.6955,22.32924,19.88598,35.27778,35.277783),
                       ("c",12.94854,15.39179,13.81641,52.87632,-8.81945,79.375),
                       ("c",-1.32812,9.96348,-0.56603,17.01802,8.81945,17.63889),
                       ("c",22.84497,-15.36624,26.60192,-37.30921,17.63889,-52.91667),
                       ("c",-8.81944,-39.68749,26.45834,-52.91666,21.12717,-84.319573),
                       ("c",14.15061,22.58346,10.67185,25.623513,5.33117,40.222353),
                       ("c",-5.34068,14.59883,-14.26083,7.92422,-8.81945,35.27777),
                       ("c",3.83884,19.29765,12.86019,39.49975,17.63889,61.73612),
                       ("c",10.7132,-13.24901,11.65465,-21.45983,0,-35.27778),
                       ("c",-22.09426,-19.48035,0.17477,-55.63579,8.81945,-70.55555),
                       ("c",8.64468,-14.919773,-8.81945,-44.097233,8.81944,-52.916673),
                       ("c",-8.81944,8.81944,0,26.45833,8.81945,44.09722),
                       ("c",8.81944,17.638893,-26.45834,61.736113,-8.81945,79.375003),
                       ("c",17.63889,17.63889,-7.75782,27.63679,18.70051,45.27568),
                       ("c",0,0,15.26443,5.08814,16.45566,16.46043),
                       ("c",-1.19123,19.15656,-16.45566,39.50912,-35.15617,52.91667),
                       ("l",-70.55556,8.81944),
                       ("l",-70.67717,-8.81945),
                       ("c",-35.27778,0,-57.326391,-44.09721,-52.916671,-52.91666),
                       ("c",4.409721,-8.81944,17.638891,-17.63889,35.399391,-17.63889),
                       ("z",)],
                       {"fill": "url(#linearGradient10558)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",238.63782,304.44917),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",273.9156,308.85889),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",159.26282,308.85889),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),
                       
                 Path((fx, fy, bw, bh),
                      [("M",185.72115,286.81028),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",243.04755,260.35195),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),
                       
                 Path((fx, fy, bw, bh),
                      [("M",141.62393,273.58112),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",203.36004,313.26862),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",106.34615,362.27557),
                       ("c",0,26.45834,52.91667,52.91667,105.83334,52.91667),
                       ("c",52.41667,0.50001,105.83334,-26.45833,105.83334,-52.91667),
                       ("c",0,-26.45834,-52.91667,-35.27778,-105.83334,-35.27778),
                       ("c",-52.91667,0,-105.83334,8.81944,-105.83334,35.27778),
                       ("z",)],
                      {"fill": "black", "fill-opacity": "0.5", "stroke": "black",
                       "stroke-width": "1px"}),

                 Path((fx, fy, bw, bh),
                      [("M",88.707259,238.30335),
                       ("c",0,35.27777,35.277781,141.11112,123.472231,141.11111),
                       ("c",88.19444,10e-6,123.47222,-105.83334,123.47223,-141.11111),
                       ("c",-17.6389,35.27777,-70.55556,52.91666,-123.47223,52.91666),
                       ("c",-52.91667,0,-105.83334,-17.63889,-123.472231,-52.91666),
                       ("z",)],
                      {"fill": "url(#linearGradient10405)",
                       "stroke": "black", "stroke-width": "1px"}),

                 Path((fx, fy, bw, bh),
                      [("M",260.68643,282.40056),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",220.99893,282.40056),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",291.55449,273.58112),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",172.49199,260.35196),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 Path((fx, fy, bw, bh),
                      [("M",207.76977,255.94224),
                       ("l",-17.63889,-17.63888),
                       ("l",17.63889,-17.63889),
                       ("l",17.63889,17.63889),
                       ("l",-17.63889,17.63888), ("z",)],
                      {"fill": "url(#ember)", "stroke": "none"}),

                 # Drawing border
                 border
                ])
            ])

def key_tops(bx, by, bw):

    mx = 40
    sx = sy = 24
    ex = ey = 8
    p1 = 880
    p2 = 1250

    paths = [
        TextBox((mx + (bx * 4), by + p1, bw * 2, 0), [Text(regular, "up")]),
        TextBox((mx + (bx * 2.5) - 4, by + p1 + 90, bw * 2, 0), [Text(regular, "left")]),
        TextBox((mx + (bx * 5.5) - 4, by + p1 + 90, bw * 2, 0), [Text(regular, "right")]),
        TextBox((mx + (bx * 4) - 16, by + p1 + 180, bw * 2, 0), [Text(regular, "down")]),
        TextBox((mx + (bx * 2.75), by + p2, bw * 2, 0), [Text(regular, "enable sound effects")]),
        TextBox((mx + (bx * 2.75), by + p2 + 55, bw * 2, 0), [Text(regular, "disable sound effects")]),
        TextBox((mx + (bx * 7.75), by + p2, bw * 2, 0), [Text(regular, "pause the game")]),
        TextBox((mx + (bx * 7.75), by + p2 + 55, bw * 2, 0), [Text(regular, "resume the game")])
        ]

    pos = [(mx + bx * 4, by + p1 + 40, ":"),
           (mx + bx * 4, by + p1 + 140, "/"),
           (mx + bx * 3.25, by + p1 + 90, "Z"),
           (mx + bx * 4.75, by + p1 + 90, "X"),
           (mx + bx * 2, by + p2, "S"),
           (mx + bx * 2, by + p2 + 55, "Q"),
           (mx + bx * 7, by + p2, "P"),
           (mx + bx * 7, by + p2 + 55, "O")]

    for x, y, ch in pos:
        paths += [
            Path((x, y, sx + (ex * 2), sy + (ey * 2)),
                 [("M",0,-ey/2 - 2 -sy), ("l",sx,0), ("q",ex,0,ex,ey),
                  ("l",0,sy), ("q",0,ey,-ex,ey), ("l",-sx,0),
                  ("q",-ex,0,-ex,-ey), ("l",0,-sy), ("q",0,-ey,ex,-ey),
                  ("z",)],
                 {"stroke": "black", "fill": "none", "stroke-width": 1}),
            TextBox((x, y, sx, 0), [Text(key_symbol, ch)])
            ]

    x, y, sx, sy = mx + (bx * 8), by + p1 + 90, 100, 24

    paths += [
        Path((x, y, sx + (ex * 2), sy + (ey * 2)),
             [("M",0,-ey/2 - 2 -sy), ("l",sx,0), ("q",ex,0,ex,ey),
              ("l",0,sy), ("q",0,ey,-ex,ey), ("l",-sx,0),
              ("q",-ex,0,-ex,-ey), ("l",0,-sy), ("q",0,-ey,ex,-ey),
              ("z",)],
             {"stroke": "black", "fill": "none", "stroke-width": 1}),
        TextBox((x, y, sx, 0), [Text(key_symbol, "Return")]),

        TextBox((mx + (bx * 10), y, bw * 2, 0), [Text(regular, "fire weapon")]),
        TextBox((mx + (bx * 8), by + p1 + 135, bw * 2, 0), [
                Text(regular, "There are four different types of "
                              "weapon available in the game.\n\n")])
        ]

    x, y, sx, sy = mx + (bx * 11.5), by + p2, 100, 24

    paths += [
        Path((x, y, sx + (ex * 2), sy + (ey * 2)),
             [("M",0,-ey/2 - 2 -sy), ("l",sx,0), ("q",ex,0,ex,ey),
              ("l",0,sy), ("q",0,ey,-ex,ey), ("l",-sx,0),
              ("q",-ex,0,-ex,-ey), ("l",0,-sy), ("q",0,-ey,ex,-ey),
              ("z",)],
             {"stroke": "black", "fill": "none", "stroke-width": 1}),
        TextBox((x, y, sx, 0), [Text(key_symbol, "Escape")]),

        TextBox((mx + (bx * 13.4), y, bw * 2, 0),
            [Text(regular, "return to the title screen")])
        ]

    return paths


if __name__ == "__main__":

    app = QApplication([])
    
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: %s <output file>\n" % sys.argv[0])
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    platform = "BBC Micro/Electron"
    
    r = 25
    hr = 0.5*r
    
    # Inlay/page height
    inlay_height = 2160
    
    # Cover width (front and back)
    cover_width = 1515
    spine_width = 60
    
    # Background colour
    background = "#105818"
    spine_background = "#186820"
    box_background = "#ffffff"
    box_shadow = "#ffb060"
    logo_background = "#ffffc0"
    logo_shadow = "#ff4040"
    
    # Placement of boxes on the front cover
    bx = 70
    bw = (1515 - (bx * 4))/2.0
    bh = bw
    # Title box vertical position and height
    tby = 165
    tbh = 115
    
    # Picture position
    py = 310
    
    # Shadow offset
    o = 0.32 # 1 - 1/(2**0.5)
    
    # Screenshot scale and horizontal positions
    sh = 256
    scale = sh/512.0
    sw = scale * 640
    sr = (bw - (2 * sw))/3.0
    
    back_flap = make_back_flap(r, hr, o, background)
    spine = make_spine(spine_width, r, hr, o, spine_background)
    front_cover = make_front_cover(bx, bw, bh, tby, tbh, py, r, hr, o, background)
    
    instructions = [
        Page((cover_width, inlay_height),
            [Path((0, 0, cover_width, inlay_height),
                   [("M",0,0), ("l",cover_width,0),
                    ("l",0,inlay_height), ("l",-cover_width,0),
                    ("l",0,-inlay_height)],
                   {"fill": background, "stroke": "none"}),
             Transform([("scale", "2.0,2.0")],
                [make_checkered(cover_width/2.0, inlay_height/2.0, 10, 10, background)] + \
                 make_title_box(bx/2.0, 30, bw + bx, 750, r, hr, o) + \
                 make_title_box(bx/2.0, 800, bw + bx, 250, r, hr, o))] + \
                 
#             make_title_box(bx + bw - sw - 18, 109, sw + 18, sh + 14, r, hr, o, "black") + \
#             make_title_box(bx, 109, sw + 18, sh + 14, r, hr, o, "black") + \

            [
#             Image((bx + 9, 109 + 9, sw, 0), "../images/screenshot1.png", scale = scale),
#             Image((bx + bw - sw - 9, 109 + 9, sw, 0), "../screenshot2.png", scale = scale),
             TextBox((bx * 2, 1669, bw * 2, 0),
                [Text(back_cover_centred,
                      u"Copyright \u00a9 2011 David Boddie\n"
                      u"An Infukor production for Retro Software\n"
                      u"http://www.retrosoftware.co.uk/")]),
             TextBox((bx * 2, 1819, bw * 2, 0),
                [Text(back_cover_small,
                      "This program is free software: you can redistribute it and/or modify "
                      "it under the terms of the GNU General Public License as published by "
                      "the Free Software Foundation, either version 3 of the License, or "
                      "(at your option) any later version.\n"
                      "\n"
                      "This program is distributed in the hope that it will be useful, "
                      "but WITHOUT ANY WARRANTY; without even the implied warranty of "
                      "MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the "
                      "GNU General Public License for more details.\n"
                      "\n"
                      "You should have received a copy of the GNU General Public License "
                      "along with this program.\nIf not, see <http://www.gnu.org/licenses/>.")])
            ] + \
                #make_logo(bx/2.0 + 670 - 35, 50, 70, 70, back_cover_publisher1, back_cover_publisher2)
            [TextBox((bx * 2, 120, bw * 2, 0), 
                 [Text(title, "Jungle Journey")]),
             TextBox((bx * 2, 12, bw * 2, 0),
                 [Text(regular,
                       "The last flames of the campfire fade to glowing embers and I am alone. "
                       "My recent acquaintances, their packs and paraphernalia have gone, leaving "
                       "me stranded deep in the heart of this jungle realm.")],
                 line_spacing = 1.1, follow = True),
             TextBox((bx * 2, 10, bw * 2, 0),
                 [Text(regular,
                       "Clouds momentarily "
                       "sweep the cold face of the moon and I perceive the clicks, whistles and "
                       "cries of creatures in the hot air that cloaks this place. Desperately, I "
                       "try to stay my panic and remember those fragments of wilderness craft "
                       "learned and unlearned many years ago.")],
                 line_spacing = 1.1, follow = True),
             TextBox((bx * 2, 15, bw * 2, 0),
                 [Text(italic_quote,
                       "Choose your weapon carefully, get ready for a fight.\n"
                       "The jungle can be dangerous if you go there at night.\n"
                       "There's time to pick up treasure, but no time to stop and stare.\n"
                       "If you don't find the hidden cave you won't get out of there.")],
                 line_spacing = 1.1, follow = True),
             TextBox((bx * 2, 15, bw * 2, 0),
                 [Text(regular,
                       "Hopeless, I scramble to my feet, reaching for any weapon still left to me. "
                       "Struggling through the dense undergrowth, I search for signs of a track or "
                       "trail. At first glance, paths that seemed to lead to safety turn out to be "
                       "impassable, overgrown by tangled and twisted vines. I remember the words of "
                       "an old teacher:")],
                 line_spacing = 1.1, follow = True),
             TextBox((bx * 2, 15, bw * 2, 0),
                 [Text(italic_quote,
                       u'\u201cDo not be tempted to use fire to make your way. '
                       'Many a traveller has strayed from the path, using fire to blaze a trail, '
                       'only to reach a dead end. Trying to return, they find that the jungle '
                       'has grown back. Those who are desperate enough will even seek out '
                       u'forgotten routes when the way home is in sight.\u201d')],
                 line_spacing = 1.0, follow = True),
             TextBox((bx * 2, 15, bw * 2, 0),
                 [Text(regular,
                       "Sensing my presence, obscene creatures emerge from the darkness, hungry "
                       "for prey. Only through skill and luck am I able to dispatch them back "
                       "into the shadows. Even though I know I must journey deeper into this "
                       "uncharted land to find the way home, the thought of vengeance drives me on.")],
                 line_spacing = 1.1, follow = True),

             TextBox((bx * 2, 24, bw * 2, 0),
                 [Text(subtitle, "Playing the Game")],
                 follow = True),
             TextBox((bx * 2, 10, bw * 2, 0),
                 [Text(regular,
                       "The player must help the character reach the exit for each level. However, the "
                       "player must first find a key to unlock the exit. On the final level, the exit "
                       "does not require a key but it may be obstructed. Enemies will appear in each "
                       "location and attack the player's character. They can be destroyed by "
                       "projectiles fired by the current weapon.")],
                 line_spacing = 1.1, follow = True),
             TextBox((bx * 2, 8, bw * 2, 0),
                 [Text(regular,
                       "Your character can move around the screen and fire using these keys:\n")],
                 line_spacing = 1.1, follow = True),
             TextBox((bx * 2, 230, bw * 2, 0),
                 [Text(regular,
                       "Alternatively, you may play using an analogue joystick. Select joystick controls by "
                       "pressing the Fire button on the title page to start the game. Press Space to "
                       "start the game with keyboard controls.\n\n"
                       "Other keys can be used to pause, unpause or exit the "
                       "game, and enable or disable sound effects:\n")],
                 line_spacing = 1.1, follow = True),
             TextBox((bx * 2, 140, bw * 2, 0),
                 [Text(regular, "Good luck on your journey!")], follow = True)

            ] + key_tops(bx, 140, bw))
        ]
    
    defs = ('<linearGradient id="box-background" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#081800" />\n'
            '  <stop offset="0.15" stop-color="#000000" />\n'
            '  <stop offset="0.5" stop-color="#000800" />\n'
            '  <stop offset="1" stop-color="#205c00" />\n'
            '</linearGradient>\n'
            '<linearGradient id="cave" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#180800" />\n'
            '  <stop offset="1" stop-color="#040000" />\n'
            '</linearGradient>\n'
            '<linearGradient id="hills" x1="0%" y1="0%" x2="100%" y2="100%">\n'
            '  <stop offset="20%" stop-color="#003000" />\n'
            '  <stop offset="100%" stop-color="#001000" />\n'
            '</linearGradient>\n'
            '<linearGradient id="distant-hills" x1="0%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="20%" stop-color="#002000" />\n'
            '  <stop offset="100%" stop-color="#000000" />\n'
            '</linearGradient>\n'
            '<linearGradient id="walls" x1="0%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="0%" stop-color="#603030" />\n'
            '  <stop offset="100%" stop-color="#502020" />\n'
            '</linearGradient>\n'
            '<linearGradient id="dark-walls" x1="0%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="0%" stop-color="#401010" />\n'
            '  <stop offset="100%" stop-color="#301010" />\n'
            '</linearGradient>\n'
            '<linearGradient id="path" x1="100%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="0%" stop-color="#303030" />\n'
            '  <stop offset="100%" stop-color="#404040" />\n'
            '</linearGradient>\n'
            '<linearGradient id="lit-window" x1="10%" y1="0%" x2="0%" y2="100%">\n'
            '  <stop offset="50%" stop-color="#00000" />\n'
            '  <stop offset="100%" stop-color="#de8600" />\n'
            '</linearGradient>\n'
            '<linearGradient id="inside-bowl" x1="50" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#400000" />\n'
            '  <stop offset="0.74074072" stop-color="#c22d00" />\n'
            '  <stop offset="1" stop-color="#d82724" />\n'
            '</linearGradient>\n'
            '<linearGradient id="linearGradient10534" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#ffff00" />\n'
            '  <stop offset="0.47083142" stop-color="#f57f00" />\n'
            '  <stop offset="0.65192044" stop-color="#eb0000" />\n'
            '  <stop offset="1" stop-color="#d82724" />\n'
            '</linearGradient>\n'
            '<linearGradient id="linearGradient10558" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#c85c00" />\n'
            '  <stop offset="0.47083142" stop-color="#f57f00" />\n'
            '  <stop offset="0.65192044" stop-color="#eb3700" />\n'
            '  <stop offset="1" stop-color="#a2311b" />\n'
            '</linearGradient>\n'
            '<radialGradient id="ember" cx="50%" cy1="50%" fx="50%" fy="50%" r="50%">\n'
            '  <stop offset="0" stop-color="#ffff7f" />\n'
            '  <stop offset="0.5" stop-color="#ffff00" />\n'
            '  <stop offset="0.9" stop-color="#ff2724" />\n'
            '  <stop offset="1" stop-color="#d82724" />\n'
            '</radialGradient>\n'
            '<linearGradient id="linearGradient10405" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#400000" />\n'
            '  <stop offset="0.74074072" stop-color="#ff3f00" />\n'
            '  <stop offset="1" stop-color="#d82724" />\n'
            '</linearGradient>\n'
            '<linearGradient id="cave-outside" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#000000" />\n'
            '  <stop offset="0.25" stop-color="#040404" />\n'
            '  <stop offset="1" stop-color="#101010" />\n'
            '</linearGradient>\n'
            )
    
    pages = instructions + [spine, front_cover]
    
    page_rects = [((0, 0, cover_width, inlay_height), False),
                  ((cover_width, 0, spine_width, inlay_height), False),
                  ((cover_width + spine_width, 0, 1515, inlay_height), False)]
    
    total_size = (3390, 2460)
    
    dx = 150
    dy = 150
    
    for i in range(len(page_rects)):
        rect, rev = page_rects[i]
        page_rects[i] = ((rect[0] + dx, rect[1] + dy,) + rect[2:], rev)
    
    inlay = Inlay(output_file, page_rects, total_size)
    inlay.open()
    inlay.add_defs(defs)
    
    i = 0
    for page in pages:
        page.render(inlay)
        i += 1
    
    inlay.close()
    
    sys.exit()
