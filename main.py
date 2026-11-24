import zlib, struct, os, sys

FONT = {
'A':'01110 10001 10001 11111 10001 10001 10001','B':'11110 10001 10001 11110 10001 10001 11110',
'C':'01110 10001 10000 10000 10000 10001 01110','D':'11110 10001 10001 10001 10001 10001 11110',
'E':'11111 10000 10000 11110 10000 10000 11111','F':'11111 10000 10000 11110 10000 10000 10000',
'G':'01110 10001 10000 10111 10001 10001 01111','H':'10001 10001 10001 11111 10001 10001 10001',
'I':'01110 00100 00100 00100 00100 00100 01110','J':'00111 00010 00010 00010 00010 10010 01100',
'K':'10001 10010 10100 11000 10100 10010 10001','L':'10000 10000 10000 10000 10000 10000 11111',
'M':'10001 11011 10101 10101 10001 10001 10001','N':'10001 11001 10101 10011 10001 10001 10001',
'O':'01110 10001 10001 10001 10001 10001 01110','P':'11110 10001 10001 11110 10000 10000 10000',
'Q':'01110 10001 10001 10001 10101 10010 01101','R':'11110 10001 10001 11110 10100 10010 10001',
'S':'01111 10000 10000 01110 00001 00001 11110','T':'11111 00100 00100 00100 00100 00100 00100',
'U':'10001 10001 10001 10001 10001 10001 01110','V':'10001 10001 10001 10001 10001 01010 00100',
'W':'10001 10001 10001 10101 10101 10101 01010','X':'10001 10001 01010 00100 01010 10001 10001',
'Y':'10001 10001 01010 00100 00100 00100 00100','Z':'11111 00001 00010 00100 01000 10000 11111',
'0':'01110 10001 10011 10101 11001 10001 01110','1':'00100 01100 00100 00100 00100 00100 01110',
'2':'01110 10001 00001 00010 00100 01000 11111','3':'11111 00010 00100 00010 00001 10001 01110',
'4':'00010 00110 01010 10010 11111 00010 00010','5':'11111 10000 11110 00001 00001 10001 01110',
'6':'00110 01000 10000 11110 10001 10001 01110','7':'11111 00001 00010 00100 01000 01000 01000',
'8':'01110 10001 10001 01110 10001 10001 01110','9':'01110 10001 10001 01111 00001 00010 01100',
'.':'00000 00000 00000 00000 00000 00110 00110',',':'00000 00000 00000 00000 00110 00110 00100',
':':'00000 00110 00110 00000 00110 00110 00000',';':'00000 00110 00110 00000 00110 00110 00100',
'!':'00100 00100 00100 00100 00100 00000 00100','?':'01110 10001 00001 00010 00100 00000 00100',
"'":'00100 00100 00000 00000 00000 00000 00000','-':'00000 00000 00000 11111 00000 00000 00000',
'/':'00001 00010 00010 00100 01000 01000 10000','(':'00010 00100 01000 01000 01000 00100 00010',
')':'01000 00100 00010 00010 00010 00100 01000','%':'11001 11010 00010 00100 01000 01011 10011',
'&':'01100 10010 10100 01000 10101 10010 01101','+':'00000 00100 00100 11111 00100 00100 00000',
'=':'00000 00000 11111 00000 11111 00000 00000','$':'00100 01111 10100 01110 00101 11110 00100',
' ':'00000 00000 00000 00000 00000 00000 00000',
}

PAPER = (247, 243, 233)
INK = (26, 26, 26)
NAVY = (19, 33, 61)

buf = bytearray(1024 * 1024 * 3)

def rect(x0, y0, x1, y1, col):
    if x0 < 0: x0 = 0
    if y0 < 0: y0 = 0
    if x1 > 1024: x1 = 1024
    if y1 > 1024: y1 = 1024
    if x0 >= x1 or y0 >= y1: return
    row = bytes(col) * (x1 - x0)
    for y in range(y0, y1):
        i = (y * 1024 + x0) * 3
        buf[i:i + len(row)] = row

def disc(cx, cy, r, col):
    if r <= 0: return
    if r == 1:
        rect(cx, cy, cx + 1, cy + 1, col); return
    x0, x1 = cx - r, cx + r
    y0, y1 = cy - r, cy + r
    for y in range(y0, y1 + 1):
        dy = y - cy
        v = r * r - dy * dy
        if v < 0: continue
        w = int(v ** 0.5)
        rect(cx - w, y, cx + w + 1, y + 1, col)

def poly(points, col):
    if not points: return
    ys = [p[1] for p in points]
    ymin = max(0, min(ys)); ymax = min(1023, max(ys))
    n = len(points)
    for y in range(ymin, ymax + 1):
        sy = y + 0.5
        xs = []
        for i in range(n):
            x1, y1 = points[i]; x2, y2 = points[(i + 1) % n]
            if (y1 <= sy < y2) or (y2 <= sy < y1):
                xs.append(x1 + (sy - y1) * (x2 - x1) / (y2 - y1))
        if len(xs) >= 2:
            xs.sort()
            for i in range(0, len(xs) - 1, 2):
                xa = int(round(xs[i])); xb = int(round(xs[i + 1]))
                rect(xa, y, xb, y + 1, col)

