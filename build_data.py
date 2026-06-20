"""
Build script: downloads data sources, parses them, and generates
static site assets with color-coded kanji SVGs.

Usage: uv run python build_data.py
"""

import gzip
import json
import os
import subprocess
import sys
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from lxml import etree

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
SITE_DIR = ROOT / "site"
SITE_DATA_DIR = SITE_DIR / "data"
KANJI_OUT_DIR = SITE_DATA_DIR / "kanji"

KVG_NS = "http://kanjivg.tagaini.net"
NSMAP = {"kvg": KVG_NS}

COLOR_RADICAL = "#2563eb"
COLOR_PHONETIC = "#dc2626"
COLOR_DEFAULT = "#374151"

# 214 Kangxi radicals: number -> (char, name)
# Variant forms included where commonly used
KANGXI_RADICALS = {
    1: ("一", "one"), 2: ("丨", "line"), 3: ("丶", "dot"), 4: ("丿", "slash"),
    5: ("乙", "second"), 6: ("亅", "hook"), 7: ("二", "two"), 8: ("亠", "lid"),
    9: ("人", "person"), 10: ("儿", "legs"), 11: ("入", "enter"), 12: ("八", "eight"),
    13: ("冂", "down box"), 14: ("冖", "cover"), 15: ("冫", "ice"), 16: ("几", "table"),
    17: ("凵", "open box"), 18: ("刀", "knife"), 19: ("力", "power"), 20: ("勹", "wrap"),
    21: ("匕", "spoon"), 22: ("匚", "box"), 23: ("匸", "hiding"), 24: ("十", "ten"),
    25: ("卜", "divination"), 26: ("卩", "seal"), 27: ("厂", "cliff"), 28: ("厶", "private"),
    29: ("又", "again"), 30: ("口", "mouth"), 31: ("囗", "enclosure"), 32: ("土", "earth"),
    33: ("士", "scholar"), 34: ("夂", "go"), 35: ("夊", "go slowly"), 36: ("夕", "evening"),
    37: ("大", "big"), 38: ("女", "woman"), 39: ("子", "child"), 40: ("宀", "roof"),
    41: ("寸", "inch"), 42: ("小", "small"), 43: ("尢", "lame"), 44: ("尸", "corpse"),
    45: ("屮", "sprout"), 46: ("山", "mountain"), 47: ("巛", "river"), 48: ("工", "work"),
    49: ("己", "oneself"), 50: ("巾", "turban"), 51: ("干", "dry"), 52: ("幺", "short thread"),
    53: ("广", "dotted cliff"), 54: ("廴", "long stride"), 55: ("廾", "two hands"),
    56: ("弋", "shoot"), 57: ("弓", "bow"), 58: ("彐", "snout"), 59: ("彡", "bristle"),
    60: ("彳", "step"), 61: ("心", "heart"), 62: ("戈", "halberd"), 63: ("戸", "door"),
    64: ("手", "hand"), 65: ("支", "branch"), 66: ("攴", "rap"), 67: ("文", "script"),
    68: ("斗", "dipper"), 69: ("斤", "axe"), 70: ("方", "square"), 71: ("无", "not"),
    72: ("日", "sun"), 73: ("曰", "say"), 74: ("月", "moon"), 75: ("木", "tree"),
    76: ("欠", "lack"), 77: ("止", "stop"), 78: ("歹", "death"), 79: ("殳", "weapon"),
    80: ("毋", "do not"), 81: ("比", "compare"), 82: ("毛", "fur"), 83: ("氏", "clan"),
    84: ("气", "steam"), 85: ("水", "water"), 86: ("火", "fire"), 87: ("爪", "claw"),
    88: ("父", "father"), 89: ("爻", "double x"), 90: ("丬", "split wood"),
    91: ("片", "slice"), 92: ("牙", "fang"), 93: ("牛", "cow"), 94: ("犬", "dog"),
    95: ("玄", "dark"), 96: ("玉", "jade"), 97: ("瓜", "melon"), 98: ("瓦", "tile"),
    99: ("甘", "sweet"), 100: ("生", "life"), 101: ("用", "use"), 102: ("田", "field"),
    103: ("疋", "bolt of cloth"), 104: ("疒", "sickness"), 105: ("癶", "footsteps"),
    106: ("白", "white"), 107: ("皮", "skin"), 108: ("皿", "dish"), 109: ("目", "eye"),
    110: ("矛", "spear"), 111: ("矢", "arrow"), 112: ("石", "stone"), 113: ("示", "spirit"),
    114: ("禸", "track"), 115: ("禾", "grain"), 116: ("穴", "cave"), 117: ("立", "stand"),
    118: ("竹", "bamboo"), 119: ("米", "rice"), 120: ("糸", "thread"), 121: ("缶", "jar"),
    122: ("网", "net"), 123: ("羊", "sheep"), 124: ("羽", "feather"), 125: ("老", "old"),
    126: ("而", "and"), 127: ("耒", "plow"), 128: ("耳", "ear"), 129: ("聿", "brush"),
    130: ("肉", "meat"), 131: ("臣", "minister"), 132: ("自", "self"), 133: ("至", "arrive"),
    134: ("臼", "mortar"), 135: ("舌", "tongue"), 136: ("舛", "oppose"), 137: ("舟", "boat"),
    138: ("艮", "stopping"), 139: ("色", "color"), 140: ("艸", "grass"), 141: ("虍", "tiger"),
    142: ("虫", "insect"), 143: ("血", "blood"), 144: ("行", "go"), 145: ("衣", "clothes"),
    146: ("襾", "west"), 147: ("見", "see"), 148: ("角", "horn"), 149: ("言", "speech"),
    150: ("谷", "valley"), 151: ("豆", "bean"), 152: ("豕", "pig"), 153: ("豸", "badger"),
    154: ("貝", "shell"), 155: ("赤", "red"), 156: ("走", "run"), 157: ("足", "foot"),
    158: ("身", "body"), 159: ("車", "cart"), 160: ("辛", "bitter"), 161: ("辰", "morning"),
    162: ("辵", "walk"), 163: ("邑", "city"), 164: ("酉", "wine"), 165: ("釆", "distinguish"),
    166: ("里", "village"), 167: ("金", "gold"), 168: ("長", "long"), 169: ("門", "gate"),
    170: ("阜", "mound"), 171: ("隶", "slave"), 172: ("隹", "short-tailed bird"),
    173: ("雨", "rain"), 174: ("青", "blue"), 175: ("非", "wrong"), 176: ("面", "face"),
    177: ("革", "leather"), 178: ("韋", "tanned leather"), 179: ("韭", "leek"),
    180: ("音", "sound"), 181: ("頁", "leaf"), 182: ("風", "wind"), 183: ("飛", "fly"),
    184: ("食", "eat"), 185: ("首", "head"), 186: ("香", "fragrant"), 187: ("馬", "horse"),
    188: ("骨", "bone"), 189: ("高", "tall"), 190: ("髟", "hair"), 191: ("鬥", "fight"),
    192: ("鬯", "sacrificial wine"), 193: ("鬲", "cauldron"), 194: ("鬼", "ghost"),
    195: ("魚", "fish"), 196: ("鳥", "bird"), 197: ("鹵", "salt"), 198: ("鹿", "deer"),
    199: ("麦", "wheat"), 200: ("麻", "hemp"), 201: ("黄", "yellow"), 202: ("黍", "millet"),
    203: ("黒", "black"), 204: ("黹", "embroidery"), 205: ("黽", "frog"), 206: ("鼎", "tripod"),
    207: ("鼓", "drum"), 208: ("鼠", "rat"), 209: ("鼻", "nose"), 210: ("斉", "even"),
    211: ("歯", "tooth"), 212: ("竜", "dragon"), 213: ("亀", "turtle"), 214: ("龠", "flute"),
}


