import xbmc
import xbmcaddon
import requests
from bs4 import BeautifulSoup
import json
import re
import time
import urllib2
import base64

ADDON = xbmcaddon.Addon()

class BaseScraper:
    def __init__(self):
        self.timeout = int(ADDON.getSetting('timeout')) or 30
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def make_request(self, url, method='GET', **kwargs):
        """Make HTTP request with error handling"""
        try:
            kwargs.setdefault('timeout', self.timeout)
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            xbmc.log(f"Request failed: {url} - {str(e)}", xbmc.LOGERROR)
            return None
    
    def search(self, query, media_type='movie'):
        """Search for content - to be implemented by subclasses"""
        raise NotImplementedError("Search method must be implemented by subclass")
    
    def get_stream_links(self, url, media_type='movie', season=None, episode=None):
        """Get stream links - to be implemented by subclasses"""
        raise NotImplementedError("Get stream links method must be implemented by subclass")
    
    def clean_title(self, title):
        """Clean title for better matching"""
        if not title:
            return ""
        # Remove special characters and normalize
        title = re.sub(r'[^\w\s]', '', title.lower())
        title = re.sub(r'\s+', ' ', title).strip()
        return title
    
    def extract_year(self, text):
        """Extract year from text"""
        year_match = re.search(r'\b(19|20)\d{2}\b', text)
        return year_match.group(0) if year_match else None
    
    def extract_quality(self, text):
        """Extract quality information from text"""
        quality_patterns = [
            r'(\d{3,4}p)',
            r'(4K|UHD)',
            r'(HD|SD)',
            r'(BluRay|WEB-DL|WEBRip|HDRip)',
            r'(DVDRip|BRRip)',
        ]
        
        qualities = []
        for pattern in quality_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            qualities.extend(matches)
        
        return ' | '.join(qualities) if qualities else 'Unknown'
