#!/usr/bin/env python3

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
from PyQt5.QtCore import QSize
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

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
        if "weight" in font:
            self.text += '      font-weight="%s"\n' % font["weight"]
        if "style" in font:
            self.text += '      font-style="%s"\n' % font["style"]
        if "colour" in font:
            self.text += '      fill="%s"\n' % font["colour"]
        self.text += '>\n'
        self.text += self._escape(text)
        self.text += '</text>\n'
    
    def close(self):
    
        self.text += "</svg>\n"
        codecs.open(self.path, "w", "utf-8").write(self.text)


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
            total_width = sum([word.width() for word in words])
            spacing = (width - total_width)/float(len(words) - 1)
        
        elif self.font.get("align", "left") == "centre":
            # Centre the text.
            total_width = sum([word.width() for word in words])
            total_space = sum([word.space() for word in words][:-1])
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
        svg.text += ' '.join(['%s(%s)' % (k, v) for(k,v) in self.transformation])
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

title = {"family": sans,
         "size": 30,
         "weight": "bold"}

subtitle = {"family": "FreeSans",
         "size": 25,
         "weight": "bold"}

front_cover_publisher1 = {"family": sans, "size": 22,
                          "weight": "bold", "align": "centre",
                          "colour": "#202020"}

front_cover_publisher2 = {"family": sans, "size": 22,
                          "weight": "bold", "align": "centre",
                          "colour": "#ffffc0"}

