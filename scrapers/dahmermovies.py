import re
import urllib
from base_scraper import BaseScraper
import xbmc

class DahmerMoviesScraper(BaseScraper):
    def __init__(self):
        super(DahmerMoviesScraper, self).__init__()
        self.base_url = "https://a.111477.xyz"
    
    def search(self, query, media_type='movie'):
        """Search for content on DahmerMovies"""
        # DahmerMovies uses direct URL structure
        clean_query = re.sub(r'[^\w\s]', '', query).strip()
        encoded_query = urllib.quote_plus(clean_query)
        
        if media_type == 'movie':
            url = f"{self.base_url}/movies/{encoded_query}/"
        else:
            url = f"{self.base_url}/tvs/{encoded_query}/"
        
        response = self.make_request(url)
        if not response:
            return []
        
        # Parse HTML to extract links (simplified)
        links = re.findall(r'<a[^>]*href="([^"]*)"[^>]*>([^<]*)</a>', response.text)
        results = []
        
        for href, text in links:
            if text and href and not href.startswith('../'):
                # Filter for quality content
                if re.search(r'(1080p|2160p|4K)', text, re.IGNORECASE):
                    results.append({
                        'title': text,
                        'url': href if href.startswith('http') else self.base_url + href,
                        'poster': '',
                        'year': self.extract_year(text),
                        'scraper_id': 'dahmermovies'
                    })
        
        return results[:10]  # Limit results
    
    def get_stream_links(self, url, media_type='movie', season=None, episode=None):
        """Get stream links from DahmerMovies"""
        # DahmerMovies provides direct links
        return [{
            'url': url,
            'quality': self.extract_quality(url),
            'size': 'Unknown'
        }]