def download_data():
    """Download all required data files."""
    DATA_DIR.mkdir(exist_ok=True)

    kanjidic_path = DATA_DIR / "kanjidic2.xml.gz"
    if not kanjidic_path.exists():
        print("Downloading KANJIDIC2...")
        resp = httpx.get(
            "http://www.edrdg.org/pub/Nihongo/kanjidic2.xml.gz",
            follow_redirects=True,
            timeout=60,
        )
        resp.raise_for_status()
        kanjidic_path.write_bytes(resp.content)

    phonetics_path = DATA_DIR / "phonetics.html"
    if not phonetics_path.exists():
        print("Downloading phonetics page...")
        resp = httpx.get(
            "https://www.edrdg.org/~jwb/kanjiphonetics/",
            follow_redirects=True,
            timeout=60,
        )
        resp.raise_for_status()
        phonetics_path.write_text(resp.text, encoding="utf-8")

    kanjivg_dir = DATA_DIR / "kanjivg"
    if not kanjivg_dir.exists():
        print("Cloning KanjiVG repository...")
        subprocess.run(
            ["git", "clone", "--depth=1", "https://github.com/KanjiVG/kanjivg.git", str(kanjivg_dir)],
            check=True,
        )

    kradfile_path = DATA_DIR / "kradfile"
    if not kradfile_path.exists():
        print("Downloading KRADFILE...")
        # Try the gzipped version first
        resp = httpx.get(
            "http://ftp.edrdg.org/pub/Nihongo/kradfile.gz",
            follow_redirects=True,
            timeout=60,
        )
        resp.raise_for_status()
        kradfile_path.write_bytes(gzip.decompress(resp.content))

    print("All data downloaded.")


