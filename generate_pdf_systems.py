#!/usr/bin/env python3
"""Generate a single PDF of the Systems Thinking book from the MkDocs markdown sources."""

import os
import re
import sys
import logging
import markdown
from fpdf import FPDF

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

# Navigation from mkdocs.yml with hierarchy level:
#   0 = top-level (Home, Introduction, Part headings, About)
#   1 = chapter within a part
#   2 = worked example (sub-section)
NAV = [
    ("Home", "index.md", 0),
    ("Introduction", "introduction.md", 0),
    ("Part I -- Foundations", "part1/index.md", 0),
    ("What Is a System?", "part1/what-is-a-system.md", 1),
    ("The Five-Level SE Hierarchy", "part1/se-hierarchy.md", 1),
    ("Product Line Thinking", "part1/product-lines.md", 1),
    ("STPA and STAMP", "part1/stpa-introduction.md", 1),
    ("Part II -- Social Systems", "part2/index.md", 0),
    ("Religion", "part2/religion.md", 1),
    ("Kingdom & Republic", "part2/kingdom-republic.md", 1),
    ("Ten Social Systems Compared", "part2/ten-systems.md", 1),
    ("Verein (e.V.)", "part2/examples/verein.md", 2),
    ("Democracy", "part2/examples/democracy.md", 2),
    ("Theocracy", "part2/examples/theocracy.md", 2),
    ("Corporation", "part2/examples/corporation.md", 2),
    ("University", "part2/examples/university.md", 2),
    ("Military", "part2/examples/military.md", 2),
    ("Family", "part2/examples/family.md", 2),
    ("One-Party State", "part2/examples/one-party-state.md", 2),
    ("Part III -- Development Frameworks", "part3/index.md", 0),
    ("Eight Frameworks Decomposed", "part3/frameworks.md", 1),
    ("The Framework Platform", "part3/framework-platform.md", 1),
    ("Hybrid Architectures", "part3/hybrids.md", 1),
    ("Part IV -- STPA Applied", "part4/index.md", 0),
    ("STPA on Religion", "part4/religion-stpa.md", 1),
    ("Control Structures in Social Systems", "part4/control-structures.md", 1),
    ("Architectural Remedies", "part4/remedies.md", 1),
    ("About", "about.md", 0),
]


def clean_markdown(text):
    """Pre-process markdown to remove MkDocs-specific syntax."""

    # Remove mermaid code blocks
    text = re.sub(r'```mermaid\n.*?```', '*[Diagram: see online version]*\n', text, flags=re.DOTALL)

    # Handle MkDocs admonitions: !!! type "title" / indented body
    def admonition_sub(m):
        title = m.group(2) or m.group(1).capitalize()
        body = m.group(3)
        body = re.sub(r'^    ', '', body, flags=re.MULTILINE)
        return f'\n> **{title}**\n>\n> {body}\n'
    text = re.sub(
        r'^!!! (\w+)(?: "([^"]*)")?\n((?:    .*\n?)+)',
        admonition_sub, text, flags=re.MULTILINE
    )

    # Remove MkDocs attribute lists: { .md-button }, { .lg }, etc.
    text = re.sub(r'\{[^}]*\.md-button[^}]*\}', '', text)
    text = re.sub(r'\{\s*[^}]*(?:width|loading|\.lg|\.middle)[^}]*\}', '', text)

    # Convert interactive visualization links to plain text notes
    text = re.sub(
        r'\[([^\]]*Interactive[^\]]*)\]\([^)]*\.html[^)]*\)',
        r'*[\1 -- see online version]*',
        text, flags=re.IGNORECASE
    )

    # Convert internal .md links to plain text
    text = re.sub(r'\[([^\]]+)\]\([^)]*\.md[^)]*\)', r'\1', text)

    # Handle footnotes: [^1] references and [^1]: definitions
    # Keep them as inline text
    text = re.sub(r'\[\^(\d+)\]:', r'[Footnote \1]:', text)
    text = re.sub(r'\[\^(\d+)\]', r'[\1]', text)

    # Remove material icons
    text = re.sub(r':material-[a-z-]+:\{[^}]*\}', '', text)
    text = re.sub(r':material-[a-z-]+:', '', text)

    # Clean up multiple blank lines
    text = re.sub(r'\n{4,}', '\n\n\n', text)

    return text


