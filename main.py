#!/usr/bin/env python3
"""Draw a one-image summary of the world news of 27 November 2026.

Running ``python3 main.py`` writes ``entry.png``: a 1024x1024
front-page-style infographic (masthead with the date, one lead story,
twelve story cards and a forty-item "also today" brief list -- 53 real
stories in all) compiled from wire reporting dated 27 November 2026.
See README.md for the source list behind every story.

The program uses only the Python standard library: it rasterises text
with a small built-in 5x7 bitmap font and encodes the PNG itself with
zlib, so it runs in the grader's no-network sandbox with nothing
installed. It is fully deterministic -- no network, no randomness, no
wall-clock time -- and re-running it reproduces the same bytes.

The PNG is written to the directory named by MAKEFUN_OUTPUT_DIR when
that variable is set (the grader's /output), otherwise next to this
script. The file is always named ``entry.png``.
"""

import os
import struct
import zlib

# ---------------------------------------------------------------------------
# Canvas and palette: a newspaper front page, paper white with black ink.
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 1024, 1024
MARGIN = 24

PAPER = (247, 243, 234)      # newsprint off-white
INK = (18, 18, 20)           # headline black
BODY = (52, 52, 54)          # summary dark grey
MUTED = (110, 108, 100)      # footer grey
RED = (178, 34, 34)          # masthead / kicker red
NAVY = (31, 58, 95)          # section blue
GOLD = (146, 104, 12)        # date gold
RULE = (18, 18, 20)          # rule lines
CARD_BG = (255, 255, 255)    # card white
CARD_EDGE = (196, 190, 176)  # card border
LEAD_BG = (255, 255, 255)    # lead panel white


class Canvas:
    """A plain RGB pixel buffer with rectangle and text drawing."""

    def __init__(self, width, height, colour):
        self.width = width
        self.height = height
        self.pixels = bytearray(colour * (width * height))

    def set_pixel(self, x, y, colour):
        if 0 <= x < self.width and 0 <= y < self.height:
            i = (y * self.width + x) * 3
            self.pixels[i:i + 3] = bytes(colour)

    def fill_rect(self, x0, y0, x1, y1, colour):
        x0 = max(0, x0)
        y0 = max(0, y0)
        x1 = min(self.width, x1)
        y1 = min(self.height, y1)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(colour) * (x1 - x0)
        for y in range(y0, y1):
            i = (y * self.width + x0) * 3
            self.pixels[i:i + len(row)] = row

    def rect(self, x0, y0, x1, y1, colour, width=1):
        self.fill_rect(x0, y0, x1, y0 + width, colour)
        self.fill_rect(x0, y1 - width, x1, y1, colour)
        self.fill_rect(x0, y0, x0 + width, y1, colour)
        self.fill_rect(x1 - width, y0, x1, y1, colour)


def _png_chunk(kind, data):
    chunk = struct.pack(">I", len(data)) + kind + data
    chunk += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return chunk


def save_png(canvas, path):
    """Encode the canvas as a PNG (filter 0 on every scanline)."""
    raw = bytearray()
    stride = canvas.width * 3
    for y in range(canvas.height):
        raw.append(0)
        start = y * stride
        raw += canvas.pixels[start:start + stride]
    ihdr = struct.pack(">IIBBBBB", canvas.width, canvas.height,
                       8, 2, 0, 0, 0)
    blob = (b"\x89PNG\r\n\x1a\n"
            + _png_chunk(b"IHDR", ihdr)
            + _png_chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + _png_chunk(b"IEND", b""))
    with open(path, "wb") as handle:
        handle.write(blob)
    return len(blob)