def line(x0, y0, x1, y1, col, w=1):
    dx = abs(x1 - x0); dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        rect(x0, y0, x0 + w, y0 + w, col)
        if x0 == x1 and y0 == y1: break
        e2 = 2 * err
        if e2 >= dy: err += dy; x0 += sx
        if e2 <= dx: err += dx; y0 += sy

def png_write(path, width, height, rows):
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += rows[y]
    comp = zlib.compress(bytes(raw), 9)
    def chunk(tag, data):
        return struct.pack('>I', len(data)) + tag + data + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    out = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', ihdr) + chunk(b'IDAT', comp) + chunk(b'IEND', b'')
    with open(path, 'wb') as f:
        f.write(out)

MARGIN = 16
GUTTER = 12
COL_W = 239
COL_X = [MARGIN + i * (COL_W + GUTTER) for i in range(4)]
ROW_Y = [112, 336]
PANEL_H = 216
SCENE_H = 92
LEAD_TOP = 112
BRIEF_TOP = 560
FOOT_TOP = 976

WHITE = (255, 255, 255)
RULE = (188, 178, 158)
PALE = (236, 231, 218)
RED = (166, 43, 43)
GREEN = (34, 117, 83)
BLUE = (46, 93, 154)
SKY = (150, 193, 218)
DARK = (22, 29, 41)
SAND = (213, 193, 154)
ORANGE = (210, 113, 46)
PURPLE = (101, 72, 132)

def text_width(s, scale):
    if not s:
        return 0
    return len(s) * 6 * scale - scale

def draw_text(x, y, s, scale, colour):
    s = s.upper()
    cx = x
    for ch in s:
        rows = FONT.get(ch, FONT[' ']).split()
        if ch != ' ':
            for ry, bits in enumerate(rows):
                for rx, bit in enumerate(bits):
                    if bit == '1':
                        rect(cx + rx * scale, y + ry * scale,
                             cx + (rx + 1) * scale, y + (ry + 1) * scale, colour)
        cx += 6 * scale

def centre_text(x0, x1, y, s, scale, colour):
    draw_text((x0 + x1 - text_width(s, scale)) // 2, y, s, scale, colour)

def truncate_width(s, maxw, scale):
    while s and text_width(s, scale) > maxw:
        s = s[:-1]
    return s.rstrip()

def wrap_text(s, maxw, scale):
    words = s.split()
    lines = []
    cur = ''
    for w in words:
        trial = w if not cur else cur + ' ' + w
        if text_width(trial, scale) <= maxw:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def fit_lines(s, maxw, scale, maxlines):
    lines = wrap_text(s, maxw, scale)
    if len(lines) <= maxlines:
        return [truncate_width(x, maxw, scale) for x in lines]
    out = lines[:maxlines]
    rest = ' '.join(lines[maxlines:])
    merged = out[-1] + ' ' + rest
    words = merged.split()
    while words and text_width(' '.join(words), maxw, scale) > maxw:
        words.pop()
    out[-1] = ' '.join(words)
    return out

def draw_masthead():
    rect(0, 0, 1024, 104, NAVY)
    rect(0, 100, 1024, 104, (225, 184, 99))
    centre_text(0, 1024, 5, 'THE WORLD IN ONE IMAGE', 6, WHITE)
    centre_text(0, 1024, 51, 'MONDAY 23 NOVEMBER 2026', 4, (255, 226, 158))
    rect(352, 86, 672, 88, (225, 184, 99))
    centre_text(0, 1024, 91, '35 STORIES - 6 REGIONS', 1, (220, 225, 236))

def draw_panel_base(x, y, tag, tag_colour, headline, caption):
    rect(x, y, x + COL_W, y + PANEL_H, (250, 247, 239))
    rect(x, y, x + COL_W, y + 1, RULE)
    rect(x, y + PANEL_H - 1, x + COL_W, y + PANEL_H, RULE)
    rect(x, y, x + 1, y + PANEL_H, RULE)
    rect(x + COL_W - 1, y, x + COL_W, y + PANEL_H, RULE)
    chipw = text_width(tag, 1) + 10
    rect(x + 7, y + SCENE_H + 7, x + 7 + chipw, y + SCENE_H + 20, tag_colour)
    draw_text(x + 12, y + SCENE_H + 10, tag, 1, WHITE)
    lines = fit_lines(headline, COL_W - 14, 2, 2)
    hy = y + SCENE_H + 26
    for ln in lines:
        draw_text(x + 7, hy, ln, 2, INK)
        hy += 17
    cy = y + SCENE_H + 64
    for ln in fit_lines(caption, COL_W - 14, 1, 2):
        draw_text(x + 7, cy, ln, 1, (54, 54, 54))
        cy += 9

def draw_briefs_frame():
    rect(0, BRIEF_TOP, 1024, BRIEF_TOP + 2, NAVY)
    header = 'ALSO ON MONDAY 23 NOVEMBER 2026'
    draw_text(16, BRIEF_TOP + 9, header, 2, NAVY)
    rule_y = BRIEF_TOP + 31
    rect(16, rule_y, 1008, rule_y + 1, RULE)
    rect(512, BRIEF_TOP + 9, 513, FOOT_TOP - 4, RULE)

def draw_footer():
    rect(0, FOOT_TOP, 1024, 1024, NAVY)
    rect(0, FOOT_TOP, 1024, FOOT_TOP + 2, (225, 184, 99))
    centre_text(0, 1024, FOOT_TOP + 16, 'SOURCES: REUTERS - AP - AFP - CNN - 23 NOVEMBER 2026', 1, (232, 236, 244))

def scene_markets(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (18, 34, 29))
    for gy in (y + 22, y + 44, y + 66):
        rect(x + 4, gy, x + COL_W - 4, gy + 1, (42, 63, 53))
    for gx in (x + 62, x + 122, x + 182):
        rect(gx, y + 5, gx + 1, y + SCENE_H - 4, (38, 58, 49))
    chip_x, chip_y = x + 10, y + 42
    rect(chip_x, chip_y, chip_x + 42, chip_y + 30, (196, 160, 66))
    rect(chip_x + 3, chip_y + 3, chip_x + 39, chip_y + 27, (38, 48, 44))
    for p in range(4):
        py = chip_y + 5 + p * 6
        rect(chip_x - 5, py, chip_x, py + 2, (218, 188, 105))
        rect(chip_x + 42, py, chip_x + 47, py + 2, (218, 188, 105))
    for p in range(5):
        px = chip_x + 6 + p * 7
        rect(px, chip_y - 4, px + 2, chip_y, (218, 188, 105))
        rect(px, chip_y + 30, px + 2, chip_y + 34, (218, 188, 105))
    for p in range(6):
        for q in range(4):
            rect(chip_x + 5 + p * 5, chip_y + 5 + q * 5, chip_x + 8 + p * 5, chip_y + 8 + q * 5, (86, 142, 105))
    pts = [(x + 66, y + 74), (x + 82, y + 70), (x + 96, y + 78), (x + 112, y + 59),
           (x + 128, y + 64), (x + 146, y + 45), (x + 162, y + 50), (x + 180, y + 30),
           (x + 198, y + 34), (x + 216, y + 14), (x + 230, y + 18)]
    for i in range(len(pts) - 1):
        line(pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], (61, 219, 124), 2)
    poly([(x + 224, y + 6), (x + 236, y + 8), (x + 231, y + 19)], (61, 219, 124))
    disc(x + 231, y + 21, 3, (61, 219, 124))
    card_x, card_y = x + 107, y + 8
    rect(card_x, card_y, card_x + 19, card_y + 14, (223, 228, 222))
    rect(card_x + 3, card_y + 3, card_x + 16, card_y + 7, (92, 104, 96))
    rect(card_x + 3, card_y + 9, card_x + 10, card_y + 12, (61, 219, 124))
    poly([(x + 205, y + 84), (x + 211, y + 72), (x + 217, y + 84)], (225, 231, 224))
    rect(x + 209, y + 84, x + 214, y + 92, (225, 231, 224))
    rect(x + 188, y + 80, x + 203, y + 92, (40, 49, 45))
    rect(x + 185, y + 78, x + 206, y + 81, (150, 128, 65))