def parse_kanjidic2():
    """Parse KANJIDIC2 XML into a dict keyed by character."""
    print("Parsing KANJIDIC2...")
    path = DATA_DIR / "kanjidic2.xml.gz"
    with gzip.open(path) as f:
        tree = etree.parse(f)

    kanji_db = {}
    for char_elem in tree.findall("character"):
        literal = char_elem.findtext("literal")

        # Readings
        on_readings = []
        kun_readings = []
        meanings = []
        rmgroup = char_elem.find("reading_meaning/rmgroup")
        if rmgroup is not None:
            for r in rmgroup.findall("reading"):
                if r.get("r_type") == "ja_on":
                    on_readings.append(r.text)
                elif r.get("r_type") == "ja_kun":
                    kun_readings.append(r.text)
            for m in rmgroup.findall("meaning"):
                # Only English meanings (no m_lang attribute)
                if m.get("m_lang") is None:
                    meanings.append(m.text)

        # Misc info
        misc = char_elem.find("misc")
        grade = misc.findtext("grade")
        jlpt = misc.findtext("jlpt")
        freq = misc.findtext("freq")
        stroke_count = misc.findtext("stroke_count")

        # Radical
        rad_num = None
        for rv in char_elem.findall("radical/rad_value"):
            if rv.get("rad_type") == "classical":
                rad_num = int(rv.text)

        kanji_db[literal] = {
            "character": literal,
            "meanings": meanings,
            "on": on_readings,
            "kun": kun_readings,
            "strokes": int(stroke_count) if stroke_count else None,
            "grade": int(grade) if grade else None,
            "jlpt": int(jlpt) if jlpt else None,
            "freq": int(freq) if freq else None,
            "radical_number": rad_num,
        }

    print(f"  Parsed {len(kanji_db)} kanji.")
    return kanji_db


