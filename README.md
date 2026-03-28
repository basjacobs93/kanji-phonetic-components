# Kanji Components

A static web app for searching and browsing kanji with their components color-coded by function:

- **Blue** strokes = meaning radical (semantic component)
- **Red** strokes = phonetic component (sound)
- **Grey** strokes = other/unclassified

Uses [KanjiVG](https://kanjivg.tagaini.net/) SVG stroke data to color actual strokes within each kanji glyph.

## Data sources

- [EDRDG Kanji Phonetics](https://www.edrdg.org/~jwb/kanjiphonetics/) — 150 phonetic component mappings
- [KanjiVG](https://github.com/KanjiVG/kanjivg) (CC-BY-SA 3.0) — SVG stroke data
- [KANJIDIC2](http://www.edrdg.org/wiki/index.php/KANJIDIC_Project) — kanji meanings, readings, grade, JLPT
- [KRADFILE](https://www.edrdg.org/krad/kradinf.html) — radical decompositions

## Usage

Build the site (downloads data on first run):

```
uv run python build_data.py
```

Serve locally:

```
uv run python main.py
```

Open http://localhost:8000.

The `site/` folder is a self-contained static site deployable to GitHub Pages or Netlify.

## Features

- Search by kanji character, English meaning, or Japanese reading
- Browse by school grade, JLPT level, radical, or phonetic component
- Click any kanji to see its colored SVG with component legend
- Navigate to related kanji sharing the same phonetic component
