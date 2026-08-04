# MoodNote Music Dataset

Bộ dataset nhạc dành cho ứng dụng MoodNote, tổng hợp từ nhiều nguồn Spotify, tập trung vào các nghệ sĩ phổ biến tại Việt Nam (nhạc Việt, K-pop, J-pop, Âu Mỹ...).

## Pipeline

```
download_music.py  →  enrich_genres.py  →  clean_music.py
                                                 ↓
                                music.csv / music.json / music.parquet
```

`download_music.py` stream từng dataset nguồn và lọc theo allowlist nghệ sĩ (`vn_artists.json`/`intl_artists.json`) NGAY khi đọc từng dòng — tránh phải tải nguyên 3 dataset (~2.6M dòng) về máy rồi mới lọc. Mỗi bước ghi ra 1 file checkpoint riêng, không ghi đè lẫn nhau, nên có thể re-run/debug từng bước độc lập.

| Bước | File | Input | Output |
|------|------|-------|--------|
| 1 | `download_music.py` | HuggingFace (3 datasets, streaming) + artist lists | `music_filtered.csv` (snake_case, đã lọc allowlist) |
| 2 | `enrich_genres.py` | `music_filtered.csv` + HuggingFace (genre dataset) | `music_enriched.csv` (+ cột `track_genre`) |
| 3 | `clean_music.py` | `music_enriched.csv` | `music.csv` / `music.json` / `music.parquet` |

Genre match rate hiện ~9% — giới hạn cấu trúc do dataset genre (114k dòng, sample cân bằng 125 genre, thiên nhạc phương Tây) ít overlap với allowlist nghệ sĩ VN/K-pop/quốc tế, không phải bug.

Các file checkpoint (`music_filtered.csv`, `music_enriched.csv`) và output cuối (`music.csv`/`music.json`/`music.parquet`) đều được gitignore — sinh lại được từ pipeline, không commit vào git.

### Chạy

```bash
pip install -r requirements.txt
python download_music.py
python enrich_genres.py
python clean_music.py
```

## Nguồn dữ liệu

| Dataset | Đặc điểm |
|---------|----------|
| [VictorHu0602/spotifymusic_73countries](https://huggingface.co/datasets/VictorHu0602/spotifymusic_73countries) | 1.7M rows, 73 quốc gia, có Spotify ID + audio features |
| [noelmurti/spotify_data](https://huggingface.co/datasets/noelmurti/spotify_data) | Có lyrics |
| [abhiramag/spotify-data-960k](https://huggingface.co/datasets/abhiramag/spotify-data-960k) | 960k tracks, có lyrics |
| [maharshipandya/spotify-tracks-dataset](https://huggingface.co/datasets/maharshipandya/spotify-tracks-dataset) | Dùng ở bước enrich, cung cấp `track_genre` |

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
| `trackId` | string | Spotify ID (nullable) |
| `trackName` | string | Tên bài hát |
| `artists` | string | Nghệ sĩ (phân cách bởi `, `) |
| `popularity` | int | Độ phổ biến Spotify (0–100, nullable) |
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
| `trackGenre` | string | Thể loại, phân cách bởi `\|` khi có nhiều genre (nullable) |
