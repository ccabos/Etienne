#!/usr/bin/env python3
"""Generate a single PDF of the Etienne Cabos book from the MkDocs markdown sources."""

import os
import re
import io
import sys
import logging
import markdown
from fpdf import FPDF
from PIL import Image as PILImage

# Suppress fpdf2's noisy HTML parser warnings
logging.getLogger("fpdf.html").setLevel(logging.ERROR)

DOCS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")

FONTS = {
    "Serif": "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
    "SerifB": "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
    "SerifI": "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
    "SerifBI": "/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf",
    "Sans": "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "SansB": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "SansI": "/usr/share/fonts/truetype/liberation/LiberationSans-Italic.ttf",
    "SansBI": "/usr/share/fonts/truetype/liberation/LiberationSans-BoldItalic.ttf",
}

NAV = [
    ("Startseite", "index.de.md"),
    ("Zeitleiste", "zeitleiste.de.md"),
    ("Stammbaum", "stammbaum.de.md"),
    ("Historische Dokumente", "dokumente/index.de.md"),
    ("Historische Karten", "dokumente/karte-1777.de.md"),
    ("Hochzeit Laurens Cabos 1729", "dokumente/hochzeit-laurens-1729.de.md"),
    ("Taufe Etienne 1737", "dokumente/taufe-etienne-1737.de.md"),
    ("Kirchenregister Caussade Juli 1737", "dokumente/kirchenregister-caussade-juli-1737.de.md"),
    ("Taufe Pierre 1740", "dokumente/taufe-pierre-1740.de.md"),
    ("Hochzeit Jean Cabos 1760", "dokumente/hochzeit-jean-1760.de.md"),
    ("Hochzeit Anne Cabos 1771", "dokumente/hochzeit-anne-1771.de.md"),
    ("Hochzeit Stettin 1772", "dokumente/hochzeit-stettin-1772.de.md"),
    ("Geburten Stettin 1772-1777", "dokumente/geburten-stettin.de.md"),
    ("Kirchenbuch Kriegsende 1779", "dokumente/kriegsende-1779.de.md"),
    ("Militärregister", "dokumente/militaerregister.de.md"),
    ("Reisepass 1780", "dokumente/reisepass-1780.de.md"),
    ("Bürgerbuch Rotterdam", "dokumente/buergerbuch-rotterdam.de.md"),
    ("Taufen Rotterdam", "dokumente/taufen-rotterdam.de.md"),
    ("Begräbnisse Rotterdam", "dokumente/begraebnisse-rotterdam.de.md"),
    ("Unterhaltsvertrag 1792", "dokumente/unterhaltsvertrag-1792.de.md"),
    ("Taufe Berlin 1793", "dokumente/taufe-berlin-1793.de.md"),
    ("Zahnarzt in Halle 1794-1798", "dokumente/zahnarzt-halle.de.md"),
    ("Hochzeit Elisabeth 1807", "dokumente/hochzeit-elisabeth-1807.de.md"),
    ("Sterbeurkunde Etienne 1808", "dokumente/sterbeurkunde-1808.de.md"),
    ("Sterbeurkunde Maria Justine 1810", "dokumente/sterbeurkunde-justine-1810.de.md"),
    ("Bulletin 1907 (Sekundärquelle)", "dokumente/bulletin-1907.de.md"),
    ("Forschungsausblick", "dokumente/forschungsausblick.de.md"),
    ("Quellen", "quellen.de.md"),
]

# Emoji and unicode symbols to strip (not supported by Liberation fonts)
EMOJI_RE = re.compile(
    "["
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F300-\U0001F9FF"  # misc symbols & pictographs
    "\U00002600-\U000027BF"  # misc symbols
    "\U0000FE0F"             # variation selector
    "\U00002B50"             # star
    "\U0001FA00-\U0001FAFF"  # extended symbols
    "]+", re.UNICODE
)


