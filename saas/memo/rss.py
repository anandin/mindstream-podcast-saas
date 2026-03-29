"""RSS feed generator for Memo.fm private feeds."""
import calendar
from email.utils import formatdate


def generate_rss(podcast, episodes, token: str) -> str:
    """Build a valid podcast RSS feed XML string."""
    base_url = "https://memo.fm"
    feed_url = f"{base_url}/api/v1/memo/feed/{token}"

    items = ""
    for ep in episodes:
        pub_date = formatdate(calendar.timegm(ep.date.timetuple()))
        audio_url = ep.audio_url or ""
        size = int((ep.audio_duration_seconds or 0) * 16000)  # rough byte estimate
        items += f"""
    <item>
      <title>{_esc(ep.title or 'Untitled')}</title>
      <description>{_esc(ep.description or '')}</description>
      <pubDate>{pub_date}</pubDate>
      <guid isPermaLink="false">{ep.id}</guid>
      <enclosure url="{audio_url}" length="{size}" type="audio/mpeg"/>
      <itunes:duration>{int(ep.audio_duration_seconds or 0)}</itunes:duration>
    </item>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"
  xmlns:itunes="http://www.itunes.com/dtds/podcast-1.0.dtd"
  xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>{_esc(podcast.title)}</title>
    <description>{_esc(podcast.description or '')}</description>
    <link>{feed_url}</link>
    <language>en</language>
    <itunes:author>{_esc(podcast.host_1_name or '')}</itunes:author>
    {items}
  </channel>
</rss>"""


def _esc(s: str) -> str:
    """Escape XML special characters."""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