def md_to_html(md_text):
    """Convert markdown to HTML suitable for fpdf2's write_html."""
    html = markdown.markdown(md_text, extensions=['tables'], output_format='html')
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
            self.cell(0, 8, 'Systems Thinking -- From SE to STPA', align='C')
            self.ln(4)
            self.set_draw_color(200, 200, 200)
            self.line(10, self.get_y(), 200, self.get_y())
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font('LibSans', '', 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

    def add_title_page(self):
        self.add_page()
        self.ln(70)
        self.set_font('LibSerif', 'B', 26)
        self.set_text_color(63, 81, 181)  # Indigo
        self.cell(0, 14, 'Systems Thinking', align='C', new_x="LMARGIN", new_y="NEXT")
        self.set_font('LibSerif', '', 18)
        self.set_text_color(80, 80, 80)
        self.cell(0, 12, 'From SE to STPA', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(15)
        self.set_font('LibSerif', 'I', 12)
        self.set_text_color(100, 100, 100)
        self.multi_cell(0, 7,
            'Applying Systems Engineering Decomposition,\n'
            'Product Line Thinking, and STPA\n'
            'to Social and Technical Systems',
            align='C')
        self.ln(30)
        self.set_font('LibSans', '', 12)
        self.set_text_color(60, 60, 60)
        self.cell(0, 8, 'C. Cabos', align='C', new_x="LMARGIN", new_y="NEXT")
        self.ln(40)
        self.set_font('LibSans', '', 9)
        self.set_text_color(140, 140, 140)
        self.cell(0, 5, 'https://ccabos.github.io/systems/', align='C', new_x="LMARGIN", new_y="NEXT")

    def add_toc(self, toc_data):
        """Add table of contents with pre-computed page numbers."""
        self.add_page()
        self.set_font('LibSerif', 'B', 20)
        self.set_text_color(63, 81, 181)
        self.cell(0, 15, 'Table of Contents', align='L', new_x="LMARGIN", new_y="NEXT")
        self.ln(3)
        self.set_draw_color(63, 81, 181)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(8)

        for title, page_num, level in toc_data:
            if level == 0:
                self.set_font('LibSans', 'B', 11)
                self.set_text_color(40, 40, 40)
                indent = 0
            elif level == 1:
                self.set_font('LibSans', '', 10)
                self.set_text_color(70, 70, 70)
                indent = 8
            else:
                self.set_font('LibSans', '', 10)
                self.set_text_color(100, 100, 100)
                indent = 16

            self.set_x(15 + indent)
            title_w = 155 - indent
            self.cell(title_w, 7, title, new_x="RIGHT")
            self.cell(20, 7, str(page_num), align='R', new_x="LMARGIN", new_y="NEXT")

    def render_section(self, nav_title, md_content, level=0):
        """Render a section and return its starting page number."""
        self.add_page()
        page_num = self.page_no()
        self.toc_entries.append((nav_title, page_num, level))

        cleaned = clean_markdown(md_content)
        html = md_to_html(cleaned)

        self.set_font('LibSerif', '', 11)
        self.set_text_color(30, 30, 30)

        try:
            self.write_html(html)
        except Exception as e:
            # Fallback: strip HTML and write as plain text
            plain = re.sub(r'<[^>]+>', ' ', html)
            plain = re.sub(r'  +', ' ', plain).strip()
            if plain:
                self.set_font('LibSerif', '', 11)
                self.set_text_color(30, 30, 30)
                self.multi_cell(0, 6, plain)

        return page_num


def load_sections():
    """Load all section content from markdown files."""
    sections = []
    for nav_title, filename, level in NAV:
        filepath = os.path.join(DOCS_DIR, filename)
        if not os.path.exists(filepath):
            print(f"  Warning: {filepath} not found, skipping")
            continue
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        sections.append((nav_title, content, level))
    return sections


def build_pdf(sections, include_toc_data=None):
    """Build the PDF. If include_toc_data is provided, insert TOC after title page."""
    pdf = BookPDF()
    pdf.set_title("Systems Thinking -- From SE to STPA")
    pdf.set_author("C. Cabos")

    pdf.add_title_page()

    if include_toc_data:
        pdf.add_toc(include_toc_data)

    for i, (nav_title, content, level) in enumerate(sections):
        print(f"  [{i+1:2d}/{len(sections)}] {nav_title}")
        pdf.render_section(nav_title, content, level)

    return pdf


def main():
    print("Loading sections...")
    sections = load_sections()

    # Pass 1: Build without TOC to measure page numbers
    print("\nPass 1: Measuring page layout...")
    pdf1 = build_pdf(sections)

    # TOC will take ~1 page (28 entries at 7mm = 196mm, fits on 1 page)
    toc_pages = 1
    adjusted_toc = [
        (title, page_num + toc_pages, level)
        for title, page_num, level in pdf1.toc_entries
    ]

    # Pass 2: Build with TOC
    print("\nPass 2: Generating final PDF with table of contents...")
    pdf2 = build_pdf(sections, include_toc_data=adjusted_toc)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Systems_Thinking_Book.pdf")
    pdf2.output(output_path)
    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f"\n  PDF generated: {output_path}")
    print(f"  Total pages: {pdf2.pages_count}")
    print(f"  File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
