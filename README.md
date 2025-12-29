# Etienne Cabos (1737-1808)

Eine Dokumentation der Familiengeschichte von Etienne Cabos - ein Leben zwischen Frankreich, Preußen und den Niederlanden.

## Über dieses Projekt

Diese Website dokumentiert das Leben und die Familiengeschichte von **Etienne Cabos** (1737-1808), einem französischen Hugenotten aus Caussade im Quercy, dessen Lebensweg ihn durch halb Europa führte:

- **1737** - Geburt in Caussade, Frankreich
- **1772-1780** - Soldat in Preußen (Stettin)
- **1780-1792** - Kaufmann in Rotterdam
- **1792-1808** - Letzte Jahre in Berlin

## Website

Die Website ist unter [https://yourusername.github.io/Etienne/](https://yourusername.github.io/Etienne/) erreichbar.

## Lokale Entwicklung

### Voraussetzungen

- Python 3.x
- pip

### Installation

```bash
pip install mkdocs mkdocs-material
```

### Lokaler Server

```bash
mkdocs serve
```

Die Website ist dann unter `http://127.0.0.1:8000` erreichbar.

### Build

```bash
mkdocs build
```

## Struktur

```
├── docs/
│   ├── index.md              # Hauptseite mit der Familiengeschichte
│   ├── quellen.md            # Quellenverzeichnis
│   ├── dokumente/            # Detailseiten zu historischen Dokumenten
│   │   ├── index.md
│   │   ├── karte-1777.md
│   │   ├── hochzeit-laurens-1729.md
│   │   └── ...
│   └── images/               # Bilder der historischen Dokumente
│       └── thumbnails/       # Vorschaubilder
├── mkdocs.yml                # MkDocs Konfiguration
└── .github/
    └── workflows/
        └── deploy.yml        # GitHub Actions für automatisches Deployment
```

## Bilder hinzufügen

Um die historischen Dokumente mit Bildern zu versehen:

1. Legen Sie die Bilder im Ordner `docs/images/` ab
2. Benennen Sie die Bilder entsprechend den Platzhaltern in den Markdown-Dateien:
   - `karte-montauban-1777.jpg`
   - `hochzeit-laurens-1729.jpg`
   - `taufe-etienne-1737.jpg`
   - usw.

## GitHub Pages Deployment

Das Repository ist für automatisches Deployment zu GitHub Pages konfiguriert:

1. Gehen Sie zu **Settings > Pages**
2. Wählen Sie unter "Build and deployment" die Option **GitHub Actions**
3. Bei jedem Push auf `main` wird die Website automatisch aktualisiert

## Lizenz

Diese Familiengeschichte ist eine private genealogische Dokumentation.
