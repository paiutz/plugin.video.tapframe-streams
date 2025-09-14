import base64
import json
import re
from base_scraper import BaseScraper
import xbmc
import xbmcgui

class FourKHDHubScraper(BaseScraper):
    def __init__(self):
        super(FourKHDHubScraper, self).__init__()
        self.base_url = "https://4khdhub.fans"
        self.domains_url = "https://raw.githubusercontent.com/phisher98/TVVVV/refs/heads/main/domains.json"
    
    def get_domains(self):
        """Get current domains from GitHub"""
        try:
            response = self.make_request(self.domains_url)
            if response:
                data = response.json()
                return data.get('4khdhub', self.base_url)
        except:
            pass
        return self.base_url
    
    def rot13(self, text):
        """ROT13 encoding/decoding"""
        result = ""
        for char in text:
            if 'a' <= char <= 'z':
                result += chr(((ord(char) - ord('a') + 13) % 26) + ord('a'))
            elif 'A' <= char <= 'Z':
                result += chr(((ord(char) - ord('A') + 13) % 26) + ord('A'))
            else:
                result += char
        return result
    
    def base64_decode(self, text):
        """Base64 decode with error handling"""
        try:
            return base64.b64decode(text).decode('utf-8')
        except:
            return ""
    
    def search(self, query, media_type='movie'):
        """Search for content on 4KHDHub"""
        domain = self.get_domains()
        search_url = f"{domain}/?s={query}"
        
        response = self.make_request(search_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Parse search results
        for link in soup.find_all('a', href=True):
            title_elem = link.find('h3', class_='movie-card-title')
            if title_elem:
                title = title_elem.get_text().strip()
                href = link['href']
                poster = link.find('img').get('src', '') if link.find('img') else ''
                
                if title and href:
                    results.append({
                        'title': title,
                        'url': href if href.startswith('http') else domain + href,
                        'poster': poster,
                        'year': self.extract_year(title),
                        'scraper_id': '4khdhub'
                    })
        
        return results[:10]  # Limit results
    
    def get_stream_links(self, url, media_type='movie', season=None, episode=None):
        """Get stream links from content page"""
        response = self.make_request(url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        links = []
        
        # Find download links
        selectors = [
            'div.download-item a',
            '.download-item a',
            'a[href*="hubdrive"]',
            'a[href*="hubcloud"]',
            'a[href*="pixeldrain"]',
            'a.btn[href]',
        ]
        
        for selector in selectors:
            for link in soup.select(selector):
                href = link.get('href')
                if href and any(x in href.lower() for x in ['hubdrive', 'hubcloud', 'pixeldrain', 'download']):
                    links.append(href)
        
        # Process links to get final stream URLs
        stream_links = []
        for link in links[:5]:  # Limit to 5 links
            stream_url = self.resolve_link(link)
            if stream_url:
                stream_links.append({
                    'url': stream_url,
                    'quality': self.extract_quality(link),
                    'size': 'Unknown'
                })
        
        return stream_links
    
    def resolve_link(self, url):
        """Resolve redirect links to final URLs"""
        try:
            response = self.make_request(url)
            if not response:
                return url
            
            # Look for redirect patterns
            html = response.text
            
            # Pattern 1: Base64 encoded redirect
            b64_pattern = r"s\('o','([A-Za-z0-9+/=]+)'"
            b64_match = re.search(b64_pattern, html)
            if b64_match:
                try:
                    decoded = self.base64_decode(b64_match.group(1))
                    decoded = self.rot13(decoded)
                    data = json.loads(decoded)
                    if 'o' in data:
                        return self.base64_decode(data['o'])
                except:
                    pass
            
            # Pattern 2: Direct links
            direct_pattern = r'href="([^"]*\.mp4[^"]*)"'
            direct_match = re.search(direct_pattern, html)
            if direct_match:
                return direct_match.group(1)
            
            return url
            
        except Exception as e:
            xbmc.log(f"Failed to resolve link: {url} - {str(e)}", xbmc.LOGERROR)
            return url