def scene_climate(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (58, 76, 78))
    rect(x, y + 66, x + COL_W, y + SCENE_H, (91, 101, 97))
    rect(x + 8, y + 9, x + 60, y + 10, (121, 141, 139))
    rect(x + 8, y + 28, x + 60, y + 29, (121, 141, 139))
    rect(x + 62, y + 3, x + 63, y + 63, (121, 141, 139))
    disc(x + 178, y + 31, 23, (43, 106, 158))
    poly([(x + 164, y + 19), (x + 175, y + 15), (x + 186, y + 20), (x + 180, y + 27),
          (x + 169, y + 28), (x + 160, y + 24)], (112, 157, 96))
    poly([(x + 176, y + 33), (x + 188, y + 30), (x + 197, y + 37), (x + 194, y + 47),
          (x + 182, y + 49), (x + 174, y + 42)], (112, 157, 96))
    line(x + 168, y + 9, x + 168, y + 53, (70, 132, 177), 1)
    line(x + 188, y + 8, x + 188, y + 54, (70, 132, 177), 1)
    line(x + 156, y + 31, x + 200, y + 31, (70, 132, 177), 1)
    left_doc = [(x + 80, y + 27), (x + 119, y + 24), (x + 118, y + 62), (x + 112, y + 57),
                (x + 105, y + 63), (x + 98, y + 57), (x + 90, y + 65), (x + 80, y + 60)]
    right_doc = [(x + 127, y + 24), (x + 165, y + 29), (x + 165, y + 59), (x + 156, y + 64),
                 (x + 148, y + 58), (x + 140, y + 66), (x + 133, y + 59), (x + 128, y + 64)]
    poly(left_doc, (238, 234, 218))
    poly(right_doc, (238, 234, 218))
    for p in range(4):
        rect(x + 88, y + 32 + p * 6, x + 111, y + 33 + p * 6, (119, 118, 106))
    for p in range(4):
        rect(x + 134, y + 33 + p * 6, x + 158, y + 34 + p * 6, (119, 118, 106))
    rect(x + 118, y + 24, x + 127, y + 66, (58, 76, 78))
    rect(x + 69, y + 54, x + 91, y + 82, (64, 58, 54))
    rect(x + 67, y + 58, x + 93, y + 61, (107, 96, 86))
    rect(x + 67, y + 70, x + 93, y + 73, (107, 96, 86))
    line(x + 69, y + 55, x + 91, y + 81, (205, 69, 61), 2)
    line(x + 91, y + 55, x + 69, y + 81, (205, 69, 61), 2)
    for p in range(5):
        cx = x + 105 + p * 15
        rect(cx, y + 70, cx + 9, y + 78, (171, 139, 87))
        rect(cx + 1, y + 78, cx + 2, y + 86, (98, 92, 83))
        rect(cx + 7, y + 78, cx + 8, y + 86, (98, 92, 83))
        rect(cx - 1, y + 77, cx + 10, y + 79, (199, 166, 109))
    rect(x + 8, y + 80, x + 90, y + 82, (126, 122, 105))

