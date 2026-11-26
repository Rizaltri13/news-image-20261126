#!/usr/bin/env python3
"""The World Today - Thursday 26 November 2026 in one image.
news-image-20261126 entry for make.fun.
Stdlib only. Draws a newspaper front page (1024x1024) and writes
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png). Deterministic:
no network, no clock, no randomness.
"""
import os
import struct
import zlib

W, H = 1024, 1024
PAPER = (247, 243, 232)
INK = (17, 17, 17)
RED = (185, 28, 28)
GREY = (110, 106, 96)
LIGHT = (232, 227, 214)
BLUE = (28, 68, 120)
GOLD = (176, 132, 32)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)


# ---------------------------------------------------------------- PNG read
def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def read_png(path):
    """Return (width, height, rows) with rows as list of bytes RGB."""
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"
    pos = 8
    idat = b""
    width = height = bitdepth = ctype = None
    plte = None
    trns = None
    while pos < len(data):
        (ln,) = struct.unpack(">I", data[pos:pos + 4])
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        pos += 12 + ln
        if typ == b"IHDR":
            width, height, bitdepth, ctype, _, _, _ = struct.unpack(
                ">IIBBBBB", chunk)
        elif typ == b"PLTE":
            plte = chunk
        elif typ == b"tRNS":
            trns = chunk
        elif typ == b"IDAT":
            idat += chunk
        elif typ == b"IEND":
            break
    assert bitdepth == 8, "only 8-bit PNGs supported"
    channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[ctype]
    raw = zlib.decompress(idat)
    stride = width * channels
    rows = []
    prev = bytearray(stride)
    p = 0
    for _y in range(height):
        f = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if f == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 255
        elif f == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif f == 3:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 255
        elif f == 4:
            for i in range(stride):
                a = line[i - channels] if i >= channels else 0
                b = prev[i]
                c = prev[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(a, b, c)) & 255
        prev = line
        if ctype == 2:
            rows.append(bytes(line))
        elif ctype == 6:
            out = bytearray()
            for i in range(0, stride, 4):
                out += line[i:i + 3]
            rows.append(bytes(out))
        elif ctype == 0:
            out = bytearray()
            for v in line:
                out += bytes((v, v, v))
            rows.append(bytes(out))
        elif ctype == 3:
            out = bytearray()
            for v in line:
                out += plte[v * 3:v * 3 + 3]
            rows.append(bytes(out))
        elif ctype == 4:
            out = bytearray()
            for i in range(0, stride, 2):
                out += bytes((line[i],) * 3)
            rows.append(bytes(out))
    return width, height, rows


# ---------------------------------------------------------------- PNG write
def _filter_row(f, row, prev, bpp):
    out = bytearray(len(row))
    if f == 0:
        return bytes(row)
    if f == 1:
        for i in range(len(row)):
            a = row[i - bpp] if i >= bpp else 0
            out[i] = (row[i] - a) & 255
    elif f == 2:
        for i in range(len(row)):
            out[i] = (row[i] - prev[i]) & 255
    elif f == 3:
        for i in range(len(row)):
            a = row[i - bpp] if i >= bpp else 0
            out[i] = (row[i] - ((a + prev[i]) >> 1)) & 255
    else:
        for i in range(len(row)):
            a = row[i - bpp] if i >= bpp else 0
            b = prev[i]
            c = prev[i - bpp] if i >= bpp else 0
            out[i] = (row[i] - _paeth(a, b, c)) & 255
    return bytes(out)


def write_png(path, width, height, rgb):
    """rgb: bytearray of width*height*3. Deterministic output."""
    def chunk(typ, payload):
        c = struct.pack(">I", len(payload)) + typ + payload
        return c + struct.pack(">I", zlib.crc32(typ + payload) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    raw = bytearray()
    prev = bytes(width * 3)
    for y in range(height):
        row = bytes(rgb[y * width * 3:(y + 1) * width * 3])
        best = None
        for f in (0, 1, 2, 3, 4):
            cand = _filter_row(f, row, prev, 3)
            score = sum(abs(b - 128) for b in cand)
            if best is None or score < best[0]:
                best = (score, f, cand)
        raw.append(best[1])
        raw += best[2]
        prev = row
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr)
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as fh:
        fh.write(png)


