"""Refresh data/videos.json with the channel's latest long-form videos and Shorts.

YouTube keeps two automatic playlists per channel: UULF<id> (long-form uploads)
and UUSH<id> (Shorts). With a YOUTUBE_API_KEY the script reads them through the
YouTube Data API; without one it falls back to their public RSS feeds, and then
to the channel feed, where Shorts are the entries linking to /shorts/<id>.
"""
import json
import os
import pathlib
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = "UCnoH33xbDq0mzT_issIqlAA"
SUFFIX = CHANNEL_ID[2:]
LONGFORM_LIST, SHORTS_LIST = "UULF" + SUFFIX, "UUSH" + SUFFIX
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "videos.json"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (whatwherewhen.store video refresh)"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def from_api(key):
    def playlist(list_id):
        query = urllib.parse.urlencode({"part": "snippet", "playlistId": list_id, "maxResults": 20, "key": key})
        try:
            items = json.loads(get("https://www.googleapis.com/youtube/v3/playlistItems?" + query))["items"]
        except urllib.error.HTTPError as err:
            if err.code == 404:  # YouTube has not created the playlist yet: no videos of this kind
                return None
            raise
        return [
            {"id": s["resourceId"]["videoId"], "title": s["title"], "published": s["publishedAt"]}
            for s in (item["snippet"] for item in items)
            if s["title"] not in ("Private video", "Deleted video")
        ]
    longform, shorts = playlist(LONGFORM_LIST), playlist(SHORTS_LIST)
    if longform is None and shorts is None:
        raise ValueError("neither playlist found")
    return longform or [], shorts or []


def feed(query):
    root = ET.fromstring(get("https://www.youtube.com/feeds/videos.xml?" + query))
    for entry in root.findall("a:entry", NS):
        link = entry.find("a:link[@rel='alternate']", NS)
        yield {
            "id": entry.findtext("yt:videoId", namespaces=NS),
            "title": entry.findtext("a:title", namespaces=NS),
            "published": entry.findtext("a:published", namespaces=NS),
        }, (link.get("href", "") if link is not None else "")


def from_playlist_feeds():
    return ([v for v, _ in feed("playlist_id=" + LONGFORM_LIST)],
            [v for v, _ in feed("playlist_id=" + SHORTS_LIST)])


def from_channel_feed():
    longform, shorts = [], []
    for video, href in feed("channel_id=" + CHANNEL_ID):
        (shorts if "/shorts/" in href else longform).append(video)
    return longform, shorts


def main():
    key = os.environ.get("YOUTUBE_API_KEY")
    sources = [("YouTube Data API", lambda: from_api(key))] if key else []
    sources += [("playlist feeds", from_playlist_feeds), ("channel feed", from_channel_feed)]

    for name, fetch in sources:
        try:
            longform, shorts = fetch()
            break
        except (urllib.error.URLError, ET.ParseError, KeyError, ValueError) as err:
            print(f"{name} failed: {err}", file=sys.stderr)
    else:
        sys.exit("Every source failed; leaving data/videos.json unchanged.")

    newest_first = lambda v: v["published"]
    data = {
        "longform": sorted(longform, key=newest_first, reverse=True),
        "shorts": sorted(shorts, key=newest_first, reverse=True),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"From {name}: {len(data['longform'])} long-form, {len(data['shorts'])} shorts")


if __name__ == "__main__":
    main()
