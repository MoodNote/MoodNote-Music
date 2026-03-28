# MoodNote Music Dataset

Bộ dataset nhạc dành cho ứng dụng MoodNote, tổng hợp từ nhiều nguồn Spotify, tập trung vào các nghệ sĩ phổ biến tại Việt Nam (nhạc Việt, K-pop, J-pop, Âu Mỹ...).

## Pipeline

```
download_music.py  →  filter_music.py  →  clean_music.py
                          ↓
                       music.csv / music.json / music.parquet
```

| Bước | File | Input | Output |
|------|------|-------|--------|
| 1 | `download_music.py` | HuggingFace (3 datasets) | `music.csv` (raw, snake_case) |
| 2 | `filter_music.py` | `music.csv` + artist lists | `music.csv` (filtered) |
| 3 | `clean_music.py` | `music.csv` | `music.csv` / `music.json` / `music.parquet` |

### Chạy

```bash
python download_music.py
python filter_music.py
python clean_music.py
```

## Nguồn dữ liệu

| Dataset | Đặc điểm |
|---------|----------|
| [VictorHu0602/spotifymusic_73countries](https://huggingface.co/datasets/VictorHu0602/spotifymusic_73countries) | 1.7M rows, 73 quốc gia, có Spotify ID + audio features |
| [noelmurti/spotify_data](https://huggingface.co/datasets/noelmurti/spotify_data) | Có lyrics |
| [abhiramag/spotify-data-960k](https://huggingface.co/datasets/abhiramag/spotify-data-960k) | 960k tracks, có lyrics |

Merge theo thứ tự ưu tiên: VictorHu0602 (có `trackId`) → noelmurti → abhiramag.

## Danh sách nghệ sĩ

| File | Nội dung |
|------|----------|
| `vn_artists.json` | Nghệ sĩ Việt Nam |
| `intl_artists.json` | Nghệ sĩ quốc tế phổ biến tại VN (K-pop, J-pop, Âu Mỹ...) |

Thêm/bớt nghệ sĩ trực tiếp trong 2 file JSON, không cần sửa code.

## Schema output

| Cột | Kiểu | Mô tả |
|-----|------|-------|
| `trackId` | string | Spotify ID |
| `trackName` | string | Tên bài hát |
| `artists` | string | Nghệ sĩ (phân cách bởi `, `) |
| `albumName` | string | Tên album |
| `popularity` | int | Độ phổ biến Spotify (0–100) |
| `isExplicit` | bool | Nội dung 18+ |
| `durationMs` | int | Thời lượng (ms) |
| `danceability` | float | |
| `energy` | float | |
| `key` | int/string | Tông nhạc |
| `loudness` | float | dB |
| `speechiness` | float | |
| `acousticness` | float | |
| `instrumentalness` | float | |
| `liveness` | float | |
| `valence` | float | Cảm xúc tích cực (0–1) |
| `tempo` | float | BPM |
| `lyrics` | string | Lời bài hát (nullable) |