# ---------------------------------------------------------------- Canvas
class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(c)

    def rect(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:(i + (x1 - x0) * 3)] = bytes(c) * (x1 - x0)

    def hline(self, x, y, w, c, t=1):
        self.rect(x, y, w, t, c)

    def vline(self, x, y, h, c, t=1):
        self.rect(x, y, t, h, c)

    def ellipse(self, cx, cy, rx, ry, c):
        for dy in range(-ry, ry + 1):
            dx = int(rx * (1 - (dy / ry) ** 2) ** 0.5) if ry else 0
            self.rect(cx - dx, cy + dy, dx * 2 + 1, 1, c)

    def blit_cover(self, img_w, img_h, rows, x, y, w, h, top_anchor=True):
        """Cover-crop the source image into the box (x, y, w, h)."""
        sx = img_w / w
        sy = img_h / h
        s = min(sx, sy)
        sw, sh = int(w * s), int(h * s)
        ox = (img_w - sw) // 2
        oy = 0 if top_anchor else (img_h - sh) // 2
        for dy in range(h):
            sy_src = oy + int(dy * s)
            if sy_src >= img_h:
                break
            src = rows[sy_src]
            for dx in range(w):
                sx_src = ox + int(dx * s)
                if sx_src >= img_w:
                    break
                i = (sx_src * 3)
                self.set(x + dx, y + dy,
                         (src[i], src[i + 1], src[i + 2]))

# ---------------------------------------------------------------- 5x7 font
# Each glyph: 7 rows of 5 bits ('#' = on).
FONT = {
"A": ("01110","10001","10001","11111","10001","10001","10001"),
"B": ("11110","10001","10001","11110","10001","10001","11110"),
"C": ("01110","10001","10000","10000","10000","10001","01110"),
"D": ("11110","10001","10001","10001","10001","10001","11110"),
"E": ("11111","10000","10000","11110","10000","10000","11111"),
"F": ("11111","10000","10000","11110","10000","10000","10000"),
"G": ("01110","10001","10000","10111","10001","10001","01111"),
"H": ("10001","10001","10001","11111","10001","10001","10001"),
"I": ("01110","00100","00100","00100","00100","00100","01110"),
"J": ("00111","00010","00010","00010","00010","10010","01100"),
"K": ("10001","10010","10100","11000","10100","10010","10001"),
"L": ("10000","10000","10000","10000","10000","10000","11111"),
"M": ("10001","11011","10101","10101","10001","10001","10001"),
"N": ("10001","11001","10101","10011","10001","10001","10001"),
"O": ("01110","10001","10001","10001","10001","10001","01110"),
"P": ("11110","10001","10001","11110","10000","10000","10000"),
"Q": ("01110","10001","10001","10001","10101","10010","01101"),
"R": ("11110","10001","10001","11110","10100","10010","10001"),
"S": ("01111","10000","10000","01110","00001","00001","11110"),
"T": ("11111","00100","00100","00100","00100","00100","00100"),
"U": ("10001","10001","10001","10001","10001","10001","01110"),
"V": ("10001","10001","10001","10001","10001","01010","00100"),
"W": ("10001","10001","10001","10101","10101","11011","10001"),
"X": ("10001","10001","01010","00100","01010","10001","10001"),
"Y": ("10001","10001","01010","00100","00100","00100","00100"),
"Z": ("11111","00001","00010","00100","01000","10000","11111"),
"0": ("01110","10001","10011","10101","11001","10001","01110"),
"1": ("00100","01100","00100","00100","00100","00100","01110"),
"2": ("01110","10001","00001","00110","01000","10000","11111"),
"3": ("11111","00010","00100","00010","00001","10001","01110"),
"4": ("00010","00110","01010","10010","11111","00010","00010"),
"5": ("11111","10000","11110","00001","00001","10001","01110"),
"6": ("00110","01000","10000","11110","10001","10001","01110"),
"7": ("11111","00001","00010","00100","01000","01000","01000"),
"8": ("01110","10001","10001","01110","10001","10001","01110"),
"9": ("01110","10001","10001","01111","00001","00010","01100"),
" ": ("00000","00000","00000","00000","00000","00000","00000"),
".": ("00000","00000","00000","00000","00000","01100","01100"),
",": ("00000","00000","00000","00000","01100","00100","01000"),
":": ("00000","01100","01100","00000","01100","01100","00000"),
";": ("00000","01100","01100","00000","01100","00100","01000"),
"!": ("00100","00100","00100","00100","00100","00000","00100"),
"?": ("01110","10001","00001","00110","00100","00000","00100"),
"-": ("00000","00000","00000","01110","00000","00000","00000"),
"–": ("00000","00000","00000","11111","00000","00000","00000"),
"—": ("00000","00000","00000","11111","00000","00000","00000"),
"'": ("00100","00100","01000","00000","00000","00000","00000"),
'"': ("01010","01010","00000","00000","00000","00000","00000"),
"(": ("00010","00100","01000","01000","01000","00100","00010"),
")": ("01000","00100","00010","00010","00010","00100","01000"),
"/": ("00001","00010","00010","00100","01000","01000","10000"),
"%": ("11001","11010","00010","00100","01000","01011","10011"),
"$": ("00100","01111","10100","01110","00101","11110","00100"),
"&": ("01100","10010","10100","01000","10101","10010","01101"),
"+": ("00000","00100","00100","11111","00100","00100","00000"),
"=": ("00000","00000","11111","00000","11111","00000","00000"),
"·": ("00000","00000","00000","01100","01100","00000","00000"),
"•": ("00000","00000","01100","01100","01100","00000","00000"),
"©": ("01110","10001","10111","10000","10111","10001","01110"),
}

