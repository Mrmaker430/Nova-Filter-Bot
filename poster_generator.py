import os
import requests
import logging
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps
from info import FILMS_LINK

logger = logging.getLogger(__name__)

FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_REGULAR = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

def load_font(font_path, size):
    try:
        return ImageFont.truetype(font_path, size)
    except Exception:
        return ImageFont.load_default()

def get_text_size(text, font):
    try:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        return font.getsize(text)

def wrap_text(text, font, max_width):
    if not text:
        return []
    words = text.split()
    lines = []
    current_line = []
    for word in words:
        test_line = ' '.join(current_line + [word])
        w, _ = get_text_size(test_line, font)
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                lines.append(word)
                current_line = []
    if current_line:
        lines.append(' '.join(current_line))
    return lines

def add_rounded_corners(im, rad):
    mask = Image.new('L', im.size, 255)
    corner = Image.new('L', (rad * 2, rad * 2), 0)
    draw = ImageDraw.Draw(corner)
    draw.ellipse((0, 0, rad * 2 - 1, rad * 2 - 1), fill=255)

    w, h = im.size
    mask.paste(corner.crop((0, 0, rad, rad)), (0, 0))
    mask.paste(corner.crop((0, rad, rad, rad * 2)), (0, h - rad))
    mask.paste(corner.crop((rad, 0, rad * 2, rad)), (w - rad, 0))
    mask.paste(corner.crop((rad, rad, rad * 2, rad * 2)), (w - rad, h - rad))

    im = im.convert('RGBA')
    im.putalpha(mask)
    return im

def create_gradient(width, height, color1, color2):
    base = Image.new('RGBA', (width, height), color1)
    top = Image.new('RGBA', (width, height), color2)
    mask = Image.new('L', (width, height))
    for y in range(height):
        alpha = int(255 * (y / height))
        mask.paste(alpha, (0, y, width, y+1))
    return Image.composite(top, base, mask)

def draw_telegram_icon(draw, x, y, size=32):
    cx = x + size // 2
    cy = y + size // 2
    # Draw Telegram blue circle
    draw.ellipse((x, y, x + size, y + size), fill='#229ED9')
    # Draw white paper plane
    # Vertices relative to cx, cy
    pts = [
        (cx + int(0.25 * size), cy - int(0.25 * size)), # point top-right
        (cx - int(0.3 * size), cy - int(0.06 * size)), # point left
        (cx - int(0.06 * size), cy + int(0.06 * size)), # fold center
        (cx - int(0.12 * size), cy + int(0.22 * size)), # bottom point
        (cx + int(0.03 * size), cy + int(0.12 * size))  # wing back
    ]
    draw.polygon(pts, fill='#FFFFFF')

