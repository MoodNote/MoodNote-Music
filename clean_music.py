import pandas as pd

df = pd.read_csv("music.csv")
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

# Deduplicate bước 1: theo spotifyId
if "spotifyId" in df.columns and df["spotifyId"].notna().any():
    df = df.sort_values("popularity", ascending=False).drop_duplicates(subset="spotifyId")
    print(f"Sau dedup spotifyId: {len(df)}")

# Deduplicate bước 2: cùng tên + artist
df = df.drop_duplicates(subset=["trackName", "artists"])
print(f"Sau dedup name+artists: {len(df)}")

# Chỉ giữ các fields cần thiết
KEEP = [
    "trackId", "trackName", "artists", "albumName",
    "popularity", "isExplicit", "durationMs",
    "danceability", "energy", "key", "loudness",
    "speechiness", "acousticness", "instrumentalness",
    "liveness", "valence", "tempo", "trackGenre",
    "lyrics",
    "mood_party", "mood_work", "mood_relax", "mood_exercise",
    "mood_running", "mood_yoga", "mood_driving", "mood_social", "mood_morning",
]
KEEP = [c for c in KEEP if c in df.columns]
df = df[KEEP].reset_index(drop=True)

# Lưu 3 formats
df.to_csv("music.csv", index=False, encoding="utf-8-sig")
df.to_parquet("music.parquet", index=False)
df.to_json("music.json", orient="records", force_ascii=False, indent=2)

print(f"\nDone! {len(df)} unique tracks")
print(f"Columns ({len(df.columns)}): {list(df.columns)}")