FONT.update({
"a": ("00000","00000","01110","00001","01111","10001","01111"),
"b": ("10000","10000","11110","10001","10001","10001","11110"),
"c": ("00000","00000","01110","10001","10000","10001","01110"),
"d": ("00001","00001","01111","10001","10001","10001","01111"),
"e": ("00000","00000","01110","10001","11111","10000","01110"),
"f": ("00110","01001","01000","11110","01000","01000","01000"),
"g": ("00000","01111","10001","10001","01111","00001","01110"),
"h": ("10000","10000","11110","10001","10001","10001","10001"),
"i": ("00100","00000","01100","00100","00100","00100","01110"),
"j": ("00010","00000","00110","00010","00010","00010","01100"),
"k": ("10000","10000","10010","10100","11000","10100","10010"),
"l": ("01100","00100","00100","00100","00100","00100","01110"),
"m": ("00000","00000","11010","10101","10101","10101","10101"),
"n": ("00000","00000","11110","10001","10001","10001","10001"),
"o": ("00000","00000","01110","10001","10001","10001","01110"),
"p": ("00000","00000","11110","10001","10001","11110","10000"),
"q": ("00000","00000","01111","10001","10001","01111","00001"),
"r": ("00000","00000","10110","11001","10000","10000","10000"),
"s": ("00000","00000","01111","10000","01110","00001","11110"),
"t": ("01000","01000","11110","01000","01000","01001","00110"),
"u": ("00000","00000","10001","10001","10001","10001","01111"),
"v": ("00000","00000","10001","10001","10001","01010","00100"),
"w": ("00000","00000","10001","10101","10101","10101","01010"),
"x": ("00000","00000","10001","01010","00100","01010","10001"),
"y": ("00000","00000","10001","10001","01111","00001","01110"),
"z": ("00000","00000","11111","00010","00100","01000","11111"),
})


def text_w(s, scale):
    """Pixel width of string s at given scale (6 units per char)."""
    return len(s) * 6 * scale


def draw_text(cv, x, y, s, scale, color):
    for ch in s:
        g = FONT.get(ch, FONT[" "])
        for r in range(7):
            row = g[r]
            for c in range(5):
                if row[c] == "1":
                    cv.rect(x + c * scale, y + r * scale, scale, scale,
                            color)
        x += 6 * scale
    return x


