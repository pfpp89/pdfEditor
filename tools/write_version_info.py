"""Write the Windows version resource for PdfEditor.exe (used by build_exe.ps1).

Shown in the file's Properties > Details. The version comes from pdf_editor.__version__.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pdf_editor import __version__  # noqa: E402

TEMPLATE = """# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(filevers={nums}, prodvers={nums}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'PDF Editor'),
      StringStruct('FileDescription', 'PDF Editor - open, reorder and delete PDF pages'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'PdfEditor'),
      StringStruct('OriginalFilename', 'PdfEditor.exe'),
      StringStruct('ProductName', 'PDF Editor'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(out):
    parts = [int(p) for p in __version__.split(".")][:4]
    nums = tuple(parts + [0] * (4 - len(parts)))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(TEMPLATE.format(nums=nums, version=__version__), encoding="utf-8")
    print(f"Version {__version__} -> {out}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "build/version_info.txt")
