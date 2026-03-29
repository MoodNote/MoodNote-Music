# -*- coding: utf-8 -*-
# Job: Enrich music.csv với genre data từ maharshipandya/spotify-tracks-dataset
# Chạy SAU filter_music.py, TRƯỚC clean_music.py
# Input:  music.csv (snake_case columns, không có track_genre)
# Output: music.csv (+ cột track_genre, pipe-separated genres)

import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import pandas as pd
from typing import cast
from datasets import load_dataset, Dataset

HF_DATASET = "maharshipandya/spotify-tracks-dataset"
GENRE_SEP  = "|"  # separator cho nhiều genre trong cùng 1 track


# ── Helpers normalize ─────────────────────────────────────────────────────────

def normalize_name(s: str) -> str:
    return str(s).lower().strip()

def normalize_artists_full(s: str) -> str:
    """Split theo ',' hoặc ';', lowercase, sort, rejoin '|'.
    Ví dụ: 'Lady Gaga, Bruno Mars' == 'Bruno Mars;Lady Gaga' → 'bruno mars|lady gaga'
    """
    parts = sorted([a.strip().lower() for a in re.split(r"[,;]", str(s)) if a.strip()])
    return "|".join(parts)

def first_artist(s: str) -> str:
    parts = [a.strip().lower() for a in re.split(r"[,;]", str(s)) if a.strip()]
    return parts[0] if parts else ""


# ── Bước 1: Load music.csv ────────────────────────────────────────────────────

print("[1/4] Loading music.csv ...")
df = pd.read_csv("music.csv")
print(f"  Rows: {len(df)}")

# Phát hiện style cột (pre-clean: snake_case, post-clean: camelCase)
if "track_id" in df.columns:
    col_id, col_name, col_artists = "track_id", "track_name", "artists"
else:
    col_id, col_name, col_artists = "trackId", "trackName", "artists"

print(f"  Column style: {'snake_case' if col_id == 'track_id' else 'camelCase'}")
print(f"  Tracks có {col_id}: {df[col_id].notna().sum()}")

if "track_genre" in df.columns:
    print("  WARNING: cột 'track_genre' đã tồn tại — sẽ overwrite.")


# ── Bước 2: Load HuggingFace genre source ────────────────────────────────────

print(f"\n[2/4] Loading {HF_DATASET} ...")
src: pd.DataFrame = cast(pd.DataFrame,
    cast(Dataset, load_dataset(HF_DATASET)["train"]).to_pandas())  # type: ignore
print(f"  Rows (multi-genre): {len(src):,}")
print(f"  Unique genres: {src['track_genre'].nunique()}")
print(f"  Unique track_ids: {src['track_id'].nunique():,}")

# Strip prefix 'spotify:track:' nếu có
src["track_id"] = src["track_id"].str.replace("spotify:track:", "", regex=False)


# ── Bước 3: Build lookup tables ───────────────────────────────────────────────

print("\n[3/4] Building genre lookup tables ...")

# Lookup A: track_id → pipe-joined genres
id_to_genres: dict[str, str] = (
    src.groupby("track_id")["track_genre"]
       .apply(lambda g: GENRE_SEP.join(sorted(set(g.dropna()))))
       .to_dict()
)
print(f"  Lookup A (track_id): {len(id_to_genres):,} entries")

# Lookup B: (norm_name, norm_artists_full) → genres
src["_norm_name"]    = src["track_name"].fillna("").apply(normalize_name)
src["_norm_artists"] = src["artists"].fillna("").apply(normalize_artists_full)
name_full_to_genres: dict[tuple[str, str], str] = (
    src.groupby(["_norm_name", "_norm_artists"])["track_genre"]
       .apply(lambda g: GENRE_SEP.join(sorted(set(g.dropna()))))
       .to_dict()
)
print(f"  Lookup B (name + full artists): {len(name_full_to_genres):,} entries")

# Lookup C: (norm_name, first_artist) → genres
src["_first_artist"] = src["artists"].fillna("").apply(first_artist)
name_first_to_genres: dict[tuple[str, str], str] = (
    src.groupby(["_norm_name", "_first_artist"])["track_genre"]
       .apply(lambda g: GENRE_SEP.join(sorted(set(g.dropna()))))
       .to_dict()
)
print(f"  Lookup C (name + first artist): {len(name_first_to_genres):,} entries")


# ── Bước 4: Match genres theo 3 tầng ─────────────────────────────────────────

print("\n[4/4] Matching genres ...")

def lookup_genre(row: pd.Series) -> str | None:
    # Tier 1: exact track_id
    tid = row[col_id]
    if pd.notna(tid) and str(tid).strip():
        genre = id_to_genres.get(str(tid).strip())
        if genre:
            return genre

    # Tier 2: normalized (track_name, full_artists)
    norm_name    = normalize_name(row[col_name])
    norm_artists = normalize_artists_full(row[col_artists])
    genre = name_full_to_genres.get((norm_name, norm_artists))
    if genre:
        return genre

    # Tier 3: normalized (track_name, first_artist)
    norm_first = first_artist(row[col_artists])
    return name_first_to_genres.get((norm_name, norm_first))

df["track_genre"] = df.apply(lookup_genre, axis=1)


# ── Report ────────────────────────────────────────────────────────────────────

total     = len(df)
matched   = df["track_genre"].notna().sum()
unmatched = total - matched

print(f"\n  Kết quả:")
print(f"    Tổng tracks:     {total:,}")
print(f"    Matched:         {matched:,} ({matched/total*100:.1f}%)")
print(f"    Unmatched (NULL):{unmatched:,} ({unmatched/total*100:.1f}%)")

genre_counts: dict[str, int] = {}
for genres_str in df["track_genre"].dropna():
    for g in str(genres_str).split(GENRE_SEP):
        genre_counts[g] = genre_counts.get(g, 0) + 1

top_genres = sorted(genre_counts.items(), key=lambda x: -x[1])[:15]
print("\n  Top 15 genres được assign:")
for g, c in top_genres:
    print(f"    {g}: {c}")

df.to_csv("music.csv", index=False, encoding="utf-8-sig")
print(f"\nĐã lưu music.csv ({len(df)} tracks, cột 'track_genre' đã thêm)")
