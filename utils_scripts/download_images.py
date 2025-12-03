"""
download_large_commons_images.py

Downloads images >= MIN_BYTES from Wikimedia Commons (no API key).
Requires: requests

Usage:
    python download_large_commons_images.py
"""

import os
import time
import requests
from urllib.parse import quote_plus

# Config
QUERIES = [
    "dogs",
    "elephants",
    "lions",
    "tigers",
    "cats",
]  # change or add queries you want
MIN_BYTES = 20 * 1024 * 1024  # 20 MB
DOWNLOAD_DIR = "/Users/ns632@apac.comcast.com/Documents/v0_photo_proof/commons_large_images"
SLEEP_BETWEEN_REQUESTS = 0.5  # polite throttle
MAX_RESULTS_PER_QUERY = 50  # how many files to check per query (search results)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "LargeImageDownloader/1.0 (your-email@example.com)"})

WIKI_API = "https://commons.wikimedia.org/w/api.php"


def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def search_files_for_query(query, limit=50):
    """
    Search namespace 6 (File:) for the query.
    Returns list of file titles like 'File:Example.jpg'
    """
    titles = []
    sparams = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": query,
        "srnamespace": 6,  # File namespace
        "srlimit": limit,
    }
    r = SESSION.get(WIKI_API, params=sparams)
    r.raise_for_status()
    j = r.json()
    for item in j.get("query", {}).get("search", []):
        titles.append(item.get("title"))
    return titles


def get_imageinfo_for_titles(titles):
    """
    Given a list of File: titles, return imageinfo for each.
    Will batch them (max 50 titles per request).
    Returns dict: title -> imageinfo dict (contains url, size, mime)
    """
    out = {}
    maxbatch = 50
    for i in range(0, len(titles), maxbatch):
        batch = titles[i : i + maxbatch]
        params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|sha1",
            "titles": "|".join(batch),
        }
        r = SESSION.get(WIKI_API, params=params)
        r.raise_for_status()
        j = r.json()
        pages = j.get("query", {}).get("pages", {})
        for pid, p in pages.items():
            title = p.get("title")
            ii = p.get("imageinfo")
            if ii and isinstance(ii, list):
                out[title] = ii[0]
        time.sleep(SLEEP_BETWEEN_REQUESTS)
    return out


def head_check(url):
    """Try to get Content-Length via HEAD (not always available)."""
    try:
        r = SESSION.head(url, allow_redirects=True, timeout=20)
        if r.status_code == 200:
            cl = r.headers.get("Content-Length")
            if cl:
                return int(cl)
    except Exception:
        pass
    return None


def download_file(url, dest_path):
    """Stream download and return number of bytes written."""
    with SESSION.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = 0
        with open(dest_path, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    total += len(chunk)
    return total


def safe_filename_from_title(title):
    # title is like 'File:Example.jpg' -> convert to 'Example.jpg'
    if title.startswith("File:"):
        name = title.split("File:", 1)[1]
    else:
        name = title
    # sanitize
    return "".join(c for c in name if c not in r'\/:*?"<>|').strip()


def main():
    ensure_dir(DOWNLOAD_DIR)
    found_any = False

    for q in QUERIES:
        print(f"\nSearching Wikimedia Commons for files matching: '{q}'")
        try:
            titles = search_files_for_query(q, limit=MAX_RESULTS_PER_QUERY)
        except Exception as e:
            print("Search failed:", e)
            continue

        if not titles:
            print("No files found for query:", q)
            continue

        print(f"Found {len(titles)} candidate files; fetching metadata...")
        try:
            info_map = get_imageinfo_for_titles(titles)
        except Exception as e:
            print("Failed to get imageinfo:", e)
            continue

        # filter and download
        for title, info in info_map.items():
            url = info.get("url")
            size = info.get("size")  # size provided by API in bytes
            mime = info.get("mime")
            nice_name = safe_filename_from_title(title)
            dest = os.path.join(DOWNLOAD_DIR, nice_name)

            # prefer API-reported size if available
            reported_size = int(size) if size is not None else None

            if reported_size is not None and reported_size < MIN_BYTES:
                # skip small files
                continue

            # If no reported size, try HEAD
            if reported_size is None:
                head_size = head_check(url)
                if head_size is not None and head_size < MIN_BYTES:
                    continue

            # Final decision: proceed to download
            print(f"Downloading: {title} ({mime}) -> {nice_name}")
            try:
                print(dest)
                bytes_written = download_file(url, dest)
                
                print(f"  downloaded {bytes_written / (1024*1024):.2f} MB")
                # double-check size
                if bytes_written < MIN_BYTES:
                    print("  file smaller than threshold; deleting")
                    os.remove(dest)
                else:
                    print("  kept file.")
                    found_any = True
            except Exception as e:
                print("  download failed:", e)

            time.sleep(SLEEP_BETWEEN_REQUESTS)

    if not found_any:
        print("\nNo images >= threshold were downloaded. Try adding other queries such as 'TIFF', 'high_resolution', 'satellite', or increasing MAX_RESULTS_PER_QUERY.")
    else:
        print("\nDone. Check the folder:", os.path.abspath(DOWNLOAD_DIR))


if __name__ == "__main__":
    main()