def scene_gulf(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (25, 36, 57))
    rect(x, y + 62, x + COL_W, y + SCENE_H, (115, 99, 71))
    rect(x + 146, y + 70, x + COL_W, y + SCENE_H, (33, 73, 102))
    disc(x + 218, y + 13, 6, (232, 220, 173))
    for sx in range(x + 8, x + 220, 23):
        rect(sx, y + 78, sx + 13, y + 79, (68, 113, 140))
        rect(sx + 6, y + 85, sx + 19, y + 86, (63, 106, 133))
    rect(x + 19, y + 54, x + 21, y + 70, (151, 156, 160))
    rect(x + 10, y + 68, x + 30, y + 72, (104, 108, 111))
    dish = [(x + 17, y + 34), (x + 31, y + 27), (x + 46, y + 35), (x + 41, y + 46), (x + 25, y + 46)]
    poly(dish, (193, 198, 194))
    line(x + 31, y + 27, x + 26, y + 37, (124, 132, 128), 1)
    line(x + 36, y + 31, x + 23, y + 42, (124, 132, 128), 1)
    line(x + 24, y + 35, x + 42, y + 41, (124, 132, 128), 1)
    disc(x + 31, y + 37, 2, (72, 80, 80))
    line(x + 82, y + 5, x + 48, y + 38, (218, 133, 68), 2)
    line(x + 107, y + 3, x + 72, y + 37, (218, 133, 68), 2)
    poly([(x + 47, y + 37), (x + 42, y + 47), (x + 53, y + 43)], (235, 195, 111))
    poly([(x + 71, y + 36), (x + 67, y + 46), (x + 77, y + 41)], (235, 195, 111))
    disc(x + 50, y + 37, 5, (235, 160, 82))
    disc(x + 74, y + 34, 4, (235, 160, 82))
    poly([(x + 127, y + 14), (x + 147, y + 17), (x + 137, y + 21)], (184, 192, 201))
    poly([(x + 132, y + 17), (x + 142, y + 18), (x + 137, y + 26)], (184, 192, 201))
    rect(x + 136, y + 13, x + 138, y + 15, (235, 143, 71))
    rect(x + 124, y + 8, x + 151, y + 9, (134, 146, 160))
    poly([(x + 174, y + 38), (x + 193, y + 41), (x + 183, y + 45)], (184, 192, 201))
    poly([(x + 179, y + 41), (x + 188, y + 42), (x + 183, y + 50)], (184, 192, 201))
    rect(x + 177, y + 47, x + 189, y + 48, (134, 146, 160))
    rect(x + 182, y + 52, x + 204, y + 62, (74, 79, 83))
    rect(x + 198, y + 38, x + 202, y + 56, (83, 88, 91))
    rect(x + 206, y + 49, x + 209, y + 59, (83, 88, 91))
    rect(x + 186, y + 55, x + 191, y + 59, (226, 151, 70))
    disc(x + 203, y + 35, 5, (109, 114, 119))
    disc(x + 209, y + 29, 4, (96, 101, 106))
    rect(x + 156, y + 74, x + 231, y + 82, (63, 42, 40))
    rect(x + 162, y + 71, x + 177, y + 75, (157, 61, 50))
    rect(x + 180, y + 68, x + 190, y + 74, (172, 175, 168))
    rect(x + 190, y + 71, x + 196, y + 75, (157, 61, 50))
    rect(x + 220, y + 65, x + 224, y + 74, (92, 91, 82))
    line(x + 154, y + 83, x + 232, y + 83, (22, 50, 72), 1)