def parse_phonetics():
    """Parse the EDRDG phonetics page HTML.

    Row format: number | component | reading | name | type | kanji1 | kanji2 | ...
    Each kanji cell has an <a> link with the kanji character (sometimes with * suffix).
    Rows starting with an <a name="K..."> anchor are separator rows and skipped.
    """
    print("Parsing phonetics page...")
    html = (DATA_DIR / "phonetics.html").read_text(encoding="utf-8")
    soup = BeautifulSoup(html, "html.parser")

    kanji_to_phonetic = {}
    phonetic_info = {}

    # Find the main data table (the large one with K-anchors)
    tables = soup.find_all("table")
    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            # Data rows have: number, component, reading, name, type, then 1+ kanji cells
            if len(cells) < 6:
                continue

            # First cell is the entry number (e.g. "1", "130", "R1", "R20").
            # Skip rows that are just anchors (no number).
            num_text = cells[0].get_text(strip=True)
            if not any(c.isdigit() for c in num_text):
                continue

            # cells[1] = component character (inside <font size="+3">)
            component = cells[1].get_text(strip=True)
            reading = cells[2].get_text(strip=True)
            name = cells[3].get_text(strip=True)
            comp_type = cells[4].get_text(strip=True)

            # cells[5:] each contain one kanji with a link
            kanji_list = []
            for cell in cells[5:]:
                for link in cell.find_all("a"):
                    text = link.get_text(strip=True).rstrip("*")
                    if len(text) == 1 and ord(text) > 0x3000:
                        kanji_list.append(text)

            if not component or not kanji_list:
                continue

            # Merge if component already seen (e.g. appears in both standard and rhyming)
            if component in phonetic_info:
                existing = phonetic_info[component]["kanji"]
                for k in kanji_list:
                    if k not in existing:
                        existing.append(k)
            else:
                phonetic_info[component] = {
                    "reading": reading,
                    "name": name,
                    "type": comp_type,
                    "kanji": kanji_list,
                }

            for k in kanji_list:
                kanji_to_phonetic[k] = component

    print(f"  Found {len(phonetic_info)} phonetic components, {len(kanji_to_phonetic)} kanji mappings.")
    return kanji_to_phonetic, phonetic_info


def parse_kradfile():
    """Parse KRADFILE into kanji -> components mapping."""
    print("Parsing KRADFILE...")
    path = DATA_DIR / "kradfile"
    content = path.read_text(encoding="euc-jp", errors="replace")

    kanji_to_components = {}
    for line in content.splitlines():
        if line.startswith("#") or not line.strip():
            continue
        parts = line.split(" : ")
        if len(parts) != 2:
            continue
        kanji = parts[0].strip()
        components = parts[1].strip().split()
        kanji_to_components[kanji] = components

    print(f"  Parsed {len(kanji_to_components)} kanji decompositions.")
    return kanji_to_components


def expand_phonetics(kanji_db, kanji_to_phonetic, phonetic_info):
    """Expand phonetic mappings using KanjiVG element decomposition + ON reading match.

    The EDRDG page only lists a curated subset. We find additional kanji that
    contain a phonetic component (per KanjiVG grouping) and share its ON reading.
    """
    print("Expanding phonetic mappings via KanjiVG elements...")
    kanjivg_dir = DATA_DIR / "kanjivg" / "kanji"

    # Build kanji -> KanjiVG element set
    kanji_elements = {}
    for svg_path in kanjivg_dir.glob("*.svg"):
        stem = svg_path.stem
        if "-" in stem:
            continue
        try:
            char = chr(int(stem, 16))
        except ValueError:
            continue
        tree = etree.parse(str(svg_path))
        root = tree.getroot()
        elements = set()
        for g in root.iter("{http://www.w3.org/2000/svg}g"):
            el = g.get(f"{{{KVG_NS}}}element")
            if el and el != char:
                elements.add(el)
        if elements:
            kanji_elements[char] = elements

    # For each phonetic component, find kanji containing it with matching ON reading
    added = 0
    for comp_char, info in phonetic_info.items():
        comp_on = set(kanji_db.get(comp_char, {}).get("on", []))
        if not comp_on:
            continue
        for kanji, elements in kanji_elements.items():
            if kanji in kanji_to_phonetic:
                continue
            if comp_char not in elements:
                continue
            kanji_on = set(kanji_db.get(kanji, {}).get("on", []))
            if kanji_on & comp_on:
                kanji_to_phonetic[kanji] = comp_char
                info["kanji"].append(kanji)
                added += 1

    print(f"  Added {added} kanji, total now {len(kanji_to_phonetic)}.")


# KanjiVG can tag several groups with kvg:radical (e.g. both the traditional
# and the Nelson radical). Prefer the standard classical radical when choosing.
RADICAL_PRIORITY = ["general", "tradit", "nelson", "jis"]


