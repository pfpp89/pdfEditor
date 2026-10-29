"""Generate the app icon files from the SVG below (run from the project root).

Writes static/icon.svg (browser favicon), static/icon.png (Linux shortcut) and
static/icon.ico (Windows shortcut). Uses only PyMuPDF, already a dependency.
"""

import struct
from pathlib import Path

import pymupdf

SVG = """<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect x="70" y="12" width="150" height="196" rx="16" fill="#9ec0f5"/>
  <path d="M52 40h100l48 48v138a16 16 0 0 1-16 16H52a16 16 0 0 1-16-16V56a16 16 0 0 1 16-16z"
        fill="#ffffff" stroke="#2f6fde" stroke-width="8" stroke-linejoin="round"/>
  <path d="M152 40v32a16 16 0 0 0 16 16h32" fill="#dbe7fb" stroke="#2f6fde" stroke-width="8"
        stroke-linejoin="round"/>
  <path d="M64 92h64M64 206h112" stroke="#9aa5b1" stroke-width="9" stroke-linecap="round"/>
  <rect x="16" y="118" width="164" height="68" rx="12" fill="#d32f2f"/>
  <path d="M40 172v-40h14a12 12 0 0 1 0 24h-14" fill="none" stroke="#fff" stroke-width="9"
        stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M84 132v40h8a20 20 0 0 0 0-40z" fill="none" stroke="#fff" stroke-width="9"
        stroke-linejoin="round"/>
  <path d="M132 172v-40h24M132 152h18" fill="none" stroke="#fff" stroke-width="9"
        stroke-linecap="round" stroke-linejoin="round"/>
</svg>
"""

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_png(size):
    doc = pymupdf.open(stream=SVG.encode(), filetype="svg")
    page = doc[0]
    zoom = size / page.rect.width
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=True)
    data = pix.tobytes("png")
    doc.close()
    return data


def write_ico(path, images):
    """ICO container with PNG-compressed entries (supported since Windows Vista)."""
    header = struct.pack("<HHH", 0, 1, len(images))
    entries, blobs = b"", b""
    offset = len(header) + 16 * len(images)
    for size, png in images:
        dim = 0 if size >= 256 else size  # 0 means 256 in the ICO format
        entries += struct.pack("<BBBBHHII", dim, dim, 0, 0, 1, 32, len(png), offset)
        blobs += png
        offset += len(png)
    path.write_bytes(header + entries + blobs)


def main():
    static = Path(__file__).resolve().parent.parent / "static"
    (static / "icon.svg").write_text(SVG, encoding="utf-8")
    (static / "icon.png").write_bytes(render_png(256))
    write_ico(static / "icon.ico", [(s, render_png(s)) for s in ICO_SIZES])
    print("Wrote icon.svg, icon.png, icon.ico in", static)


if __name__ == "__main__":
    main()