front_cover_title = {"family": sans, "size": 56,
                     "weight": "bold", "align": "centre", "colour": "white"}

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
    
    x = cx - (len("POWER") * w)/2.0
    y += h
    
    for ch in "POWER":
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

            red_level = int((level * 3.5) + 24) % 64

            vines.insert(0,
                Path((fx, fy - 50, bw, bh), list(map(tuple, path)),
                     {"stroke": "#00%02x00" % (level//2), "stroke-width": 1,
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
           (cx - 270, by - 50, 8, 4, c3),
           (cx + 110, by - 55, 8, 4, c3)]

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
                             [(("L",) + p) for p in points[1:]] + \
                             [("L",points[-1][0], points[0][1]), ("z",)], style))
        patterns.append(Path((bx, fy, bw, bh),
                             [("M",lw - points[0][0], points[0][1])] + \
                             [("L",lw-p[0],p[1]) for p in points[1:]] + \
                             [("L",lw-points[-1][0], points[0][1]), ("z",)], style))
    
    # Eyes
    eyes = make_eyes(30, py - 120, bw, bh)
    
    # Vines
    vines = make_vines(fx, fy, bw, bh)
    
    border = Path((bx, py, bw, bh),
                  [("M",0,-bh/4), ("l",bw,0), ("l",0,1.25*bh), ("l",-bw,0), ("l",0,-1.25*bh)],
                  {"fill": "none", "stroke": "#000000", "stroke-width": 8})
    
    # Calculate the scale factor based on the target dimensions and drawing
    # dimensions.
    scale = 2100. / bw # 2970 / (bh*1.414286)
    dy = py - (bh*0.414286)

    return Page((2100, 2970), [Transform([("scale", "%f,%f" % (scale, scale)), ("translate", "0,%f" % -dy)],
                [Path((bx, py, bw, bh),
                      [("M",0,-bh*0.414286), ("l",bw,0), ("l",0,1.414286*bh), ("l",-bw,0), ("l",0,-1.414286*bh)],
                      {"fill": "url(#box-background)", "stroke": "none", "stroke-width": 4}),

                 Path((bx, py, bw, bh),
                      [("M",bw/4.0,cy), ("l",bw/2.0,0), ("c",0,-cy/3.0,-bw/8.0,-cy/2.0,-bw/4.0,-cy/2.0),
                       ("c",-bw/8.0,0,-bw/4.0,cy/6.0,-bw/4.0,cy/2.0)],
                      {"fill": "black", "stroke": "none", "stroke-width": 4}),

                 Clip('nonzero', border, patterns + vines),

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
                      {"fill": "url(#outside-bowl)",
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

                 Path((bx, py, bw, bh),
                      [("M",0,-bh/4), ("l",bw,0), ("l",0,bh/3.5), ("l",-bw,0), ("l",0,-bh/3.5)],
                      {"fill": "url(#box-fade)", "stroke": "none", "stroke-width": 4}),

                 Transform([("translate", "%i,%i" % (bw*0.3, -py*2.0)),
                            ("scale", "2.5,2.5")], [
                     Path((bx, py, bw, bh), [
                        # J
                           ("M",-5,-1), ("m",0,2.70833),
                           ("c",0,1.35417, 0,1.35417, 1.35417,1.35417),
                           ("l",5.41666,0), ("l",0,13.1875),
                           ("c",0,1.35417, -1.35416,2.70833, -2.70833,2.70833),
                           ("c",-1.35416,0, -2.70833,-1.35416, -2.70833,-2.70833),
                           ("l",-2.70834,0), ("l",0,1.35417),
                           ("c",0,2.70833, 2.70834,5.41666, 6.77084,5.41666),
                           ("c",2.70833,0, 5.41666,-2.70833, 5.41666,-5.41666),
                           ("l",0,-14.54167), ("l",5.41667,0), ("l",0,-1.70833),
                           ("c",0,-1.35417, 0,-1.35417, -1.35417,-1.35417),
                           ("l",-14.89583,0), ("z",),
                        # U
                           ("M",13.95834,0), ("m",4.0625,0),
                           ("l",0,14.89583), ("c",0,1.35417, 1.35416,4.0625, 4.06249,4.0625),
                           ("l",1.35417,0), ("c",2.70834,0, 4.0625,-2.70833, 4.0625,-4.0625),
                           ("l",0,-14.89583), ("l",4.0625,0), ("l",0,16.25),
                           ("c",0,2.70833, -2.70833,6.77083, -8.125,6.77083),
                           ("l",-1.35417,0), ("c",-5.41667,0, -8.12499,-4.0625, -8.12499,-6.77083),
                           ("l",0,-16.25), ("z",),
                        # N
                           ("M",34.27084,0), ("l",0,23.02083),
                           ("l",4.0625,0), ("l",0,-16.25), ("l",10.83333,16.25),
                           ("l",4.0625,0), ("l",0,-21.66666),
                           ("c", 0,-1.35417, 0,-1.35417, -1.35417,-1.35417),
                           ("l",-2.70833,0), ("l",0,16.25), ("l",-10.83333,-16.25),
                           ("l",-4.0625,0), ("z",),
                        # G
                           ("M",55.9375,10.83333),
                           ("c",0,-5.41667, 2.70834,-10.83333, 8.125,-10.83333),
                           ("c",4.00919,0.3847, 6.71753,0.3847, 8.0717,5.80137),
                           ("l",-2.65503,0.96946),
                           ("c",0,-2.70833, -2.70833,-2.70833, -4.0625,-2.70833),
                           ("c",-2.70833,0, -5.41667,1.35416, -5.41667,6.77083),
                           ("c",0,5.41667, 2.70834,8.125, 5.41667,8.125),
                           ("c",2.70833,0, 5.41667,-1.35416, 5.41667,-4.0625),
                           ("l",-2.70834,0), ("l",0,-2.70833), ("l",5.41667,0),
                           ("l",0,4.0625),
                           ("c",0,4.0625, -2.70833,6.77083, -8.125,6.77083),
                           ("c",-6.77083,0, -9.47917,-5.41666, -9.47917,-12.1875),
                           ("z",),
                        # L
                           ("M",76.40355,22.86729), ("l",13.54167,0),
                           ("c",1.35416,0, 1.35416,0, 1.35416,-1.35417),
                           ("l",0,-2.70833), ("l",-10.83333,0), ("l",0,-17.60417),
                           ("c",0,-1.35417, 0,-1.35417, -1.35417,-1.35417),
                           ("l",-2.70833,0), ("l",0,23.02084), ("z",),
                        # E
                           ("M",93.85418,0), ("l",0,23.02083),
                           ("l",12.18749,0), ("c",1.35417,0, 1.35417,0, 1.35417,-1.35417),
                           ("l",0,-2.70833), ("l",-10.83333,0), ("l",0,-6.77083),
                           ("l",5.41666,0), ("c",1.35417,0, 1.35417,0, 1.35417,-1.35417),
                           ("l",0,-2.70833), ("l",-6.77083,0), ("l",0,-5.41667),
                           ("l",8.125,0), ("c",1.35416,0, 1.35416,0, 1.35416,-1.35416),
                           ("l",0,-1.35417), ("l",-12.18749,0), ("z",)],
                          {"fill": "url(#logo-top)", "fill-opacity": "1",
                           "fill-rule": "evenodd", "stroke": "none"}),
                        ]),

                 Transform([("translate", "%i,%i" % (bw*0.25, -py*1.77)),
                            ("scale", "2.5,2.5")], [
                     Path((bx, py, bw, bh), [
                        # J
                           ("M",0,-1), ("m",0,2.70833),
                           ("c",0,1.35417, 0,1.35417, 1.35417,1.35417),
                           ("l",5.41666,0), ("l",0,13.1875),
                           ("c",0,1.35417, -1.35416,2.70833, -2.70833,2.70833),
                           ("c",-1.35416,0, -2.70833,-1.35416, -2.70833,-2.70833),
                           ("l",-2.70834,0), ("l",0,1.35417),
                           ("c",0,2.70833, 2.70834,5.41666, 6.77084,5.41666),
                           ("c",2.70833,0, 5.41666,-2.70833, 5.41666,-5.41666),
                           ("l",0,-14.54167), ("l",5.41667,0), ("l",0,-1.70833),
                           ("c",0,-1.35417, 0,-1.35417, -1.35417,-1.35417),
                           ("l",-14.89583,0), ("z",),
                        # O
                           ("M",16.0964695,12.1875),
                           ("c",0,-8.125, 4.06249,-12.1875, 9.47916,-12.1875),
                           ("c",5.41667,0, 9.47917,4.0625, 9.47917,12.1875),
                           ("c",0,6.77084, -4.0625,10.83334, -9.47917,10.83334),
                           ("c",-5.41667,0, -9.47916,-4.0625, -9.47916,-10.83334),
                           ("z",),
                           ("m",4.06249,0),
                           ("c",0,-6.77083, 2.70834,-9.47916, 5.41667,-9.47916),
                           ("c",2.70834,0, 5.41667,2.70833, 5.41667,9.47916),
                           ("c",0,5.41667, -2.70833,8.125, -5.41667,8.125),
                           ("c",-2.70833,0, -5.41667,-2.70833, -5.41667,-8.125),
                           ("z",),
                        # U
                           ("M",38.76313,0), ("m",4.0625,0),
                           ("l",0,14.89583),
                           ("c",0,1.35417, 1.35417,4.0625, 4.0625,4.0625),
                           ("l",1.35417,0),
                           ("c",2.70833,0, 4.0625,-2.70833, 4.0625,-4.0625),
                           ("l",0,-14.89583), ("l",4.0625,0), ("l",0,16.25),
                           ("c",0,2.70833, -2.70833,6.77083, -8.125,6.77084),
                           ("l",-1.35417,0),
                           ("c",-5.41666,0, -8.125,-4.06251, -8.125,-6.77084),
                           ("l",0,-16.25), ("z",),
                        # R
                           ("M",59.22918,0), ("l",0,21.66667),
                           ("c",0,1.35417, 0,1.35417, 1.35416,1.35417),
                           ("l",2.70834,0), ("l",0,-9.47917), ("l",4.0625,0),
                           ("l",5.41666,9.47917), ("l",2.70834,0), ("l",0,-1.35417),
                           ("l",-5.41667,-9.47917),
                           ("c",4.0625,-1.35416, 4.0625,-4.0625, 4.0625,-5.41666),
                           ("l",0,-1.35417),
                           ("c",0,-2.70833, -1.35417,-5.41667, -5.41667,-5.41667),
                           ("l",-9.47916,0), ("z",),
                           ("m",4.0625,2.70834), ("l",0,6.77083), ("l",4.0625,0),
                           ("c",4.06249,0, 4.06249,-6.77084, 0,-6.77083),
                           ("l",-4.0625,0), ("z",),
                        # N
                           ("M",75.98689,0), ("l",0,23.02084),
                           ("l",4.0625,0), ("l",0,-16.25), ("l",10.83333,16.25),
                           ("l",4.0625,0), ("l",0,-21.66667),
                           ("c",0,-1.35417, 0,-1.35417, -1.35417,-1.35417),
                           ("l",-2.70833,0), ("l",0,16.25), ("l",-10.83333,-16.25),
                           ("l",-4.0625,0), ("z",),
                        # E
                           ("M",97.50001,0), ("l",0,23.02084), ("l",12.1875,0),
                           ("c",1.35417,0, 1.35417,0, 1.35417,-1.35417),
                           ("l",0,-2.70834), ("l",-10.83333,0), ("l",0,-6.77083),
                           ("l",5.41667,0),
                           ("c",1.35416,0, 1.35416,0, 1.35416,-1.35417),
                           ("l",0,-2.70833), ("l",-6.77083,0), ("l",0,-5.41667),
                           ("l",8.125,0), ("c",1.35416,0, 1.35416,0, 1.35416,-1.35416),
                           ("l",0,-1.35417), ("l",-12.1875,0), ("z",),
                        # Y
                           ("M",118.1196,23.02084), ("l",2.70834,0),
                           ("c",1.35416,0, 1.35416,0, 1.35416,-1.35417),
                           ("l",-0.15354,-10.67979),
                           ("c",2.70833,-2.70834, 6.92438,-4.21605, 6.92438,-10.98688),
                           ("c",-1.35417,0, -2.70834,0, -2.86188,1.50771),
                           ("c",0.15354,2.55479, -3.90896,6.61729, -5.26312,7.97146),
                           ("l",-1.35417,0),
                           ("c",-2.70833,-2.70833, -5.72376,-3.75542, -5.57021,-9.32563),
                           ("c",-1.90754,-0.20788, -2.86188,0.67709, -2.70833,1.35417),
                           ("c",-0.15355,4.73959, 2.47715,7.38683, 6.92437,9.32562),
                           ("l",0,12.18751), ("z",)
                          ],
                          {"fill": "url(#logo-bottom)", "fill-opacity": "1",
                           "fill-rule": "evenodd", "stroke": "none"}),
                        ])
                       ] + \

                 make_logo(bw/2.0, 70, 30, 30, front_cover_publisher1, front_cover_publisher2) + \
                 eyes
                )
            ])


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
    inlay_height = 2142
    
    # Cover width (front and back)
    cover_width = 1515
    
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
    
    front_cover = make_front_cover(0, bw, bh, tby, tbh, py, r, hr, o, background)
    
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
            '<linearGradient id="outside-bowl" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#400000" />\n'
            '  <stop offset="0.74074072" stop-color="#3f0f00" />\n'
            '  <stop offset="1" stop-color="#400704" />\n'
            '</linearGradient>\n'
            '<linearGradient id="cave-outside" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#000000" />\n'
            '  <stop offset="0.25" stop-color="#040404" />\n'
            '  <stop offset="1" stop-color="#101010" />\n'
            '</linearGradient>\n'
            '<linearGradient id="box-fade" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0.85" stop-color="black" stop-opacity="1" />\n'
            '  <stop offset="1" stop-color="black" stop-opacity="0" />\n'
            '</linearGradient>\n'
            '<linearGradient id="logo-top" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#007f00" stop-opacity="1" />\n'
            '  <stop offset="1" stop-color="#007f00" stop-opacity="0.5" />\n'
            '</linearGradient>\n'
            '<linearGradient id="logo-bottom" x1="50%" y1="0%" x2="50%" y2="100%">\n'
            '  <stop offset="0" stop-color="#007f00" stop-opacity="1" />\n'
            '  <stop offset="1" stop-color="#ffff00" stop-opacity="0.5" />\n'
            '</linearGradient>\n'
            )
    
    pages = [front_cover]
    
    total_size = (cover_width, inlay_height)
    
    svg = SVG(output_file)
    svg.open()
    svg.add_defs(defs)
    
    front_cover.render(svg)
    
    svg.close()
    
    sys.exit()
