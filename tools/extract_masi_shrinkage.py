#!/usr/bin/env python3
"""临时工具2：提取 Masi 2018 Table 2（裂缝纬度 vs εv/α 五档）与 57° 原始表述。"""
import re
from pathlib import Path

PDF = Path(__file__).resolve().parents[1] / "docs" / "references" / "Masi_2018_cracks_Pantheon.pdf"
from pypdf import PdfReader
r = PdfReader(str(PDF))
pages = [p.extract_text() or "" for p in r.pages]

print("===== 搜索 57 / 58 / 59（裂缝纬度数值） =====")
for pi, t in enumerate(pages):
    for m in re.finditer(r"5[0-9]\s*°|[0-9]{2}\s*°", t):
        i = m.start()
        seg = t[max(0, i - 200):i + 250].replace("\n", " ")
        print(f"[p{pi + 1}] ...{seg}...")
        print("---")

print("\n===== 搜索 Table 2 / springing / latitude / θmax 上下文 =====")
for pi, t in enumerate(pages):
    if re.search(r"Table 2|springing|latitude", t, re.I):
        print(f"\n########## PAGE {pi + 1} 全文 ##########")
        print(t)