async def generate_movie_poster(movie_data):
    """
    Generates a gorgeous 1280x720 movie poster banner using PIL.
    movie_data is expected to be a dictionary returned by get_poster().
    """
    width, height = 1280, 720

    # 1. Background (Blurred and Darkened backdrop)
    backdrop_img = None
    if movie_data.get('backdrop'):
        try:
            resp = requests.get(movie_data['backdrop'], timeout=5)
            if resp.status_code == 200:
                backdrop_img = Image.open(BytesIO(resp.content))
        except Exception as e:
            logger.warning(f"Failed to fetch backdrop from URL {movie_data.get('backdrop')}: {e}")

    if not backdrop_img and movie_data.get('poster'):
        try:
            resp = requests.get(movie_data['poster'], timeout=5)
            if resp.status_code == 200:
                backdrop_img = Image.open(BytesIO(resp.content))
        except Exception as e:
            logger.warning(f"Failed to fetch poster as backup backdrop: {e}")

    if backdrop_img:
        # Fit, Blur and Darken
        backdrop_img = ImageOps.fit(backdrop_img, (width, height))
        backdrop_img = backdrop_img.filter(ImageFilter.GaussianBlur(radius=15))
        overlay = Image.new('RGBA', (width, height), (0, 0, 0, 160)) # opacity 160/255
        canvas = Image.alpha_composite(backdrop_img.convert('RGBA'), overlay)
    else:
        # Fallback to elegant cinematic gradient
        canvas = create_gradient(width, height, (15, 23, 42, 255), (44, 24, 16, 255))

    draw = ImageDraw.Draw(canvas)

    # 2. Draw Poster on the right
    poster_loaded = False
    if movie_data.get('poster'):
        try:
            resp = requests.get(movie_data['poster'], timeout=5)
            if resp.status_code == 200:
                post_img = Image.open(BytesIO(resp.content))
                post_img = ImageOps.fit(post_img, (340, 510))
                post_img = add_rounded_corners(post_img, 12)

                # Draw white border background
                # A rounded rectangle with 6px padding on all sides: 340+12=352, 510+12=522
                draw.rounded_rectangle(
                    [(850, 100), (850 + 352, 100 + 522)],
                    radius=15,
                    fill="#FFFFFF"
                )

                # Paste poster inside
                canvas.paste(post_img, (856, 106), post_img)
                poster_loaded = True
        except Exception as e:
            logger.warning(f"Failed to render poster on canvas: {e}")

    # Fallback border/placeholder if poster download fails
    if not poster_loaded:
        draw.rounded_rectangle(
            [(850, 100), (850 + 352, 100 + 522)],
            radius=15,
            fill="#1E293B"
        )
        # Draw placeholder text inside
        f_placeholder = load_font(FONT_BOLD, 24)
        tw, th = get_text_size("NO POSTER", f_placeholder)
        draw.text((850 + 176 - tw//2, 100 + 261 - th//2), "NO POSTER", font=f_placeholder, fill="#94A3B8")

    # 3. Draw Left-Side Elements
    # A. Title & Rating
    title = str(movie_data.get('title', '')).upper()
    font_title = load_font(FONT_BOLD, 44)
    rating = movie_data.get('rating')

    # Calculate IMDb Rating Badge dimensions
    badge_w = 0
    badge_h = 0
    badge_text = ""
    font_rating = None
    if rating:
        font_rating = load_font(FONT_BOLD, 20)
        badge_text = f"★ {rating:.1f} IMDb"
        tw, th = get_text_size(badge_text, font_rating)
        badge_w = tw + 24
        badge_h = th + 12

    # Wrap title - if rating is present, reduce wrap limit to leave space for rating
    max_title_width = 720
    if rating:
        max_title_width = 720 - (badge_w + 20)

    title_lines = wrap_text(title, font_title, max_title_width)
    current_y = 100

    for i, line in enumerate(title_lines):
        draw.text((60, current_y), line, font=font_title, fill="#FFFFFF")
        lw, lh = get_text_size(line, font_title)

        # If last line and rating exists, place rating beside the title
        if i == len(title_lines) - 1 and rating:
            badge_x = 60 + lw + 20
            # Center vertically with the title line
            badge_y = current_y + (lh - badge_h) // 2
            draw.rounded_rectangle(
                [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
                radius=8,
                fill="#F5C518"
            )
            draw.text((badge_x + 12, badge_y + 6), badge_text, font=font_rating, fill="#000000")
        current_y += lh + 8

    if not title_lines and rating:
        badge_x = 60
        badge_y = current_y
        draw.rounded_rectangle(
            [(badge_x, badge_y), (badge_x + badge_w, badge_y + badge_h)],
            radius=8,
            fill="#F5C518"
        )
        draw.text((badge_x + 12, badge_y + 6), badge_text, font=font_rating, fill="#000000")
        current_y += badge_h + 8

    # Draw solid underline under title
    underline_y = current_y + 8
    draw.line([(60, underline_y), (780, underline_y)], fill="#FFFFFF", width=3)
    current_y = underline_y + 12

    # C. Plot description
    plot_text = movie_data.get('plot') or "No description available."
    font_plot = load_font(FONT_REGULAR, 22)
    plot_lines = wrap_text(plot_text, font_plot, 720)

    # Limit plot to max 4 lines
    if len(plot_lines) > 4:
        plot_lines = plot_lines[:3]
        plot_lines[-1] += "..."

    for line in plot_lines:
        draw.text((60, current_y), line, font=font_plot, fill="#E2E8F0")
        _, lh = get_text_size(line, font_plot)
        current_y += lh + 6

    # D. Metadata badges (Pills)
    # Target badges dynamically to decrease gaps
    badge_y = current_y + 15
    badges = []

    # Kind / Media Type
    kind = str(movie_data.get('kind', 'movie')).lower()
    if kind == 'tv':
        seasons = movie_data.get('seasons')
        if seasons:
            badges.append(f"{seasons} SEASON" if seasons == 1 else f"{seasons} SEASONS")
        else:
            badges.append("TV SERIES")
    else:
        badges.append("MOVIE")
        runtime = movie_data.get('runtime')
        if runtime:
            badges.append(f"{runtime} MIN")

    # Genres (Up to 2 genres)
    genres_list = [g.strip() for g in str(movie_data.get('genres', '')).split(',') if g.strip()]
    for g in genres_list[:2]:
        badges.append(g.upper())

    # Year
    year = movie_data.get('year')
    if year:
        badges.append(str(year))

    # Draw badges
    current_x = 60
    font_badge = load_font(FONT_BOLD, 18)
    badge_max_h = 0
    for b_text in badges:
        bw, bh = get_text_size(b_text, font_badge)
        pill_w = bw + 20
        pill_h = bh + 12
        badge_max_h = max(badge_max_h, pill_h)
        # Semi-transparent high-contrast blue background with a medium radius 10
        draw.rounded_rectangle(
            [(current_x, badge_y), (current_x + pill_w, badge_y + pill_h)],
            radius=10,
            fill=(30, 64, 175, 180)
        )
        draw.text((current_x + 10, badge_y + 6), b_text, font=font_badge, fill="#FFFFFF")
        current_x += pill_w + 12

    # E. Watermark Banner
    watermark_text = os.environ.get("POSTER_WATERMARK")
    if not watermark_text:
        if FILMS_LINK and "t.me/" in FILMS_LINK:
            watermark_text = "@" + FILMS_LINK.split("t.me/")[1].strip("/")
        else:
            watermark_text = "@cholochhitro"

    # Position the watermark dynamically with a tight gap of 20px, minimum 610px
    watermark_y = max(badge_y + badge_max_h + 20, 610)
    font_watermark = load_font(FONT_BOLD, 20)
    ww, wh = get_text_size(watermark_text, font_watermark)

    # Watermark pill containing Telegram icon and username
    # Total width: 15px pad + 32px icon + 10px gap + ww + 15px pad
    pill_w = 15 + 32 + 10 + ww + 15
    pill_h = 44
    draw.rounded_rectangle(
        [(60, watermark_y), (60 + pill_w, watermark_y + pill_h)],
        radius=10, # medium radius 10 instead of 22
        fill=(15, 23, 42, 180) # 70% opacity dark background for high visibility
    )
    # Draw Telegram icon
    draw_telegram_icon(draw, 60 + 6, watermark_y + 6, size=32)
    # Draw username text
    draw.text((60 + 6 + 32 + 10, watermark_y + 11), watermark_text, font=font_watermark, fill="#FFFFFF")

    # Save to BytesIO
    out_io = BytesIO()
    out_io.name = "poster.png"
    canvas.convert('RGB').save(out_io, 'JPEG', quality=90)
    out_io.seek(0)
    return out_io