def find_radical_paths(svg_root, radical_char=None):
    """Find the path ids of the single group representing the kanji's radical.

    A kanji like 辞 tags both 舌 (nelson) and 辛 (tradit) with kvg:radical, which
    would colour nearly the whole character. We pick one group: the one whose
    element matches the kanji's classical radical char if known, otherwise the
    highest-priority radical type.
    """
    candidates = []
    for g in svg_root.iter("{http://www.w3.org/2000/svg}g"):
        rad_type = g.get(f"{{{KVG_NS}}}radical")
        if rad_type:
            candidates.append((g, rad_type, g.get(f"{{{KVG_NS}}}element")))
    if not candidates:
        return set()

    chosen = None
    if radical_char:
        chosen = next((g for g, _, el in candidates if el == radical_char), None)
    if chosen is None:
        candidates.sort(
            key=lambda c: RADICAL_PRIORITY.index(c[1]) if c[1] in RADICAL_PRIORITY else len(RADICAL_PRIORITY)
        )
        chosen = candidates[0][0]

    return {p.get("id") for p in chosen.iter("{http://www.w3.org/2000/svg}path") if p.get("id")}


def find_phonetic_paths(svg_root, phonetic_char):
    """Find all path elements under a group matching the phonetic component."""
    phonetic_paths = set()

    # Strategy 1: find <g kvg:element="X"> matching the phonetic character
    for g in svg_root.iter("{http://www.w3.org/2000/svg}g"):
        element_attr = g.get(f"{{{KVG_NS}}}element")
        if element_attr == phonetic_char:
            for path in g.iter("{http://www.w3.org/2000/svg}path"):
                path_id = path.get("id")
                if path_id:
                    phonetic_paths.add(path_id)
            if phonetic_paths:
                return phonetic_paths

    # Strategy 2: check kvg:phon attribute
    for g in svg_root.iter("{http://www.w3.org/2000/svg}g"):
        phon_attr = g.get(f"{{{KVG_NS}}}phon")
        if phon_attr:
            for path in g.iter("{http://www.w3.org/2000/svg}path"):
                path_id = path.get("id")
                if path_id:
                    phonetic_paths.add(path_id)
            if phonetic_paths:
                return phonetic_paths

    return phonetic_paths


def colorize_svg(svg_path, phonetic_char=None, radical_char=None):
    """Parse a KanjiVG SVG and colorize strokes by component role.

    Returns the modified SVG string.
    """
    parser = etree.XMLParser(remove_blank_text=True)
    tree = etree.parse(str(svg_path), parser)
    root = tree.getroot()

    radical_paths = find_radical_paths(root, radical_char)
    phonetic_paths = find_phonetic_paths(root, phonetic_char) if phonetic_char else set()

    # If a path is in both radical and phonetic, phonetic wins (more informative)
    for path in root.iter("{http://www.w3.org/2000/svg}path"):
        path_id = path.get("id")
        if path_id in phonetic_paths:
            path.set("style", f"stroke:{COLOR_PHONETIC};stroke-width:3")
        elif path_id in radical_paths:
            path.set("style", f"stroke:{COLOR_RADICAL};stroke-width:3")
        else:
            path.set("style", f"stroke:{COLOR_DEFAULT};stroke-width:3")

    # Remove the stroke numbers group to keep SVG clean
    svg_ns = "http://www.w3.org/2000/svg"
    for g in root.findall(f"{{{svg_ns}}}g"):
        gid = g.get("id", "")
        if "StrokeNumbers" in gid:
            root.remove(g)

    return etree.tostring(root, encoding="unicode", pretty_print=False)