def strip_emojis(text):
    return EMOJI_RE.sub('', text)


def clean_markdown(text, file_dir):
    """Pre-process markdown to remove MkDocs-specific syntax."""
    text = re.sub(r'^---\n.*?\n---\n', '', text, flags=re.DOTALL)
    text = re.sub(r'<style>.*?</style>', '', text, flags=re.DOTALL)
    text = re.sub(r'```mermaid\n.*?```', '\n*[Diagramm: siehe Online-Version]*\n', text, flags=re.DOTALL)

    # Timeline sections
    text = re.sub(
        r'<div class="timeline-section"[^>]*>(.*?)</div>',
        lambda m: f"\n### {strip_emojis(re.sub(r'<[^>]+>', '', m.group(1))).strip()}\n",
        text
    )

    # Timeline items
    def timeline_item_replacer(m):
        content = m.group(0)
        year = re.search(r'<div class="timeline-year">(.*?)</div>', content)
        event = re.search(r'<div class="timeline-event">(.*?)</div>', content, re.DOTALL)
        location = re.search(r'<div class="timeline-location">(.*?)</div>', content, re.DOTALL)
        yr = strip_emojis(re.sub(r'<[^>]+>', '', year.group(1))).strip() if year else ""
        ev = strip_emojis(re.sub(r'<[^>]+>', '', event.group(1))).strip() if event else ""
        loc = strip_emojis(re.sub(r'<[^>]+>', '', location.group(1))).strip() if location else ""
        parts = re.split(r'</div>', content)
        extra_parts = []
        for p in parts[3:]:
            cleaned = re.sub(r'<[^>]+>', '', p).strip()
            if cleaned:
                extra_parts.append(cleaned)
        extra = " ".join(extra_parts)
        line = f"- **{yr}** -- {ev}"
        if loc:
            line += f" ({loc})"
        if extra:
            line += f" -- {extra}"
        return line + "\n"

    text = re.sub(
        r'<div class="timeline-item[^"]*"[^>]*>.*?</div>\s*</div>',
        timeline_item_replacer, text, flags=re.DOTALL
    )
    text = re.sub(r'<div class="timeline">\s*', '', text)
    text = re.sub(r'</?div[^>]*>', '', text)
    text = re.sub(r'<span[^>]*>.*?</span>', '', text, flags=re.DOTALL)

    # Merge italic translation paragraphs into preceding blockquote so they
    # render inside the same styled transcript box. Pattern:
    #     > *"original"*
    #
    #     *translation*
    # becomes:
    #     > *"original"*
    #     >
    #     > *translation*
    bq_italic_pattern = re.compile(
        r'((?:^> [^\n]*\n)+)\n(\*[^\n*][^\n]*?\*)\s*\n',
        re.MULTILINE,
    )
    def merge_italic_into_bq(m):
        bq_block = m.group(1).rstrip('\n')
        italic = m.group(2)
        return bq_block + '\n>\n> ' + italic + '\n'
    # Run repeatedly so consecutive translations get merged in turn
    prev = None
    while prev != text:
        prev = text
        text = bq_italic_pattern.sub(merge_italic_into_bq, text)

    # Also handle "**Übersetzung:**\n*translation*" following blockquote
    bq_uebersetzung_pattern = re.compile(
        r'((?:^> [^\n]*\n)+)\n\*\*Übersetzung:\*\*\s*\n(\*[^\n]+?\*)\s*\n',
        re.MULTILINE,
    )
    def merge_uebersetzung(m):
        bq_block = m.group(1).rstrip('\n')
        translation = m.group(2)
        return bq_block + '\n>\n> ' + translation + '\n'
    text = bq_uebersetzung_pattern.sub(merge_uebersetzung, text)

    # Admonitions: render as bold-italic intro paragraph (NOT blockquote/transcript box)
    def admonition_sub(m):
        title = m.group(2) or m.group(1).capitalize()
        body = m.group(3)
        body = re.sub(r'^    ', '', body, flags=re.MULTILINE).strip()
        return f'\n**{title}:** *{body}*\n'
    text = re.sub(
        r'^!!! (\w+)(?: "([^"]*)")?\n((?:    .*\n?)+)',
        admonition_sub, text, flags=re.MULTILINE
    )

    # MkDocs attribute lists
    text = re.sub(r'\{\s*[^}]*(?:width|loading|\.lg|\.middle)[^}]*\}', '', text)
    text = re.sub(r':material-[a-z-]+:\{[^}]*\}', '', text)
    text = re.sub(r':material-[a-z-]+:', '', text)

    # Fix image paths
    def fix_image_path(m):
        alt = m.group(1)
        path = m.group(2)
        if path.startswith('http'):
            return f'*[Bild: {alt}]*'
        abs_path = os.path.normpath(os.path.join(file_dir, path))
        if os.path.exists(abs_path):
            return f'![{alt}]({abs_path})'
        return f'*[Bild: {alt}]*'
    text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', fix_image_path, text)

    # Remove nav links
    text = re.sub(r'\[← [^\]]*\]\([^)]*\)\s*$', '', text, flags=re.MULTILINE)
    text = re.sub(r'^\s*\[→[^\]]*\]\([^)]*\)\s*$', '', text, flags=re.MULTILINE)

    # Convert internal links to plain text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\.md[^)]*\)', r'\1', text)
    text = re.sub(r'\[([^\]]+)\]\(#[^)]*\)', r'\1', text)

    # Strip emojis
    text = strip_emojis(text)

    # Clean up PDF link reference (keep as text)
    text = re.sub(r'\[([^\]]*)\]\(dokumente/[^)]*\.pdf\)', r'\1', text)

    # Clean up blanks
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text


