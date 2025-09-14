import re
import json
from base_scraper import BaseScraper
import xbmc
from bs4 import BeautifulSoup

class UHDMoviesScraper(BaseScraper):
    def __init__(self):
        super(UHDMoviesScraper, self).__init__()
        self.base_url = "https://uhdmovies.email"
        self.domains_url = "https://raw.githubusercontent.com/phisher98/TVVVV/refs/heads/main/domains.json"
    
    def get_domain(self):
        """Get current domain from GitHub"""
        try:
            response = self.make_request(self.domains_url)
            if response:
                data = response.json()
                return data.get('UHDMovies', self.base_url)
        except:
            pass
        return self.base_url
    
    def search(self, query, media_type='movie'):
        """Search for content on UHDMovies"""
        domain = self.get_domain()
        search_url = f"{domain}/search/{query}"
        
        response = self.make_request(search_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        # Parse search results
        for article in soup.find_all('article', class_='gridlove-post'):
            link_elem = article.find('a', href=lambda x: x and '/download-' in x)
            if link_elem:
                title = link_elem.get('title', '') or link_elem.get_text().strip()
                href = link_elem['href']
                
                if title and href:
                    results.append({
                        'title': title,
                        'url': href if href.startswith('http') else domain + href,
                        'poster': '',
                        'year': self.extract_year(title),
                        'scraper_id': 'uhdmovies'
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
        for link in soup.find_all('a', href=True):
            href = link['href']
            if any(x in href.lower() for x in ['tech.unblockedgames', 'tech.examzculture', 'tech.examdegree']):
                # Extract quality from surrounding text
                parent = link.find_parent()
                quality_text = ""
                if parent:
                    quality_text = parent.get_text()
                
                links.append({
                    'url': href,
                    'quality': self.extract_quality(quality_text),
                    'size': self.extract_size(quality_text)
                })
        
        # Resolve links to get final URLs
        stream_links = []
        for link in links[:5]:  # Limit to 5 links
            final_url = self.resolve_sid_link(link['url'])
            if final_url:
                stream_links.append({
                    'url': final_url,
                    'quality': link['quality'],
                    'size': link['size']
                })
        
        return stream_links
    
    def resolve_sid_link(self, url):
        """Resolve SID links to final URLs"""
        try:
            # This is a simplified version - in reality, SID resolution is complex
            # and involves multiple steps and JavaScript execution
            response = self.make_request(url)
            if not response:
                return None
            
            html = response.text
            
            # Look for direct download links
            patterns = [
                r'href="([^"]*workers\.dev[^"]*)"',
                r'href="([^"]*driveleech\.net[^"]*)"',
                r'href="([^"]*\.mp4[^"]*)"',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, html)
                if match:
                    return match.group(1)
            
            return None
            
        except Exception as e:
            xbmc.log(f"Failed to resolve SID link: {url} - {str(e)}", xbmc.LOGERROR)
            return None
    
    def extract_size(self, text):
        """Extract file size from text"""
        size_pattern = r'\[([0-9.,]+\s*[KMGT]B[^\]]*)\]'
        match = re.search(size_pattern, text)
        return match.group(1) if match else 'Unknown'
