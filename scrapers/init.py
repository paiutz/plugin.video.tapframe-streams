import xbmcaddon
from fourkhdhub import FourKHDHubScraper
from uhdmovies import UHDMoviesScraper
from dahmermovies import DahmerMoviesScraper

ADDON = xbmcaddon.Addon()

# Available scrapers
SCRAPERS = {
    '4khdhub': FourKHDHubScraper,
    'uhdmovies': UHDMoviesScraper,
    'dahmermovies': DahmerMoviesScraper,
}

def get_available_scrapers():
    """Get list of available scrapers from manifest"""
    try:
        with open(ADDON.getAddonInfo('path') + '/manifest.json', 'r') as f:
            manifest = json.load(f)
            return manifest.get('scrapers', [])
    except:
        # Fallback scrapers
        return [
            {
                'id': '4khdhub',
                'name': '4KHDHub',
                'description': '4KHDHub direct links',
                'enabled': ADDON.getSetting('enable_4khdhub') == 'true',
                'supportedTypes': ['movie', 'tv']
            },
            {
                'id': 'uhdmovies',
                'name': 'UHDMovies',
                'description': 'High-quality movie and TV show streams',
                'enabled': ADDON.getSetting('enable_uhdmovies') == 'true',
                'supportedTypes': ['movie', 'tv']
            },
            {
                'id': 'dahmermovies',
                'name': 'DahmerMovies',
                'description': 'High-quality streams from DahmerMovies',
                'enabled': ADDON.getSetting('enable_dahmermovies') == 'true',
                'supportedTypes': ['movie', 'tv']
            }
        ]

def search_all_scrapers(query, scraper_ids=None, media_type='movie'):
    """Search across all enabled scrapers"""
    results = []
    available_scrapers = get_available_scrapers()
    
    for scraper_info in available_scrapers:
        scraper_id = scraper_info['id']
        
        # Check if scraper should be used
        if scraper_ids and scraper_id not in scraper_ids:
            continue
        
        if not scraper_info.get('enabled', True):
            continue
        
        if media_type not in scraper_info.get('supportedTypes', []):
            continue
        
        try:
            scraper_class = SCRAPERS.get(scraper_id)
            if scraper_class:
                scraper = scraper_class()
                scraper_results = scraper.search(query, media_type)
                
                # Add scraper info to results
                for result in scraper_results:
                    result['scraper_id'] = scraper_id
                    result['scraper_name'] = scraper_info['name']
                
                results.extend(scraper_results)
                
        except Exception as e:
            xbmc.log(f"Search failed for {scraper_id}: {str(e)}", xbmc.LOGERROR)
    
    return results

def get_stream_links(scraper_id, url, media_type='movie', season=None, episode=None):
    """Get stream links from specific scraper"""
    try:
        scraper_class = SCRAPERS.get(scraper_id)
        if scraper_class:
            scraper = scraper_class()
            return scraper.get_stream_links(url, media_type, season, episode)
    except Exception as e:
        xbmc.log(f"Failed to get stream links from {scraper_id}: {str(e)}", xbmc.LOGERROR)
    
    return []