def scene_libya(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (13, 26, 49))
    rect(x, y + 51, x + COL_W, y + SCENE_H, (24, 53, 82))
    disc(x + 208, y + 15, 8, (225, 219, 190))
    for wy in (y + 58, y + 67, y + 77, y + 86):
        for wx in range(x + (wy % 17), x + 232, 34):
            rect(wx, wy, wx + 17, wy + 1, (54, 91, 121))
    rect(x + 4, y + 49, x + 64, y + 55, (73, 75, 72))
    rect(x + 9, y + 42, x + 12, y + 51, (104, 104, 96))
    rect(x + 8, y + 23, x + 10, y + 43, (153, 156, 148))
    flag = [(x + 10, y + 24), (x + 37, y + 24), (x + 37, y + 39), (x + 10, y + 39)]
    poly(flag, (104, 174, 213))
    disc(x + 23, y + 31, 5, (245, 245, 237))
    disc(x + 23, y + 31, 2, (104, 174, 213))
    poly([(x + 57, y + 55), (x + 120, y + 55), (x + 146, y + 68), (x + 139, y + 76),
          (x + 72, y + 76), (x + 50, y + 67)], (81, 89, 96))
    rect(x + 78, y + 48, x + 104, y + 58, (107, 116, 121))
    rect(x + 89, y + 38, x + 92, y + 49, (148, 155, 155))
    rect(x + 86, y + 44, x + 104, y + 46, (148, 155, 155))
    rect(x + 110, y + 43, x + 112, y + 56, (148, 155, 155))
    rect(x + 105, y + 47, x + 117, y + 49, (148, 155, 155))
    rect(x + 64, y + 61, x + 81, y + 65, (43, 48, 53))
    rect(x + 121, y + 60, x + 138, y + 64, (43, 48, 53))
    disc(x + 83, y + 57, 8, (235, 142, 54))
    disc(x + 83, y + 57, 4, (248, 212, 110))
    poly([(x + 83, y + 44), (x + 89, y + 57), (x + 77, y + 57)], (232, 107, 48))
    for p in range(3):
        disc(x + 84 + p * 4, y + 46 - p * 7, 5 + p * 2, (65, 66, 65))
    rect(x + 163, y + 62, x + 185, y + 64, (53, 87, 113))
    rect(x + 150, y + 70, x + 178, y + 72, (47, 81, 108))
    for dx, dy in ((x + 158, y + 21), (x + 187, y + 13), (x + 214, y + 31)):
        poly([(dx, dy), (dx + 17, dy + 4), (dx + 8, dy + 9)], (128, 141, 158))
        poly([(dx + 4, dy + 4), (dx + 12, dy + 5), (dx + 8, dy + 13)], (128, 141, 158))
        rect(dx + 7, dy + 3, dx + 9, dy + 5, (226, 81, 66))
    line(x + 158, y + 25, x + 151, y + 45, (96, 129, 153), 1)
    line(x + 187, y + 17, x + 181, y + 40, (96, 129, 153), 1)
    rect(x + 226, y + 46, x + 228, y + 90, (79, 82, 81))
    rect(x + 214, y + 46, x + 228, y + 48, (79, 82, 81))

def scene_mexico(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (31, 25, 36))
    rect(x, y + 64, x + COL_W, y + SCENE_H, (54, 46, 47))
    rect(x, y + 64, x + COL_W, y + 66, (102, 84, 65))
    for bx, bw, bh in ((x + 1, 39, 49), (x + 45, 28, 37), (x + 189, 49, 54), (x + 166, 20, 42)):
        rect(bx, y + 62 - bh, bx + bw, y + 64, (44, 38, 45))
        for wx in range(bx + 5, bx + bw - 3, 11):
            for wy in range(y + 66 - bh, y + 56, 10):
                rect(wx, wy, wx + 4, wy + 4, (188, 156, 84))
    poly([(x + 78, y + 63), (x + 101, y + 55), (x + 119, y + 63)], (47, 39, 43))
    rect(x + 80, y + 63, x + 117, y + 70, (60, 49, 44))
    disc(x + 85, y + 66, 4, (33, 31, 34))
    disc(x + 111, y + 66, 4, (33, 31, 34))
    rect(x + 92, y + 58, x + 105, y + 63, (68, 52, 40))
    poly([(x + 94, y + 59), (x + 99, y + 46), (x + 104, y + 59)], (225, 109, 39))
    poly([(x + 91, y + 60), (x + 96, y + 51), (x + 99, y + 60)], (241, 174, 62))
    for p in range(4):
        disc(x + 100 + p * 3, y + 47 - p * 6, 4 + p * 2, (63, 55, 58))
    rect(x + 144, y + 57, x + 176, y + 70, (53, 44, 45))
    rect(x + 151, y + 51, x + 169, y + 58, (43, 38, 42))
    disc(x + 150, y + 67, 4, (31, 29, 31))
    disc(x + 171, y + 67, 4, (31, 29, 31))
    poly([(x + 147, y + 57), (x + 154, y + 41), (x + 162, y + 57)], (227, 101, 34))
    disc(x + 154, y + 49, 5, (249, 186, 66))
    for p in range(3):
        disc(x + 156 + p * 2, y + 39 - p * 6, 5 + p * 2, (77, 63, 62))
    rect(x + 180, y + 60, x + 223, y + 63, (115, 91, 65))
    for bar in range(3):
        rect(x + 187 + bar * 11, y + 64, x + 190 + bar * 11, y + 70, (177, 139, 84))
    rect(x + 54, y + 11, x + 112, y + 19, (28, 31, 38))
    rect(x + 65, y + 19, x + 101, y + 27, (38, 42, 50))
    rect(x + 79, y + 27, x + 91, y + 31, (24, 27, 33))
    rect(x + 45, y + 12, x + 122, y + 13, (111, 121, 132))
    rect(x + 80, y + 6, x + 90, y + 12, (48, 52, 59))
    line(x + 84, y + 7, x + 84, y + 91, (220, 212, 168))
    line(x + 60, y + 6, x + 60, y + 73, (146, 147, 134))
    line(x + 110, y + 26, x + 139, y + 63, (145, 146, 133))
    line(x + 110, y + 26, x + 79, y + 62, (145, 146, 133))
    rect(x + 95, y + 37, x + 100, y + 65, (22, 22, 27))
    disc(x + 97, y + 34, 4, (22, 22, 27))
    rect(x + 86, y + 64, x + 107, y + 68, (22, 22, 27))
    rect(x + 84, y + 58, x + 91, y + 64, (52, 54, 59))
    rect(x + 102, y + 58, x + 109, y + 64, (52, 54, 59))
    rect(x + 94, y + 47, x + 101, y + 51, (126, 132, 135))
    rect(x + 73, y + 38, x + 79, y + 66, (26, 27, 32))
    disc(x + 76, y + 34, 3, (26, 27, 32))
    rect(x + 70, y + 45, x + 82, y + 49, (44, 47, 53))
    rect(x + 113, y + 38, x + 119, y + 66, (26, 27, 32))
    disc(x + 116, y + 34, 3, (26, 27, 32))
    rect(x + 110, y + 45, x + 122, y + 49, (44, 47, 53))