def build_site(kanji_db, kanji_to_phonetic, phonetic_info, kanji_to_components):
    """Generate all static site data files."""
    print("Building site data...")

    SITE_DIR.mkdir(exist_ok=True)
    SITE_DATA_DIR.mkdir(exist_ok=True)
    KANJI_OUT_DIR.mkdir(exist_ok=True)

    kanjivg_dir = DATA_DIR / "kanjivg" / "kanji"

    # Build reverse lookups
    # radical_number -> list of kanji chars
    by_radical = {}
    # phonetic component -> list of kanji chars
    by_phonetic = {}
    for comp, info in phonetic_info.items():
        by_phonetic[comp] = info["kanji"]

    search_index = []
    processed = 0
    skipped = 0

    for char, info in kanji_db.items():
        codepoint = f"{ord(char):05x}"
        svg_path = kanjivg_dir / f"{codepoint}.svg"

        if not svg_path.exists():
            skipped += 1
            continue

        # Radical info
        rad_num = info.get("radical_number")
        rad_info = None
        rad_char = None
        if rad_num and rad_num in KANGXI_RADICALS:
            rad_char, rad_name = KANGXI_RADICALS[rad_num]
            rad_info = {"number": rad_num, "char": rad_char, "name": rad_name}

        # Colorize SVG
        phonetic_char = kanji_to_phonetic.get(char)
        svg_str = colorize_svg(svg_path, phonetic_char, rad_char)

        # Phonetic info
        phon_info = None
        if phonetic_char and phonetic_char in phonetic_info:
            pi = phonetic_info[phonetic_char]
            phon_info = {
                "char": phonetic_char,
                "reading": pi["reading"],
                "name": pi["name"],
            }

        # Related kanji
        related_phonetic = []
        if phonetic_char and phonetic_char in by_phonetic:
            related_phonetic = [k for k in by_phonetic[phonetic_char] if k != char]

        # Track by radical
        if rad_num:
            by_radical.setdefault(rad_num, []).append(char)

        # Components from KRADFILE
        components = kanji_to_components.get(char, [])

        kanji_entry = {
            "character": char,
            "meanings": info["meanings"],
            "on": info["on"],
            "kun": info["kun"],
            "strokes": info["strokes"],
            "grade": info["grade"],
            "jlpt": info["jlpt"],
            "freq": info["freq"],
            "radical": rad_info,
            "phonetic": phon_info,
            "components": components,
            "related_phonetic": related_phonetic,
            "svg": svg_str,
        }

        # Write per-kanji JSON
        out_path = KANJI_OUT_DIR / f"{codepoint}.json"
        out_path.write_text(json.dumps(kanji_entry, ensure_ascii=False), encoding="utf-8")

        # Add to search index (compact)
        search_index.append({
            "c": char,
            "cp": codepoint,
            "m": ", ".join(info["meanings"][:3]),
            "on": ", ".join(info["on"][:3]),
            "kun": ", ".join(info["kun"][:2]),
            "g": info["grade"],
            "j": info["jlpt"],
            "f": info["freq"],
            "r": rad_num,
            "p": phonetic_char,
        })

        processed += 1

    # Write search index
    index_path = SITE_DATA_DIR / "search-index.json"
    index_path.write_text(json.dumps(search_index, ensure_ascii=False), encoding="utf-8")

    # Write phonetic components list (for browse-by-phonetic)
    phonetics_list = []
    for comp, info in phonetic_info.items():
        phonetics_list.append({
            "char": comp,
            "reading": info["reading"],
            "name": info["name"],
            "type": info["type"],
            "count": len(info["kanji"]),
        })
    phonetics_path = SITE_DATA_DIR / "phonetics.json"
    phonetics_path.write_text(json.dumps(phonetics_list, ensure_ascii=False), encoding="utf-8")

    # Write radicals list (for browse-by-radical)
    radicals_list = []
    for num, (char, name) in sorted(KANGXI_RADICALS.items()):
        count = len(by_radical.get(num, []))
        if count > 0:
            radicals_list.append({"n": num, "c": char, "name": name, "count": count})
    radicals_path = SITE_DATA_DIR / "radicals.json"
    radicals_path.write_text(json.dumps(radicals_list, ensure_ascii=False), encoding="utf-8")

    print(f"  Processed {processed} kanji, skipped {skipped}.")
    print(f"  Search index: {index_path} ({index_path.stat().st_size / 1024:.0f} KB)")


def main():
    download_data()
    kanji_db = parse_kanjidic2()
    kanji_to_phonetic, phonetic_info = parse_phonetics()
    kanji_to_components = parse_kradfile()
    expand_phonetics(kanji_db, kanji_to_phonetic, phonetic_info)
    build_site(kanji_db, kanji_to_phonetic, phonetic_info, kanji_to_components)
    print("Done! Run: cd site && python -m http.server 8000")


if __name__ == "__main__":
    main()