def draw_text_centered(cv, cx, y, s, scale, color):
    draw_text(cv, cx - text_w(s, scale) // 2, y, s, scale, color)


def wrap(s, max_chars):
    """Greedy word wrap into lines of at most max_chars characters."""
    lines, cur = [], ""
    for word in s.split(" "):
        if cur and len(cur) + 1 + len(word) > max_chars:
            lines.append(cur)
            cur = word
        else:
            cur = (cur + " " + word).strip()
    if cur:
        lines.append(cur)
    return lines


def draw_para(cv, x, y, s, scale, color, max_chars, line_h):
    for ln in wrap(s, max_chars):
        draw_text(cv, x, y, ln, scale, color)
        y += line_h
    return y


# ---------------------------------------------------------------- pictograms
def pic_chart(cv, x, y, s, c1, c2):
    """Rising bar chart with arrow."""
    bars = [10, 18, 14, 26, 34]
    bw = 8 * s
    for i, bh in enumerate(bars):
        cv.rect(x + i * (bw + 3 * s), y + 40 * s - bh * s, bw, bh * s, c1)
    # arrow
    for i in range(5):
        cv.rect(x + i * 8 * s, y + (36 - i * 6) * s, 8 * s, 3 * s, c2)
    cv.rect(x + 4 * 8 * s, y + 6 * s, 3 * s, 10 * s, c2)


def pic_bank(cv, x, y, s, c1, c2):
    """Bank / rate: pediment + columns + percent."""
    cv.rect(x, y + 8 * s, 48 * s, 4 * s, c1)
    for i in range(4):
        cv.rect(x + 2 * s + i * 12 * s, y + 16 * s, 5 * s, 22 * s, c1)
    cv.rect(x, y + 40 * s, 48 * s, 4 * s, c1)
    draw_text(cv, x + 52 * s, y + 12 * s, "%", 3, c2)


def pic_car(cv, x, y, s, c1, c2):
    """Car front view."""
    cv.rect(x + 6 * s, y + 14 * s, 36 * s, 14 * s, c1)
    cv.rect(x + 12 * s, y + 6 * s, 24 * s, 10 * s, c1)
    cv.ellipse(x + 13 * s, y + 32 * s, 6 * s, 6 * s, c2)
    cv.ellipse(x + 35 * s, y + 32 * s, 6 * s, 6 * s, c2)
    cv.rect(x + 10 * s, y + 18 * s, 7 * s, 5 * s, PAPER)
    cv.rect(x + 31 * s, y + 18 * s, 7 * s, 5 * s, PAPER)


def pic_factory(cv, x, y, s, c1, c2):
    """Factory with chimney + boxes."""
    cv.rect(x, y + 18 * s, 30 * s, 22 * s, c1)
    cv.rect(x + 32 * s, y + 4 * s, 7 * s, 36 * s, c1)
    cv.rect(x + 34 * s, y, 3 * s, 5 * s, c2)
    cv.rect(x + 4 * s, y + 24 * s, 5 * s, 5 * s, PAPER)
    cv.rect(x + 14 * s, y + 24 * s, 5 * s, 5 * s, PAPER)
    cv.rect(x + 24 * s, y + 24 * s, 5 * s, 5 * s, PAPER)
    cv.rect(x + 42 * s, y + 30 * s, 14 * s, 10 * s, c2)
    cv.rect(x + 46 * s, y + 24 * s, 6 * s, 6 * s, c2)


def pic_flame(cv, x, y, s, c1, c2):
    """Oil derrick + flame."""
    # two legs slanting inwards
    for i in range(9):
        cv.rect(x + (4 + i) * s, y + (36 - i * 4) * s, 3 * s, 4 * s, c1)
        cv.rect(x + (28 - i) * s, y + (36 - i * 4) * s, 3 * s, 4 * s, c1)
    cv.rect(x + 6 * s, y + 28 * s, 24 * s, 3 * s, c1)
    cv.rect(x + 10 * s, y + 18 * s, 16 * s, 3 * s, c1)
    cv.rect(x + 2 * s, y + 40 * s, 32 * s, 4 * s, c1)
    cv.ellipse(x + 44 * s, y + 12 * s, 8 * s, 12 * s, c2)
    cv.ellipse(x + 44 * s, y + 15 * s, 4 * s, 6 * s, GOLD)


def pic_flag(cv, x, y, s, c1, c2):
    """Flag on a pole (stars-and-stripes hint)."""
    cv.rect(x, y, 4 * s, 44 * s, c1)
    for i in range(4):
        cv.rect(x + 4 * s, y + i * 8 * s, 40 * s, 4 * s,
                c2 if i % 2 == 0 else PAPER)
    cv.rect(x + 4 * s, y, 16 * s, 16 * s, BLUE)
    for dy in (4, 10):
        for dx in (4, 10):
            cv.rect(x + dx * s, y + dy * s, 2 * s, 2 * s, WHITE)


# ---------------------------------------------------------------- layout
def build():
    cv = Canvas(W, H, PAPER)
    here = os.path.dirname(os.path.abspath(__file__))
    iw, ih, rows = read_png(os.path.join(here, "hero.png"))

    # Masthead
    draw_text_centered(cv, W // 2, 22, "THE WORLD TODAY", 7, INK)
    cv.hline(28, 84, W - 56, INK, 3)
    cv.hline(28, 92, W - 56, INK, 1)
    draw_text(cv, 28, 96, "No. 26", 1, GREY)
    draw_text(cv, W - 28 - text_w("PRICE: ONE DAY", 1), 96,
              "PRICE: ONE DAY", 1, GREY)

    # Date band
    cv.rect(28, 112, W - 56, 34, RED)
    draw_text_centered(cv, W // 2, 121, "THURSDAY, 26 NOVEMBER 2026", 2,
                       WHITE)

    # Hero picture + caption
    cv.blit_cover(iw, ih, rows, 28, 158, 640, 300, top_anchor=True)
    cv.hline(28, 158, 640, INK, 2)
    cv.hline(28, 456, 640, INK, 2)
    cv.vline(28, 158, 300, INK, 2)
    cv.vline(666, 158, 300, INK, 2)
    draw_text(cv, 28, 464,
              "Rescue teams pump floodwater from a mine shaft in Bogor,",
              1, GREY)
    draw_text(cv, 28, 477, "West Java. (Illustration)", 1, GREY)

    # Hero text, right column
    x = 692
    draw_text(cv, x, 158, "DISASTER", 2, RED)
    y = 186
    for ln in ("13 DEAD, 13", "STILL TRAPPED", "BELOW"):
        draw_text(cv, x, y, ln, 3, INK)
        y += 26
    y += 6
    y = draw_para(cv, x, y,
                  "Rescuers resumed the search on Thursday for 13 miners "
                  "still trapped in a flooded illegal gold shaft in Bogor, "
                  "West Java, after 13 bodies were recovered.",
                  2, INK, 25, 18)
    y += 8
    cv.hline(x, y, 304, GREY, 1)
    y += 8
    draw_para(cv, x, y,
              "26 entered Mon 23 Nov. River flood. Shaft ~100 m deep. "
              "325 rescuers. Police probe the illegal pit.",
              1, INK, 50, 12)

    # Standfirst
    y = 500
    cv.hline(28, y, W - 56, INK, 1)
    y += 10
    draw_para(cv, 28, y,
              "Twenty-six men went down the Mount Butak shafts on Monday. "
              "Heavy rain swelled the Ciseureuh river, floodwater poured "
              "in. Pumps are draining the 100-metre shaft "
              "as police open a probe into the illegal pit.",
              2, INK, 80, 18)

    # Facts strip
    cv.rect(28, 566, W - 56, 26, INK)
    draw_text_centered(cv, W // 2, 574,
                       "26 ENTERED MONDAY  ·  100-M SHAFT  ·  325 RESCUERS  ·  "
                       "6 OF 13 DEAD IDENTIFIED", 1, WHITE)

    # Tiles
    tiles = [
        ("MARKETS", "Asia bounces back",
         "Nikkei +1.6%, Kospi +1.9% on Thursday after Wall Street fought "
         "back. Nvidia fell 3.9% to $149.30; Brent $94.81.",
         pic_chart, INK, RED),
        ("RATES", "Seoul hikes to 3.25%",
         "Bank of Korea resumes tightening with a quarter-point rise as a "
         "chip export boom keeps inflation high.",
         pic_bank, INK, RED),
        ("TRADE", "China firms press Japan",
         "A JETRO survey finds Chinese rivals a growing threat to "
         "Japanese firms operating abroad.",
         pic_factory, INK, RED),
        ("ENERGY", "Saudi hits back at Ras Isa",
         "Riyadh struck the Houthi-held Ras Isa refinery after attacks on "
         "Ras Tanura pushed oil near $95.",
         pic_flame, INK, RED),
        ("TECH", "Uber names Asia chief",
         "Rakesh Ranjan will lead India and South Asia from 4 January "
         "2027, Uber said on Thursday.",
         pic_car, INK, RED),
        ("AMERICA", "Iowa blast a success",
         "The US Army says the controlled detonation of its bomb-chemical "
         "stockpile went exactly as planned.",
         pic_flag, INK, RED),
    ]
    tw, th, gap = 314, 168, 12
    for i, (kick, head, body, pic, c1, c2) in enumerate(tiles):
        tx = 28 + (i % 3) * (tw + gap)
        ty = 606 + (i // 3) * (th + gap)
        cv.rect(tx, ty, tw, th, LIGHT)
        cv.hline(tx, ty, tw, INK, 2)
        draw_text(cv, tx + 10, ty + 10, kick, 1, RED)
        draw_text(cv, tx + 10, ty + 28, head, 2, INK)
        draw_para(cv, tx + 10, ty + 56, body, 1, INK, 38, 12)
        pic(cv, tx + tw - 62, ty + th - 52, 1, c1, c2)

    # Ticker
    cv.rect(28, 966, W - 56, 30, BLACK)
    draw_text_centered(cv, W // 2, 975,
                       "OIL HOLDS NEAR $95 AS GULF TENSIONS SIMMER  ·  GOLD "
                       "EASES TO $3,566 AN OUNCE  ·  DOLLAR 103.71, EURO "
                       "$1.0973  ·  US MARKS THANKSGIVING DAY",
                       1, WHITE)

    # Footer
    draw_text_centered(cv, W // 2, 1006,
                       "Sources: Reuters, AP, CNN, Arirang - Stories first "
                       "reported Thursday 26 November 2026 (UTC).",
                       1, GREY)
    return cv


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    cv = build()
    write_png(os.path.join(outdir, "entry.png"), W, H, cv.px)


if __name__ == "__main__":
    main()