def scene_europe(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (198, 211, 220))
    rect(x, y + 58, x + COL_W, y + SCENE_H, (159, 170, 176))
    rect(x + 36, y + 4, x + 92, y + 33, (30, 66, 133))
    star_offsets = [(0, -10), (5, -9), (9, -5), (10, 0), (9, 5), (5, 9),
                    (0, 10), (-5, 9), (-9, 5), (-10, 0), (-9, -5), (-5, -9)]
    for ox, oy in star_offsets:
        cx, cy = x + 64 + ox, y + 18 + oy
        poly([(cx, cy - 2), (cx + 2, cy), (cx, cy + 2), (cx - 2, cy)], (247, 205, 69))
    poly([(x + 12, y + 44), (x + 61, y + 31), (x + 110, y + 44)], (222, 218, 205))
    rect(x + 16, y + 44, x + 106, y + 50, (236, 233, 220))
    for p in range(5):
        rect(x + 22 + p * 17, y + 50, x + 29 + p * 17, y + 83, (242, 239, 228))
        rect(x + 22 + p * 17, y + 50, x + 24 + p * 17, y + 83, (188, 184, 172))
    rect(x + 14, y + 83, x + 108, y + 87, (217, 212, 199))
    rect(x + 56, y + 58, x + 66, y + 82, (68, 75, 80))
    poly([(x + 118, y + 73), (x + 224, y + 73), (x + 214, y + 84), (x + 129, y + 84)], (87, 47, 46))
    rect(x + 120, y + 70, x + 225, y + 74, (129, 139, 142))
    rect(x + 181, y + 57, x + 204, y + 70, (214, 216, 209))
    rect(x + 186, y + 61, x + 198, y + 66, (75, 100, 123))
    rect(x + 205, y + 53, x + 210, y + 67, (107, 102, 96))
    rect(x + 195, y + 49, x + 218, y + 52, (119, 115, 108))
    disc(x + 195, y + 42, 14, (188, 53, 48))
    disc(x + 195, y + 42, 10, (238, 232, 216))
    line(x + 187, y + 34, x + 203, y + 50, (188, 53, 48), 3)
    line(x + 187, y + 50, x + 203, y + 34, (188, 53, 48), 3)
    rect(x + 226, y + 37, x + 228, y + 88, (90, 89, 83))
    rect(x + 226, y + 39, x + 239, y + 42, (240, 240, 235))
    rect(x + 226, y + 42, x + 239, y + 45, (49, 83, 158))
    rect(x + 226, y + 45, x + 239, y + 48, (186, 57, 52))
    rect(x + 16, y + 87, x + 228, y + 89, (118, 128, 132))

def scene_asia(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (240, 222, 194))
    rect(x, y + 41, x + COL_W, y + 43, (201, 171, 136))
    rect(x + 16, y + 5, x + 72, y + 14, (238, 139, 54))
    rect(x + 16, y + 14, x + 72, y + 24, (247, 245, 235))
    rect(x + 16, y + 24, x + 72, y + 34, (45, 127, 70))
    disc(x + 44, y + 19, 5, (40, 62, 130))
    disc(x + 44, y + 19, 2, (247, 245, 235))
    for ang in ((1, 0), (0, 1), (3, 1), (1, 3)):
        line(x + 44, y + 19, x + 44 + ang[0] * 3, y + 19 + ang[1] * 3, (247, 245, 235), 1)
        line(x + 44, y + 19, x + 44 - ang[0] * 3, y + 19 - ang[1] * 3, (247, 245, 235), 1)
    nepal = [(x + 126, y + 5), (x + 170, y + 5), (x + 155, y + 19), (x + 174, y + 19),
             (x + 137, y + 40), (x + 137, y + 5)]
    poly(nepal, (34, 64, 145))
    inner = [(x + 131, y + 8), (x + 163, y + 8), (x + 151, y + 18), (x + 166, y + 20),
             (x + 139, y + 35), (x + 139, y + 8)]
    poly(inner, (193, 50, 55))
    disc(x + 145, y + 14, 3, (247, 245, 235))
    disc(x + 147, y + 25, 4, (247, 245, 235))
    rect(x + 12, y + 52, x + 228, y + 54, (131, 127, 120))
    rect(x + 17, y + 55, x + 80, y + 76, (44, 79, 121))
    rect(x + 22, y + 59, x + 44, y + 68, (169, 204, 218))
    rect(x + 50, y + 59, x + 70, y + 68, (169, 204, 218))
    rect(x + 78, y + 58, x + 84, y + 76, (31, 55, 88))
    rect(x + 84, y + 54, x + 218, y + 74, (194, 199, 194))
    for p in range(5):
        rect(x + 91 + p * 25, y + 58, x + 107 + p * 25, y + 67, (72, 96, 117))
    rect(x + 84, y + 71, x + 218, y + 74, (112, 124, 131))
    for wx in (x + 34, x + 64, x + 98, x + 126, x + 154, x + 182, x + 210):
        disc(wx, y + 77, 4, (42, 43, 44))
        disc(wx, y + 77, 2, (146, 147, 142))
    poly([(x + 118, y + 84), (x + 145, y + 75), (x + 157, y + 82), (x + 132, y + 90)], (57, 70, 92))
    poly([(x + 205, y + 84), (x + 178, y + 75), (x + 166, y + 82), (x + 192, y + 90)], (57, 70, 92))
    rect(x + 152, y + 77, x + 174, y + 88, (226, 191, 156))
    rect(x + 147, y + 80, x + 152, y + 86, (226, 191, 156))
    rect(x + 174, y + 80, x + 179, y + 86, (226, 191, 156))
    rect(x + 160, y + 78, x + 166, y + 87, (190, 145, 112))
    rect(x + 12, y + 90, x + 228, y + 92, (172, 145, 116))

