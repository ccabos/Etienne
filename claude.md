# Etienne Cabos - Family History Documentation

## Project Overview

This is a **genealogy documentation website** for Etienne Cabos (1737-1808), a French Huguenot whose life spanned France, Prussia, and the Netherlands. The site is written in **German** and built with **MkDocs** using the **Material theme**.

**Live site:** https://ccabos.github.io/Etienne/

## Technology Stack

- **Static Site Generator:** MkDocs
- **Theme:** mkdocs-material
- **Plugins:** glightbox (image lightbox), search (German)
- **Deployment:** GitHub Pages via GitHub Actions
- **Language:** German (de)

## Project Structure

```
├── docs/
│   ├── index.md              # Main narrative page
│   ├── zeitleiste.md         # Timeline
│   ├── stammbaum.md          # Family tree
│   ├── quellen.md            # Sources/bibliography
│   ├── dokumente/            # Historical document pages
│   │   ├── index.md          # Documents overview
│   │   └── *.md              # Individual document pages
│   └── images/               # Historical document images
│       └── thumbnails/       # Thumbnail images
├── mkdocs.yml                # MkDocs configuration
└── .github/workflows/
    └── deploy.yml            # GitHub Actions deployment
```

## Common Tasks

### Local Development
```bash
pip install mkdocs mkdocs-material mkdocs-glightbox
mkdocs serve                  # Start local server at http://127.0.0.1:8000
mkdocs build                  # Build static site to /site
```

### Adding New Content
- New document pages go in `docs/dokumente/`
- Images go in `docs/images/`
- Update `mkdocs.yml` nav section when adding pages
- Use German for all content

### Markdown Features Used
- Material theme grid cards for document galleries
- Admonitions for notes/warnings
- Mermaid diagrams (for family trees)
- Image lightbox via glightbox plugin

## Content Guidelines

- All content is in **German**
- Historical documents include transcriptions and context
- Use the established card layout for document thumbnails
- Link images to their detail pages using the grid cards pattern
- Maintain consistent naming: `dokumente/topic-name.md`

## Key Files

- `mkdocs.yml` - Site configuration, navigation, theme settings
- `docs/index.md` - Main narrative with the full family story
- `docs/stammbaum.md` - Family tree visualization
- `docs/zeitleiste.md` - Chronological timeline

## Notes

- This is a private genealogical documentation project
- The family history spans 1729-1810
- Key locations: Caussade (France), Stettin (Prussia), Rotterdam, Berlin
