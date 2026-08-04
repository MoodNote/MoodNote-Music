# -*- coding: utf-8 -*-
# Job: Stream 3 HuggingFace datasets, lọc theo allowlist nghệ sĩ (vn_artists.json +
# intl_artists.json) NGAY khi đọc từng dòng, normalize schema, dedup, merge → music_filtered.csv
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import re, json
import pandas as pd
from typing import cast
from datasets import load_dataset, IterableDataset

SCHEMA = [
    "track_id", "track_name", "artists", "album_name",
    "popularity", "explicit", "duration_ms",
    "danceability", "energy", "key", "loudness",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo",
    "lyrics",
]

def pad_schema(df: pd.DataFrame) -> pd.DataFrame:
    for col in SCHEMA:
        if col not in df.columns:
            df[col] = None
    return df[SCHEMA].copy()

# ── Allowlist nghệ sĩ (dùng để lọc từng dòng ngay lúc stream, tránh tải hết dataset) ──
def split_artists(s: str) -> list[str]:
    return [a.strip() for a in re.split(r"[,;]", str(s)) if a.strip()]

with open("vn_artists.json", encoding="utf-8") as f:
    target: set[str] = set(json.load(f))
with open("intl_artists.json", encoding="utf-8") as f:
    target.update(json.load(f))
print(f"Target artists: {len(target)}")

def has_target(artist_str: str) -> bool:
    return any(a in target for a in split_artists(str(artist_str)))

def stream_filtered_rows(dataset_name: str, artist_col: str) -> list[dict]:
    stream = cast(IterableDataset, load_dataset(dataset_name, streaming=True)["train"])
    filtered = stream.filter(lambda ex: has_target(ex.get(artist_col, "")))
    return list(filtered)

# ── Nguồn 1: VictorHu0602/spotifymusic_73countries ───────────────────────────
print("[1/3] VictorHu0602/spotifymusic_73countries ...")
rows1 = stream_filtered_rows("VictorHu0602/spotifymusic_73countries", "artists")
ds1 = pd.DataFrame(rows1)
print(f"  Sau filter allowlist: {len(ds1)}")

ds1 = ds1.sort_values("popularity", ascending=False).drop_duplicates("spotify_id")
ds1 = ds1.rename(columns={"spotify_id": "track_id", "name": "track_name", "is_explicit": "explicit"})
df1 = pad_schema(ds1)
print(f"  Sau dedup: {len(df1)}")

# ── Nguồn 2: noelmurti/spotify_data ──────────────────────────────────────────
print("\n[2/3] noelmurti/spotify_data ...")
rows2 = stream_filtered_rows("noelmurti/spotify_data", "Artist(s)")
ds2 = pd.DataFrame(rows2)
print(f"  Sau filter allowlist: {len(ds2)}")

def parse_duration(s: str):
    try:
        parts: list[str] = str(s).split(":")
        if len(parts) == 2:
            return (int(parts[0]) * 60 + int(parts[1])) * 1000
        if len(parts) == 3:
            return (int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])) * 1000
    except Exception:
        pass
    return None

ds2 = ds2.rename(columns={
    "Artist(s)": "artists", "song": "track_name", "text": "lyrics",
    "Album": "album_name", "Popularity": "popularity", "Explicit": "explicit",
    "Key": "key", "Tempo": "tempo", "Loudness (db)": "loudness",
    "Energy": "energy", "Danceability": "danceability", "Positiveness": "valence",
    "Speechiness": "speechiness", "Liveness": "liveness",
    "Acousticness": "acousticness", "Instrumentalness": "instrumentalness",
})
ds2["track_id"]    = None
ds2["duration_ms"] = ds2["Length"].apply(parse_duration) if "Length" in ds2.columns else None
ds2 = ds2.drop_duplicates(["track_name", "artists"])
df2 = pad_schema(ds2)
print(f"  Sau dedup: {len(df2)}")

# ── Nguồn 3: abhiramag/spotify-data-960k ─────────────────────────────────────
print("\n[3/3] abhiramag/spotify-data-960k ...")
rows3 = stream_filtered_rows("abhiramag/spotify-data-960k", "artists")
ds3 = pd.DataFrame(rows3)
print(f"  Sau filter allowlist: {len(ds3)}")

ds3 = ds3.rename(columns={"name": "track_name"})
ds3["track_id"]    = None
ds3["explicit"]    = None
ds3["popularity"]  = None
ds3["duration_ms"] = pd.to_numeric(ds3["duration"], errors="coerce") * 1000 if "duration" in ds3.columns else None
ds3 = ds3.drop_duplicates(["track_name", "artists"])
df3 = pad_schema(ds3)
print(f"  Sau dedup: {len(df3)}")

# ── Merge: nguồn 1 ưu tiên (có track_id), rồi 2, rồi 3 ──────────────────────
print("\nMerge ...")
merged = pd.concat([df1, df2, df3], ignore_index=True)

with_id    = merged[merged["track_id"].notna()].drop_duplicates("track_id")
without_id = merged[merged["track_id"].isna()]

used_keys = set(zip(with_id["track_name"].str.lower().fillna(""),
                    with_id["artists"].str.lower().fillna("")))
without_id = without_id[
    ~without_id.apply(lambda r: (str(r["track_name"]).lower(),
                                  str(r["artists"]).lower()) in used_keys, axis=1)
]

final = pd.concat([with_id, without_id], ignore_index=True)
final = final.drop_duplicates(["track_name", "artists"])

print(f"\nKết quả:")
print(f"  Nguồn 1: {len(df1)}  |  Nguồn 2: {len(df2)}  |  Nguồn 3: {len(df3)}")
print(f"  Sau merge & dedup: {len(final)}")
print(f"  Có lyrics: {final['lyrics'].notna().sum()}")

assert list(final.columns) == SCHEMA
assert len(final) > 0
assert final["track_id"].notna().sum() > 0
assert final.loc[final["track_id"].notna(), "track_id"].is_unique
assert final["artists"].apply(has_target).all()

final.to_csv("music_filtered.csv", index=False, encoding="utf-8-sig")
print(f"\nĐã lưu music_filtered.csv ({len(final)} tracks)")