def md_to_html(md_text):
    html = markdown.markdown(md_text, extensions=['tables'], output_format='html')

    # Replace blockquotes with sentinel markers for custom rendering
    # fpdf2's write_html has very limited styling support, so we render
    # blockquotes manually with drawing primitives in render_transcript_box()
    html = re.sub(
        r'<blockquote>\s*(.*?)\s*</blockquote>',
        lambda m: '<!--BQ_START-->' + m.group(1).strip() + '<!--BQ_END-->',
        html, flags=re.DOTALL
    )

    # fpdf2's write_html does not support nested formatting tags inside <td>
    # or <th> cells (it raises NotImplementedError on <strong>/<em>/<a> inside
    # them). Strip those tags inside table cells while keeping the text.
    def strip_inner_tags(m):
        cell = m.group(0)
        return re.sub(r'</?(?:strong|em|a|code|b|i)\b[^>]*>', '', cell)
    html = re.sub(r'<td[^>]*>.*?</td>', strip_inner_tags, html, flags=re.DOTALL)
    html = re.sub(r'<th[^>]*>.*?</th>', strip_inner_tags, html, flags=re.DOTALL)

    return html


class BookPDF(FPDF):
    def __init__(self):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.set_auto_page_break(auto=True, margin=20)
        self.add_font('LibSerif', '', FONTS["Serif"])
        self.add_font('LibSerif', 'B', FONTS["SerifB"])
        self.add_font('LibSerif', 'I', FONTS["SerifI"])
        self.add_font('LibSerif', 'BI', FONTS["SerifBI"])
        self.add_font('LibSans', '', FONTS["Sans"])
        self.add_font('LibSans', 'B', FONTS["SansB"])
        self.add_font('LibSans', 'I', FONTS["SansI"])
        self.add_font('LibSans', 'BI', FONTS["SansBI"])
        self.toc_entries = []

    def header(self):
        if self.page_no() > 1:
            self.set_font('LibSans', '', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 8, 'Etienne Cabos (1737-1808)', align='C')
            self.ln(4)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('LibSans', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Seite {self.page_no()}', align='C')

    def add_title_page(self):
        self.add_page()
        self.ln(60)
        self.set_font('LibSerif', 'B', 28)
        self.set_text_color(101, 67, 33)
        self.cell(0, 15, 'Etienne Cabos', align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_font('LibSerif', '', 18)
        self.cell(0, 12, '(1737 - 1808)', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(10)
        self.set_font('LibSerif', 'I', 14)
        self.set_text_color(80, 80, 80)
        self.cell(0, 10, 'Ein Leben zwischen Frankreich,', align='C', new_x="LMARGIN", new_y="NEXT")
        self.cell(0, 10, 'Preussen und den Niederlanden', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(20)
        map_path = os.path.join(DOCS_DIR, 'images', 'karte-stationen.png')
        if os.path.exists(map_path):
            with PILImage.open(map_path) as img:
                img.thumbnail((1200, 1200), PILImage.LANCZOS)
                if img.mode in ('RGBA', 'P', 'LA'):
                    bg = PILImage.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    bg.paste(img, mask=img.split()[-1] if 'A' in img.mode else None)
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=85, optimize=True)
                buf.seek(0)
            x = (210 - 120) / 2
            self.image(buf, x=x, w=120)
            self.ln(5)
            self.set_font('LibSans', 'I', 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 5, 'Lebensstationen: Caussade - Stettin - Rotterdam - Berlin',
                      align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(20)
        self.set_font('LibSans', '', 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 5, 'https://ccabos.github.io/Etienne/', align='C', new_x="LMARGIN", new_y="NEXT")

    def add_toc(self, toc_data):
        """Add table of contents with pre-computed page numbers."""
        self.add_page()
        self.set_font('LibSerif', 'B', 20)
        self.set_text_color(101, 67, 33)
        self.cell(0, 15, 'Inhaltsverzeichnis', align='L', new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_draw_color(101, 67, 33)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

        for title, page_num, is_document in toc_data:
            if is_document:
                self.set_font('LibSans', '', 10)
                self.set_text_color(80, 80, 80)
                indent = 8
            else:
                self.set_font('LibSans', 'B', 11)
                self.set_text_color(40, 40, 40)
                indent = 0
            self.set_x(15 + indent)
            title_w = 155 - indent
            # Dots between title and page number
            dots = '.' * max(2, int((title_w - self.get_string_width(title)) / self.get_string_width('.')))
            self.cell(title_w, 7, title, new_x="RIGHT")
            self.cell(20, 7, str(page_num), align='R', new_x="LMARGIN", new_y="NEXT")

    def place_image(self, img_path, alt_text=""):
        if not os.path.exists(img_path):
            return
        try:
            with PILImage.open(img_path) as pil_img:
                iw, ih = pil_img.size

                # Downscale large images for PDF (max 1600px wide)
                max_px = 1600
                if iw > max_px or ih > max_px:
                    pil_img.thumbnail((max_px, max_px), PILImage.LANCZOS)
                    iw, ih = pil_img.size

                # Convert to RGB if necessary (e.g. RGBA PNGs)
                if pil_img.mode in ('RGBA', 'P', 'LA'):
                    bg = PILImage.new('RGB', pil_img.size, (255, 255, 255))
                    if pil_img.mode == 'P':
                        pil_img = pil_img.convert('RGBA')
                    bg.paste(pil_img, mask=pil_img.split()[-1] if 'A' in pil_img.mode else None)
                    pil_img = bg
                elif pil_img.mode != 'RGB':
                    pil_img = pil_img.convert('RGB')

                # Save compressed to temp buffer
                buf = io.BytesIO()
                pil_img.save(buf, format='JPEG', quality=80, optimize=True)
                buf.seek(0)

            aspect = ih / iw
            max_w = 170  # mm
            w = min(max_w, iw * 0.264583)
            h = w * aspect
            available = self.h - self.get_y() - 30
            if h > available:
                if h > 220:
                    h = 220
                    w = h / aspect
                self.add_page()
            x = (210 - w) / 2
            self.image(buf, x=x, w=w)
            self.ln(3)
            if alt_text:
                self.set_font('LibSans', 'I', 8)
                self.set_text_color(100, 100, 100)
                self.cell(0, 4, alt_text, align='C', new_x="LMARGIN", new_y="NEXT")
                self.set_text_color(30, 30, 30)
            self.ln(3)
        except Exception as e:
            print(f"    Image error ({os.path.basename(img_path)}): {e}")
            pass

    def render_transcript_box(self, text):
        """Render a transcript blockquote as a visually distinct box with background and left border.

        Renders line-by-line with manual page break handling so the background fill
        and left border never bleed across page boundaries.
        """
        box_x = 15  # 5mm indent from page margin (10mm)
        box_w = 180  # width of the box
        padding = 3  # mm padding inside the box
        line_h = 5.5
        inner_w = box_w - 2 * padding

        # Split text into paragraphs to preserve blank-line spacing inside the box
        paragraphs = re.split(r'\n\s*\n', text.strip())

        self.ln(4)
        self.set_font('LibSerif', 'I', 10)
        self.set_text_color(60, 45, 30)

        # Pre-wrap each paragraph to lines using dry_run, building a flat list
        # of (line_text, is_blank) tuples for sequential rendering.
        rendered_lines = []
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            if i > 0:
                rendered_lines.append(('', True))  # blank spacer line
            wrapped = self.multi_cell(
                inner_w, line_h, para,
                dry_run=True, output='LINES'
            )
            for ln in wrapped:
                rendered_lines.append((ln, False))

        for line_text, is_blank in rendered_lines:
            # Page break check - leave room for footer
            if self.get_y() + line_h > (self.h - self.b_margin):
                self.add_page()
                # After add_page, font/colors persist but reset just in case
                self.set_font('LibSerif', 'I', 10)
                self.set_text_color(60, 45, 30)

            y = self.get_y()
            # Background fill across full box width
            self.set_fill_color(228, 215, 197)  # Warm tan #E4D7C5
            self.rect(box_x, y, box_w, line_h, style='F')
            # Thick brown left border for this line segment
            self.set_draw_color(141, 110, 76)  # Brown #8D6E4C
            self.set_line_width(1.0)
            self.line(box_x, y, box_x, y + line_h)
            # Render the text on top
            if not is_blank:
                self.set_xy(box_x + padding, y)
                self.cell(inner_w, line_h, line_text, new_x="LMARGIN", new_y="NEXT")
            else:
                self.set_y(y + line_h)

        # Reset state
        self.set_line_width(0.2)
        self.set_text_color(30, 30, 30)
        self.set_draw_color(0, 0, 0)
        self.ln(4)

    def render_section(self, nav_title, md_content, file_dir, is_document=False):
        """Render a section and return the starting page number."""
        self.add_page()
        page_num = self.page_no()
        self.toc_entries.append((nav_title, page_num, is_document))

        cleaned = clean_markdown(md_content, file_dir)
        html = md_to_html(cleaned)

        # Split out images for manual placement
        segments = re.split(r'(<img\s[^>]+/?>)', html)

        self.set_font('LibSerif', '', 11)
        self.set_text_color(30, 30, 30)

        for segment in segments:
            # Check for img tag
            img_match = re.search(r'src="([^"]+)"', segment)
            if segment.strip().startswith('<img') and img_match:
                img_path = img_match.group(1)
                alt_match = re.search(r'alt="([^"]*)"', segment)
                alt_text = alt_match.group(1) if alt_match else ""
                self.place_image(img_path, alt_text)
                continue

            # Remove any stray img tags
            segment = re.sub(r'<img[^>]*/?>', '', segment)
            if not segment.strip():
                continue

            # Split by blockquote markers for custom rendering
            bq_parts = re.split(r'(<!--BQ_START-->.*?<!--BQ_END-->)', segment, flags=re.DOTALL)

            for part in bq_parts:
                if part.startswith('<!--BQ_START-->'):
                    # Extract text, strip HTML tags, render as styled box.
                    # Preserve paragraph breaks: <p>...</p> becomes \n\n separators.
                    inner = re.sub(r'<!--/?BQ_(?:START|END)-->', '', part).strip()
                    inner = re.sub(r'</p>\s*<p>', '\n\n', inner)
                    inner = re.sub(r'<br\s*/?>', '\n', inner)
                    plain_text = re.sub(r'<[^>]+>', '', inner)
                    plain_text = re.sub(r'&quot;', '"', plain_text)
                    plain_text = re.sub(r'&amp;', '&', plain_text)
                    plain_text = re.sub(r'&lt;', '<', plain_text)
                    plain_text = re.sub(r'&gt;', '>', plain_text)
                    plain_text = re.sub(r'&#39;', "'", plain_text)
                    plain_text = re.sub(r'&nbsp;', ' ', plain_text)
                    # Collapse multiple spaces but preserve newlines
                    plain_text = re.sub(r'[ \t]+', ' ', plain_text).strip()
                    if plain_text:
                        self.render_transcript_box(plain_text)
                else:
                    if not part.strip():
                        continue
                    try:
                        self.set_font('LibSerif', '', 11)
                        self.write_html(part)
                    except Exception:
                        plain = re.sub(r'<[^>]+>', ' ', part)
                        plain = re.sub(r'  +', ' ', plain).strip()
                        if plain:
                            self.set_font('LibSerif', '', 11)
                            self.set_text_color(30, 30, 30)
                            self.multi_cell(0, 6, plain)
                            self.ln(2)

        return page_num


def load_sections():
    """Load all section content."""
    main_sections = {"index.de.md", "zeitleiste.de.md", "stammbaum.de.md", "quellen.de.md"}
    sections = []
    for nav_title, filename in NAV:
        filepath = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  Warning: {filepath} not found, skipping")
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        file_dir = os.path.dirname(filepath)
        is_doc = os.path.basename(filename) not in main_sections
        sections.append((nav_title, content, file_dir, is_doc))
    return sections


def build_pdf(sections, include_toc_data=None):
    """Build the PDF. If include_toc_data is provided, insert TOC after title page."""
    pdf = BookPDF()
    pdf.set_title("Etienne Cabos (1737-1808)")
    pdf.set_author("Familie Cabos")

    pdf.add_title_page()

    if include_toc_data:
        pdf.add_toc(include_toc_data)

    for i, (nav_title, content, file_dir, is_doc) in enumerate(sections):
        print(f"  [{i+1:2d}/{len(sections)}] {nav_title}")
        pdf.render_section(nav_title, content, file_dir, is_document=is_doc)

    return pdf


def main():
    print("Loading sections...")
    sections = load_sections()

    # Pass 1: Build without TOC to learn page numbers
    print("\nPass 1: Measuring page layout...")
    pdf1 = build_pdf(sections)

    # The TOC will take ~1 page (26 entries). Account for this offset.
    # Pass 1 has: title(1 page) + content pages
    # Pass 2 will have: title(1 page) + TOC(1 page) + content pages
    # So all content page numbers shift by +1
    toc_pages_needed = 1  # 26 entries at 7mm each = 182mm, fits on 1 page
    adjusted_toc = [
        (title, page_num + toc_pages_needed, is_doc)
        for title, page_num, is_doc in pdf1.toc_entries
    ]

    # Pass 2: Build with TOC
    print("\nPass 2: Generating final PDF with table of contents...")
    pdf2 = build_pdf(sections, include_toc_data=adjusted_toc)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Etienne_Cabos_Buch.pdf")
    pdf2.output(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n  PDF generated: {output_path}")
    print(f"  Total pages: {pdf2.pages_count}")
    print(f"  File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
