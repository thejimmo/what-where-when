"""Refresh data/videos.json from the channel's public YouTube RSS feed.

The feed lists the 15 most recent uploads. Shorts are told apart from
long-form videos by their link, which points at /shorts/<id>.
"""
import json
import pathlib
import urllib.request
import xml.etree.ElementTree as ET

CHANNEL_ID = "UCnoH33xbDq0mzT_issIqlAA"
FEED = f"https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "videos.json"
NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}


def main():
    req = urllib.request.Request(FEED, headers={"User-Agent": "whatwherewhen.store video refresh"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())

    longform, shorts = [], []
    for entry in root.findall("a:entry", NS):
        video = {
            "id": entry.findtext("yt:videoId", namespaces=NS),
            "title": entry.findtext("a:title", namespaces=NS),
            "published": entry.findtext("a:published", namespaces=NS),
        }
        link = entry.find("a:link[@rel='alternate']", NS)
        href = link.get("href", "") if link is not None else ""
        (shorts if "/shorts/" in href else longform).append(video)

    newest_first = lambda v: v["published"]
    data = {
        "longform": sorted(longform, key=newest_first, reverse=True),
        "shorts": sorted(shorts, key=newest_first, reverse=True),
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"{len(data['longform'])} long-form, {len(data['shorts'])} shorts")


if __name__ == "__main__":
    main()