# ---------------------------------------------------------------------------
# Bitmap font: 5x7 glyphs, one row string per row, "#" = ink, "." = blank.
# ---------------------------------------------------------------------------
GLYPHS = {
    "A": (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "B": ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    "C": (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    "D": ("####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."),
    "E": ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    "F": ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    "G": (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    "H": ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    "I": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "#####"),
    "J": ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    "K": ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    "L": ("#....", "#....", "#....", "#....", "#....", "#....", "#####"),
    "M": ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    "N": ("#...#", "##..#", "#.#.#", "#.#.#", "#..##", "#..##", "#...#"),
    "O": (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "P": ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    "Q": (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    "R": ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    "S": (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    "T": ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    "U": ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    "V": ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "W": ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "X": ("#...#", "#...#", ".#.#.", "..#..", ".#.#.", "#...#", "#...#"),
    "Y": ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    "Z": ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    "0": (".###.", "#..##", "#.#.#", "#.#.#", "##..#", "#...#", ".###."),
    "1": ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "2": (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    "3": ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    "4": ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    "5": ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    "6": (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    "7": ("#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."),
    "8": (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    "9": (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    # Lowercase letters (x-height rows, descenders where needed).
    "a": (".....", ".....", ".###.", "....#", ".####", "#...#", ".####"),
    "b": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "####."),
    "c": (".....", ".....", ".####", "#....", "#....", "#....", ".####"),
    "d": ("....#", "....#", ".####", "#...#", "#...#", "#...#", ".####"),
    "e": (".....", ".....", ".###.", "#...#", "#####", "#....", ".###."),
    "f": ("..##.", ".#..#", ".#...", "####.", ".#...", ".#...", ".#..."),
    "g": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "h": ("#....", "#....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "i": (".....", "..#..", ".....", ".##..", "..#..", "..#..", ".###."),
    "j": (".....", "...#.", ".....", "..##.", "...#.", "...#.", "##..."),
    "k": ("#....", "#....", "#..#.", "#.#..", "##...", "#.#..", "#..#."),
    "l": (".##..", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    "m": (".....", ".....", "##.#.", "#.#.#", "#.#.#", "#.#.#", "#.#.#"),
    "n": (".....", ".....", "####.", "#...#", "#...#", "#...#", "#...#"),
    "o": (".....", ".....", ".###.", "#...#", "#...#", "#...#", ".###."),
    "p": (".....", ".....", "####.", "#...#", "#...#", "####.", "#...."),
    "q": (".....", ".....", ".####", "#...#", "#...#", ".####", "....#"),
    "r": (".....", ".....", "#.##.", "##..#", "#....", "#....", "#...."),
    "s": (".....", ".....", ".####", "#....", ".###.", "....#", "####."),
    "t": (".#...", ".#...", "####.", ".#...", ".#...", ".#...", "..##."),
    "u": (".....", ".....", "#...#", "#...#", "#...#", "#..##", ".##.#"),
    "v": (".....", ".....", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    "w": (".....", ".....", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    "x": (".....", ".....", "#...#", ".#.#.", "..#..", ".#.#.", "#...#"),
    "y": (".....", ".....", "#...#", "#...#", "#...#", ".####", "....#"),
    "z": (".....", ".....", "#####", "...#.", "..#..", ".#...", "#####"),
    # Punctuation and symbols.
    " ": (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    ".": (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ",": (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    ":": (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    ";": (".....", ".##..", ".##..", ".....", ".##..", ".##..", ".#..."),
    "!": ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    "?": (".###.", "#...#", "....#", "...#.", "..#..", ".....", "..#.."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '"': (".#.#.", ".#.#.", ".#.#.", ".....", ".....", ".....", "....."),
    "-": (".....", ".....", ".....", ".###.", ".....", ".....", "....."),
    "\u2014": (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    "(": ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ")": (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    "/": ("....#", "....#", "...#.", "..#..", ".#...", "#....", "#...."),
    "%": ("##..#", "##.#.", "...#.", "..#..", ".#...", "#.###", "#..##"),
    "&": (".##..", "#..#.", "#.#..", ".#...", "#.#.#", "#..#.", ".##.#"),
    "+": (".....", "..#..", "..#..", ".###.", "..#..", "..#..", "....."),
    "=": (".....", ".....", ".###.", ".....", ".###.", ".....", "....."),
    "*": (".....", ".#.#.", "..#..", ".###.", "..#..", ".#.#.", "....."),
    "\u00b7": (".....", ".....", ".....", ".##..", ".##..", ".....", "....."),
    "$": ("..#..", ".####", "#.#..", ".###.", "..#.#", "####.", "..#.."),
    "\u2022": (".....", ".....", ".###.", ".###.", ".###.", ".....", "....."),
}

GLYPH_W, GLYPH_H = 5, 7
ADVANCE = 6  # glyph width plus one pixel of tracking


def text_width(text, scale):
    """Pixel width of ``text`` drawn at the given integer ``scale``."""
    return (len(text) * ADVANCE - 1) * scale if text else 0


def draw_text(canvas, x, y, text, scale, colour):
    """Draw ``text`` with its top-left corner at (x, y)."""
    cx = x
    for char in text:
        glyph = GLYPHS.get(char)
        if glyph is None:
            raise ValueError("no glyph for character: %r" % char)
        for row, line in enumerate(glyph):
            for col, pixel in enumerate(line):
                if pixel == "#":
                    canvas.fill_rect(cx + col * scale, y + row * scale,
                                     cx + (col + 1) * scale,
                                     y + (row + 1) * scale, colour)
        cx += ADVANCE * scale
    return cx


def draw_centred(canvas, y, text, scale, colour):
    """Draw ``text`` centred horizontally on the canvas at height ``y``."""
    x = (WIDTH - text_width(text, scale)) // 2
    draw_text(canvas, x, y, text, scale, colour)


def wrap(text, scale, max_width):
    """Greedy word wrap measured in pixels; returns a list of lines."""
    words = text.split(" ")
    lines, current = [], ""
    for word in words:
        trial = word if not current else current + " " + word
        if text_width(trial, scale) <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_lines(canvas, x, y, lines, scale, colour, leading):
    for line in lines:
        draw_text(canvas, x, y, line, scale, colour)
        y += leading
    return y


# ---------------------------------------------------------------------------
# The day's stories: (kicker, headline lines, deck/summary).
# Every item was reported on Friday 27 November 2026; see README.md.
# ---------------------------------------------------------------------------
LEAD = (
    "IRAN WAR - TOP STORY",
    ("TRUMP: 'VICTORY AT HAND'",
     "IN IRAN WAR, DEAL OFFERED"),
    "Speaking to US troops on Thanksgiving, the president said victory "
    "over Iran was near and offered Tehran a chance to make a deal. Iran "
    "denied any role in the Kuwait drone deaths, and Hormuz tanker "
    "traffic rose despite attacks.",
)

CARDS = [
    ("MIDDLE EAST",
     "Israel warns 1m Gazans may be displaced",
     "The defence minister said a million Palestinians face displacement "
     "if Hamas refuses to disarm."),
    ("GULF",
     "Houthi strike hits Saudi Aramco refinery",
     "A worker was killed and some operations halted at Jazan. The "
     "Saudi-led coalition struck a Houthi missile site in reply."),
    ("IRAN",
     "Iran builds secret complex by nuclear sites",
     "A US institute says Tehran is rapidly building an underground "
     "complex near its nuclear sites."),
    ("UKRAINE",
     "Trump: Putin wants a deal to end the war",
     "The US president said Russia's leader 'would like to make a deal' "
     "to end the war in Ukraine."),
    ("UKRAINE",
     "Zelensky warns of big Russian attack soon",
     "Kyiv says Moscow is preparing a large-scale attack on Ukraine "
     "within days."),
    ("NEW ZEALAND",
     "NZ coalition falls one seat short",
     "The National-led coalition won 65 of 130 seats and must seek help "
     "from the centrist Opportunity Party to govern."),
    ("BANGLADESH",
     "Hasina sets 16 Dec return to Bangladesh",
     "The death-sentenced ex-premier says she will return from Delhi on "
     "Victory Day, putting Dhaka on edge."),
    ("SPAIN",
     "Ship capsizes off Ibiza; oil spill feared",
     "Spain races to contain oil after a diesel tanker capsized, leaving "
     "one crew member dead."),
    ("EGYPT",
     "Cairo tanker fire kills 31; driver held",
     "A fuel tanker overturned on a packed highway and exploded. "
     "Prosecutors arrested a man accused of causing it."),
    ("SPACE",
     "US clears SpaceX for 1m satellites",
     "Washington approved plans for up to a million orbital data-centre "
     "satellites, an AI hub in space."),
    ("MARKETS",
     "Musk pledges $18bn in SpaceX shares",
     "Musk and SpaceX will give two shares each to every US child with "
     "an active Trump Account."),
    ("SPORT",
     "Eagles' 21-point comeback stuns Cowboys",
     "A 59-yard field goal sealed the Thanksgiving comeback; the Bears "
     "beat the Lions in a classic."),
]

BRIEFS = [
    "North Korea halts military aid to Russia, Kyiv intel says",
    "Kim Jong Un vows to keep expanding nuclear arsenal",
    "Ukraine hits Russian Su-34 airbase in Volgograd region",
    "Drone fire hits Slavyansk-ECO refinery in Krasnodar",
    "Russia warns Estonia border move could bring hostilities",
    "Germany arrests two over pro-Iran synagogue plot",
    "North Korea expels Swiss diplomat in sanctions row",
    "Russian military plane crashes in Siberia; 19 dead",
    "Argentina bars central bank from printing money for spending",
    "Spain's Hernandez de Cos picked as next ECB president",
    "UK net migration falls to near 30-year low",
    "China industrial profits jump 20.1% in October",
    "Global stocks rally as tech rebounds before Thanksgiving",
    "Oil rises as Houthis claim Saudi refinery strike",
    "Nvidia halts chip shipments to SE Asia to block China loophole",
    "S&P puts Nvidia on CreditWatch Negative",
    "Apple pulls MiniMax chatbot Talkie over child safety",
    "Altria weighs all-cash bid for Imperial Brands",
    "Thanksgiving storm leaves 724,000 without power in east US",
    "Macy's Thanksgiving parade postponed",
    "Trump targets Somali immigrants in Thanksgiving message",
    "AFP takes content platform offline after cyberattack",
    "FIFA says personal data stolen in cyberattack",
    "Israeli forces demolish 50 structures in West Bank village",
    "Syria seizes 783,000 Captagon pills from Lebanon",
    "Iraq jails eight French nationals for life over ISIS links",
    "FAO: agrifood climate finance falls as extremes intensify",
    "World's ice will keep melting even at net zero, study warns",
    "Quantum drone sets world speed record: 727 km/h in Germany",
    "Gukesh draws game 3; chess title match level 1.5-1.5",
    "NZ 131-4 at tea in 2nd Test; debutant Brar takes wicket",
    "Sri Lanka A stun India A with twin centuries, reach final",
    "Bears beat Lions in Thanksgiving NFL classic",
    "Thailand market fire; refinery blaze brought under control",
    "South Korea warns after Russian jet enters defence zone",
    "Pakistan teen held on FBI lead after asking AI about a bomb",
    "French police convicted over 2020 beating of producer Zecler",
    "US approved nearly 900,000 AI chip exports to China in 6 months",
    "Turkey's central bank reserves fall $17bn to 18-month low",
    "Brazil eyes Bradesco chairman for finance minister",
]

FOOTER = ("Sources: Reuters \u00b7 AP \u00b7 BBC \u00b7 The Guardian \u00b7 CNN \u00b7 "
          "ESA \u00b7 AFP \u00b7 WSJ \u2014 Compiled from reporting dated "
          "Friday 27 November 2026")


# ---------------------------------------------------------------------------
# Layout: masthead, lead story, twelve cards, forty briefs, footer.
# ---------------------------------------------------------------------------
def draw_masthead(canvas):
    """Paper name, the date in large type, and the story count."""
    canvas.fill_rect(MARGIN, 14, WIDTH - MARGIN, 16, RULE)
    draw_centred(canvas, 24, "THE WORLD IN ONE DAY", 4, INK)
    draw_centred(canvas, 58, "FRIDAY 27 NOVEMBER 2026", 3, RED)
    draw_centred(canvas, 86, "ONE DAY'S NEWS, FROM EVERY REGION - 53 STORIES "
                 "FROM THE WIRES", 1, MUTED)
    canvas.fill_rect(MARGIN, 100, WIDTH - MARGIN, 103, RULE)


def draw_lead(canvas):
    """The day's biggest story, full width under the masthead."""
    x0, y0, x1, y1 = MARGIN, 112, WIDTH - MARGIN, 252
    canvas.fill_rect(x0, y0, x1, y1, LEAD_BG)
    canvas.rect(x0, y0, x1, y1, RULE, 2)
    canvas.fill_rect(x0 + 2, y0 + 2, x1 - 2, y0 + 10, RED)
    kicker, headline, deck = LEAD
    draw_text(canvas, x0 + 16, y0 + 14, kicker, 1, RED)
    y = draw_lines(canvas, x0 + 16, y0 + 28, headline, 3, INK, 25)
    draw_lines(canvas, x0 + 16, y + 6,
               wrap(deck, 2, x1 - x0 - 32), 2, BODY, 18)


def draw_cards(canvas):
    """Twelve story cards in a 4 x 3 grid."""
    x0, y0 = MARGIN, 262
    cols, rows = 4, 3
    gap = 10
    cw = (WIDTH - 2 * MARGIN - (cols - 1) * gap) // cols
    ch = 140
    for idx, (kicker, headline, summary) in enumerate(CARDS):
        col, row = idx % cols, idx // cols
        bx = x0 + col * (cw + gap)
        by = y0 + row * (ch + gap)
        canvas.fill_rect(bx, by, bx + cw, by + ch, CARD_BG)
        canvas.rect(bx, by, bx + cw, by + ch, CARD_EDGE, 1)
        canvas.fill_rect(bx + 1, by + 1, bx + cw - 1, by + 7, NAVY)
        draw_text(canvas, bx + 10, by + 13, kicker, 1, NAVY)
        draw_lines(canvas, bx + 10, by + 28,
                   wrap(headline, 2, cw - 20)[:3], 2, INK, 17)
        draw_lines(canvas, bx + 10, by + 84,
                   wrap(summary, 1, cw - 20)[:4], 1, BODY, 10)


def draw_briefs(canvas):
    """Forty one-line stories in two columns under the cards."""
    y0 = 712
    draw_text(canvas, MARGIN, y0, "ALSO TODAY", 2, RED)
    canvas.fill_rect(MARGIN, y0 + 20, WIDTH - MARGIN, y0 + 22, RULE)
    col_w = (WIDTH - 2 * MARGIN - 20) // 2
    y = y0 + 32
    for idx, item in enumerate(BRIEFS):
        col = idx // 20
        row = idx % 20
        x = MARGIN + col * (col_w + 20)
        draw_text(canvas, x, y + row * 11, "\u2022 " + item, 1, BODY)


def draw_footer(canvas):
    """Sources line at the foot of the page."""
    y = 968
    canvas.fill_rect(MARGIN, y, WIDTH - MARGIN, y + 2, RULE)
    draw_centred(canvas, y + 10, FOOTER, 1, MUTED)


def main():
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        out_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(out_dir, exist_ok=True)
    canvas = Canvas(WIDTH, HEIGHT, PAPER)
    draw_masthead(canvas)
    draw_lead(canvas)
    draw_cards(canvas)
    draw_briefs(canvas)
    draw_footer(canvas)
    path = os.path.join(out_dir, "entry.png")
    size = save_png(canvas, path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
