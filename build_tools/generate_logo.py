"""
Generate a new logo.png for Nimbus Adaptive Controller.
Replaces the old 'PROJECT NIMBUS' logo with 'NIMBUS ADAPTIVE CONTROLLER'.
Run from the project root: python build_tools/generate_logo.py
"""
from PIL import Image, ImageDraw, ImageFont

SIZE = 1024
img = Image.new('RGB', (SIZE, SIZE), (245, 245, 245))
draw = ImageDraw.Draw(img)

CLOUD_BLUE = (52, 152, 219)

# Cloud sits in the top ~50% of the image (base at y=430)
cloud_base_y = 430
cloud_left  = 190
cloud_right = 834

bumps = [
    (512, 155, 140),   # centre top — tallest
    (345, 230, 105),   # left-centre
    (679, 230, 105),   # right-centre
    (220, 305,  90),   # far left
    (804, 305,  90),   # far right
]
for (bx, by, br) in bumps:
    draw.ellipse([bx - br, by - br, bx + br, by + br], fill=CLOUD_BLUE)

# Flat bottom fill
draw.rectangle([cloud_left, 270, cloud_right, cloud_base_y], fill=CLOUD_BLUE)


def draw_cursor(draw, ox, oy, scale=1.0):
    """Draw a mouse-cursor arrow (white outline, dark fill)."""
    pts = [
        (0,  0),
        (0,  30),
        (8,  24),
        (14, 38),
        (19, 36),
        (13, 22),
        (22, 22),
    ]
    WHITE, DARK = (255, 255, 255), (25, 25, 25)
    outline = [(ox + p[0] * scale, oy + p[1] * scale) for p in pts]
    draw.polygon(outline, fill=WHITE)
    s = 0.78
    inner = [(ox + p[0] * scale * s + scale * 1.5,
              oy + p[1] * scale * s + scale * 1.5) for p in pts]
    draw.polygon(inner, fill=DARK)


def draw_joystick(draw, ox, oy, scale=1.0):
    """Draw a simple arcade-joystick (white outline, dark fill)."""
    WHITE, DARK = (255, 255, 255), (25, 25, 25)
    bw, bh = int(72 * scale), int(46 * scale)
    bx, by = ox - bw // 2, oy + int(35 * scale)
    draw.rectangle([bx, by, bx + bw, by + bh], fill=WHITE)
    draw.rectangle([bx + 5, by + 5, bx + bw - 5, by + bh - 5], fill=DARK)
    sw = int(16 * scale)
    sh = int(65 * scale)
    sx = ox - sw // 2
    draw.rectangle([sx, oy - sh // 2, sx + sw, oy + sh // 2], fill=WHITE)
    draw.rectangle([sx + 4, oy - sh // 2 + 4, sx + sw - 4, oy + sh // 2 - 4], fill=DARK)
    br = int(22 * scale)
    top = oy - sh // 2
    draw.ellipse([ox - br, top - br, ox + br, top + br], fill=WHITE)
    draw.ellipse([ox - br + 4, top - br + 4, ox + br - 4, top + br - 4], fill=DARK)


# Icons inside the cloud — centred vertically in the cloud body
icon_y = 300
draw_cursor(draw,   ox=310, oy=icon_y, scale=4.8)
draw_joystick(draw, ox=650, oy=icon_y + 20, scale=2.1)

# ── Text ──────────────────────────────────────────────────────────────────────
font_candidates = [
    'C:/Windows/Fonts/ariblk.ttf',   # Arial Black (boldest)
    'C:/Windows/Fonts/arialbd.ttf',  # Arial Bold
    'C:/Windows/Fonts/arial.ttf',
]
font_large = font_sub = None
for fp in font_candidates:
    try:
        font_large = ImageFont.truetype(fp, 100)
        font_sub   = ImageFont.truetype(fp, 56)
        break
    except OSError:
        pass
if font_large is None:
    font_large = font_sub = ImageFont.load_default()

TEXT_COLOR = (20, 20, 20)

def centered_text(draw, text, font, y):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    draw.text(((SIZE - w) // 2, y), text, font=font, fill=TEXT_COLOR)
    return bbox[3] - bbox[1]   # return line height

y = 530
h1 = centered_text(draw, 'NIMBUS',     font_large, y);  y += h1 + 14
h2 = centered_text(draw, 'ADAPTIVE',   font_sub,   y);  y += h2 + 8
centered_text(draw, 'CONTROLLER', font_sub,   y)

img.save('logo.png', 'PNG')
print('logo.png saved successfully.')
