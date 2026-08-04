# -*- coding: utf-8 -*-
# Job: Rename camelCase, ép dtype đúng, dedup, chọn cột, xuất music.csv/json/parquet
# Input:  music_enriched.csv
# Output: music.csv, music.json, music.parquet

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd

df = pd.read_csv("music_enriched.csv")
print(f"Rows ban đầu: {len(df)}")

# Rename cột về camelCase
RENAME = {
    "track_id":    "trackId",
    "track_name":  "trackName",
    "album_name":  "albumName",
    "explicit":    "isExplicit",
    "duration_ms": "durationMs",
    "track_genre": "trackGenre",
}
df = df.rename(columns=RENAME)

# Deduplicate: cùng tên + artist
df = df.drop_duplicates(subset=["trackName", "artists"])
print(f"Sau dedup name+artists: {len(df)}")

# ── Ép dtype ───────────────────────────────────────────────────────────────
_TRUE  = {True, "True", "true", "1", 1}
_FALSE = {False, "False", "false", "0", 0}

def to_bool(v: object) -> bool | pd.NA:
    if v in _TRUE:
        return True
    if v in _FALSE:
        return False
    return pd.NA

df["isExplicit"] = df["isExplicit"].apply(to_bool).astype("boolean")

for col in ("popularity", "durationMs", "key"):
    df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

AUDIO_FEATURES = [
    "danceability", "energy", "loudness", "speechiness",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
]
for col in AUDIO_FEATURES:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Chỉ giữ các fields cần thiết
KEEP = [
    "trackId", "trackName", "artists",
    "popularity", "isExplicit", "durationMs",
    "danceability", "energy", "key", "loudness",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo", "trackGenre",
]
KEEP = [c for c in KEEP if c in df.columns]
df = df[KEEP].reset_index(drop=True)

assert not any(c.startswith("mood_") for c in df.columns)
assert df["isExplicit"].dtype.name == "boolean"
assert not df.duplicated(subset=["trackName", "artists"]).any()

# Lưu 3 formats
df.to_csv("music.csv", index=False, encoding="utf-8-sig")
df.to_parquet("music.parquet", index=False)
df.to_json("music.json", orient="records", force_ascii=False, indent=2)

print(f"\nDone! {len(df)} unique tracks")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