def scene_ukraine(x, y):
    rect(x, y, x + COL_W, y + SCENE_H, (16, 25, 48))
    for sx, sy in ((42, 9), (86, 20), (122, 7), (163, 18), (201, 9), (228, 30)):
        rect(x + sx, y + sy, x + sx + 1, y + sy + 1, (193, 203, 220))
    disc(x + 78, y + 11, 2, (222, 224, 214))
    rect(x + 7, y + 53, x + 35, y + 80, (35, 40, 49))
    rect(x + 39, y + 45, x + 72, y + 80, (30, 36, 46))
    rect(x + 76, y + 60, x + 99, y + 80, (38, 42, 50))
    rect(x + 103, y + 50, x + 126, y + 80, (32, 37, 46))
    for wx in (11, 19, 27, 44, 54, 62, 80, 88, 108, 116):
        rect(x + wx, y + 57, x + wx + 4, y + 62, (184, 154, 77))
    for wx in (44, 54, 62, 108, 116):
        rect(x + wx, y + 69, x + wx + 4, y + 74, (120, 135, 146))
    damaged = [(x + 132, y + 80), (x + 132, y + 34), (x + 168, y + 34), (x + 168, y + 45),
               (x + 180, y + 42), (x + 184, y + 52), (x + 180, y + 59), (x + 188, y + 66),
               (x + 196, y + 60), (x + 203, y + 50), (x + 207, y + 40), (x + 211, y + 34),
               (x + 217, y + 34), (x + 217, y + 80)]
    poly(damaged, (147, 139, 124))
    poly([(x + 132, y + 34), (x + 168, y + 34), (x + 168, y + 45), (x + 160, y + 47),
          (x + 151, y + 41), (x + 143, y + 47)], (96, 91, 83))
    poly([(x + 203, y + 50), (x + 211, y + 34), (x + 217, y + 34), (x + 217, y + 59),
          (x + 209, y + 56)], (96, 91, 83))
    for wy in (y + 41, y + 50, y + 59, y + 68):
        for wx in (x + 139, x + 150, x + 161, x + 175, x + 190, x + 201, x + 209):
            if not (wy == y + 50 and wx > x + 180) and not (wy == y + 41 and wx > x + 196):
                rect(wx, wy, wx + 6, wy + 5, (63, 73, 80))
    rect(x + 138, y + 47, x + 145, y + 54, (224, 133, 57))
    rect(x + 198, y + 68, x + 206, y + 74, (219, 111, 48))
    for p in range(3):
        disc(x + 190 + p * 3, y + 27 - p * 6, 5 + p * 2, (63, 62, 65))
    poly([(x + 45, y + 24), (x + 69, y + 28), (x + 55, y + 34)], (135, 146, 162))
    poly([(x + 50, y + 28), (x + 62, y + 29), (x + 55, y + 39)], (135, 146, 162))
    rect(x + 55, y + 26, x + 58, y + 29, (227, 81, 63))
    line(x + 52, y + 24, x + 72, y + 23, (83, 94, 110), 1)
    poly([(x + 96, y + 15), (x + 122, y + 18), (x + 107, y + 25)], (135, 146, 162))
    poly([(x + 102, y + 19), (x + 114, y + 19), (x + 107, y + 30)], (135, 146, 162))
    rect(x + 107, y + 17, x + 109, y + 19, (227, 81, 63))
    line(x + 101, y + 16, x + 124, y + 14, (83, 94, 110), 1)
    rect(x + 20, y + 20, x + 22, y + 82, (172, 178, 180))
    rect(x + 22, y + 21, x + 52, y + 33, (244, 245, 241))
    rect(x + 34, y + 21, x + 39, y + 33, (44, 84, 158))
    rect(x + 22, y + 25, x + 52, y + 29, (44, 84, 158))
    for fx in range(x + 9, x + 234, 19):
        rect(fx, y + 72, fx + 2, y + 92, (37, 42, 48))
        rect(fx + 8, y + 78, fx + 10, y + 92, (37, 42, 48))
    for fy in (y + 76, y + 82, y + 88):
        rect(x + 6, fy, x + 236, fy + 1, (94, 99, 104))
    for p in range(9):
        fx = x + 11 + p * 26
        line(fx, y + 74, fx + 8, y + 90, (78, 84, 90), 1)
    rect(x, y + 90, x + COL_W, y + 92, (85, 88, 92))

