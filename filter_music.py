# -*- coding: utf-8 -*-
# Job: Filter music.csv theo vn_artists.json + intl_artists.json → vn_music.csv
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re, json
import pandas as pd

def split_artists(s: str) -> list[str]:
    return [a.strip() for a in re.split(r"[,;]", str(s)) if a.strip()]

# Load danh sách nghệ sĩ mục tiêu
with open("vn_artists.json", encoding="utf-8") as f:
    target: set[str] = set(json.load(f))
with open("intl_artists.json", encoding="utf-8") as f:
    target.update(json.load(f))
print(f"Target artists: {len(target)}")

# Load raw data
df = pd.read_csv("music.csv")
print(f"music.csv: {len(df)} tracks")

# Filter
def has_target(artist_str: str) -> bool:
    return any(a in target for a in split_artists(str(artist_str)))

filtered = df[df["artists"].apply(has_target)].copy()
print(f"Sau filter: {len(filtered)} tracks")
print(f"Có lyrics: {filtered["lyrics"].notna().sum()}")

filtered.to_csv("music.csv", index=False, encoding="utf-8-sig")
print(f"Đã lưu music.csv ({len(filtered)} tracks)")
