import re
import urllib.request
import urllib.parse
import webbrowser
import logging
import pyautogui

logger = logging.getLogger("MJ.BrowserControl")

class BrowserController:
    def __init__(self):
        pass

    def google_search(self, query: str) -> str:
        """Search anything on Google"""
        clean_query = query.strip()
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://www.google.com/search?q={encoded}"
        webbrowser.open(url)
        return f"Google par '{clean_query}' search kar diya hai."

    def youtube_play(self, query: str) -> str:
        """Directly plays the top video on YouTube without stopping at search results"""
        clean_query = query.strip()
        encoded = urllib.parse.quote_plus(clean_query)
        search_url = f"https://www.youtube.com/results?search_query={encoded}"

        # Attempt to scrape top video ID for true instant autoplay
        try:
            req = urllib.request.Request(
                search_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                html = resp.read().decode("utf-8", errors="ignore")

            video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
            if video_ids:
                top_video_id = video_ids[0]
                play_url = f"https://www.youtube.com/watch?v={top_video_id}&autoplay=1"
                logger.info(f"Direct YouTube autoplay resolved: {play_url}")
                webbrowser.open(play_url)
                return f"YouTube par '{clean_query}' play kar diya hai."
        except Exception as e:
            logger.warning(f"Could not resolve direct video ID: {e}, falling back to search page.")

        # Fallback to search results
        webbrowser.open(search_url)
        return f"YouTube par '{clean_query}' search kar diya hai."

    def youtube_search(self, query: str) -> str:
        """Search videos on YouTube"""
        clean_query = query.strip()
        encoded = urllib.parse.quote_plus(clean_query)
        url = f"https://www.youtube.com/results?search_query={encoded}"
        webbrowser.open(url)
        return f"YouTube par '{clean_query}' open kar diya hai."

    def open_url(self, url: str) -> str:
        """Open any website directly"""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        webbrowser.open(url)
        return f"Website open kar di hai: {url}"

    # Media Playback Controls
    def media_play_pause(self) -> str:
        pyautogui.press("playpause")
        return "Media play/pause kar diya hai."

    def media_next(self) -> str:
        pyautogui.press("nexttrack")
        return "Next track chala diya hai."

    def media_previous(self) -> str:
        pyautogui.press("prevtrack")
        return "Previous track chala diya hai."

# Global instance
browser_control = BrowserController()