def draw_leads():
    saffron = (196, 116, 35)
    gold = (151, 113, 37)
    eu_blue = (30, 66, 133)
    leads = [
        ('MARKETS', GREEN, 'HUANG RETURNS AS NVIDIA CEO',
         'Shares surge 31% as board reinstates chief 11 days after resignation', scene_markets),
        ('CLIMATE', BLUE, 'COP31 COLLAPSES WITHOUT A PACT',
         'Draft drops fossil fuels; Guterres calls outcome deeply disappointing', scene_climate),
        ('GULF', RED, 'IRAN STRIKES US BASES IN BAHRAIN',
         'Two Patriot radars hit; Sitra factory burns, two wounded', scene_gulf),
        ('LIBYA', NAVY, 'UKRAINE SINKS RUSSIAN CORVETTE',
         'Drone attack in Benghazi port; UN mission seeks investigation', scene_libya),
        ('MEXICO', ORANGE, 'CHAPO ISIDRO RAID TOLL REACHES 20',
         'Four soldiers and 16 cartel members dead in Sinaloa', scene_mexico),
        ('EUROPE', eu_blue, 'EU HITS 60 BANKS WITH NEW SANCTIONS',
         'Crypto and 70 shadow-fleet vessels hit; Russian teams banned', scene_europe),
        ('ASIA', saffron, 'NEPAL AND INDIA SEAL AID PACT',
         'Modi meets Shah; 24,000 crore package and new train flagged off', scene_asia),
        ('UKRAINE', gold, 'KYIV STRIKES KILL 15 IN FIFTH WINTER',
         'Finland summons envoy; Russia warns Estonia over border', scene_ukraine),
    ]
    for index, (tag, colour, headline, caption, scene) in enumerate(leads):
        col = index % 4
        row = index // 4
        px = MARGIN + col * (COL_W + GUTTER)
        py = ROW_Y[row]
        draw_panel_base(px, py, tag, colour, headline, caption)
        scene(px, py)

BRIEFS = [
    "USA - Democrats clinch 258 House seats, largest since 1992",
    "USA - FBI probes suspected NCIC hack; Washington pauses gun checks",
    "USA - DOJ files to recover $1bn+ crypto stolen in Binance hack",
    "USA - Trump orders Army to pause lead azide detonation in Iowa",
    "USA - Amtrak train derails in Louisiana; 95 aboard, 5 hurt",
    "USA - Trump wants permanent Iran deal; may resume strikes",
    "USA - Iran drone and missile attacks hit year-long high, Trump says",
    "ICC - Tajikistan becomes 4th country to quit ICC since US push",
    "SPAIN - Court shelves case vs Puigdemont, clearing return from exile",
    "GERMANY - About 450 schools get bomb threats by email on Monday",
    "ZAMBIA - Opposition leader Mundubile charged with treason",
    "FRANCE - Melenchon gains 5 pts in runoff poll vs Le Pen, 65-35",
    "FRANCE - Tens of thousands march in 6th cost-of-living protest weekend",
    "RUSSIA - To spend $576m on 2 rail ferries to supply Kaliningrad",
    "SYRIA - US discussing military training for Syrian forces",
    "YEMEN - Govt claims 647 strikes on Houthi targets; 86 hit",
    "SUDAN - Saudi condemns drone attacks on Khartoum, UN building hit",
    "ISRAEL - Coalition talks fail; Eisenkot has until Dec 6 to form govt",
    "LEBANON - Villagers return home as Israeli pullback begins",
    "GAZA - Israeli strike on Beirut flat kills at least 5, wounds 25",
    "PERU - Aftershock watch on after M6.7 quake; no casualties",
    "INDONESIA - 24 confirmed dead in Banten candy factory fire",
    "SPORT - Verstappen wins Las Vegas GP ahead of Norris, Piastri",
    "SPORT - Alcaraz beats Zverev to win first ATP Finals title",
    "CULTURE - Australian broadcaster Molly Meldrum dies at 83",
    "KOREA - Education minister quits over AI-cheating exam rules row",
    "MARKETS - CrowdStrike buys Zscaler in $44bn deal; Asia stocks slide",
]

def draw_briefs():
    columns = (16, 524)
    start_y = BRIEF_TOP + 42
    pitch = 26
    for index, brief in enumerate(BRIEFS):
        col = 0 if index < 14 else 1
        row = index if col == 0 else index - 14
        bx = columns[col]
        by = start_y + row * pitch
        text = truncate_width(brief, 480, 1)
        draw_text(bx, by, text, 1, INK)

def main():
    rect(0, 0, 1024, 1024, PAPER)
    draw_masthead()
    draw_leads()
    draw_briefs_frame()
    draw_briefs()
    draw_footer()
    rows = [bytes(buf[y * 3072:(y + 1) * 3072]) for y in range(1024)]
    outdir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    os.makedirs(outdir, exist_ok=True)
    png_write(os.path.join(outdir, 'entry.png'), 1024, 1024, rows)

if __name__ == '__main__':
    main()
