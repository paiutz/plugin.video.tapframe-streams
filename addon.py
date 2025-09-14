import sys
import urllib
import urlparse
import xbmc
import xbmcgui
import xbmcplugin
import xbmcaddon
import json
import base64
from scrapers import get_available_scrapers, search_all_scrapers, get_stream_links

# Addon constants
ADDON = xbmcaddon.Addon()
ADDON_ID = ADDON.getAddonInfo('id')
ADDON_NAME = ADDON.getAddonInfo('name')
ADDON_VERSION = ADDON.getAddonInfo('version')
ADDON_PATH = ADDON.getAddonInfo('path')
ADDON_HANDLE = int(sys.argv[1])

# Base URL
BASE_URL = sys.argv[0]

def build_url(query):
    """Build URL from query parameters"""
    return BASE_URL + '?' + urllib.urlencode(query)

def get_params():
    """Get URL parameters"""
    param_string = sys.argv[2]
    if len(param_string) >= 2:
        return urlparse.parse_qs(param_string[1:])
    return {}

def show_main_menu():
    """Display main menu with scraper options"""
    xbmcplugin.setContent(ADDON_HANDLE, 'files')
    
    # Get available scrapers
    scrapers = get_available_scrapers()
    
    # Add search option
    url = build_url({'mode': 'search'})
    li = xbmcgui.ListItem('[COLOR gold]Search Movies/TV Shows[/COLOR]', iconImage='DefaultAddonsSearch.png')
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, True)
    
    # Add scraper options
    for scraper in scrapers:
        if scraper.get('enabled', True):
            url = build_url({'mode': 'scraper_menu', 'scraper_id': scraper['id']})
            li = xbmcgui.ListItem(scraper['name'], iconImage='DefaultVideo.png')
            li.setArt({'fanart': ADDON.getAddonInfo('fanart')})
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, True)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def show_scraper_menu(scraper_id):
    """Show menu for specific scraper"""
    xbmcplugin.setContent(ADDON_HANDLE, 'files')
    
    scrapers = get_available_scrapers()
    scraper = next((s for s in scrapers if s['id'] == scraper_id), None)
    
    if not scraper:
        xbmcgui.Dialog().notification('Error', 'Scraper not found', xbmcgui.NOTIFICATION_ERROR)
        return
    
    # Search option
    url = build_url({'mode': 'search', 'scraper_id': scraper_id})
    li = xbmcgui.ListItem('[COLOR gold]Search ' + scraper['name'] + '[/COLOR]', iconImage='DefaultAddonsSearch.png')
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, True)
    
    # Recent/Movies option
    url = build_url({'mode': 'browse', 'scraper_id': scraper_id, 'content_type': 'movie'})
    li = xbmcgui.ListItem('Browse Movies', iconImage='DefaultMovies.png')
    xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, True)
    
    # TV Shows option
    if 'tv' in scraper.get('supportedTypes', []):
        url = build_url({'mode': 'browse', 'scraper_id': scraper_id, 'content_type': 'tv'})
        li = xbmcgui.ListItem('Browse TV Shows', iconImage='DefaultTVShows.png')
        xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, True)
    
    xbmcplugin.endOfDirectory(ADDON_HANDLE)

def show_search_dialog(scraper_id=None):
    """Show search dialog"""
    keyboard = xbmc.Keyboard('', 'Search Movies/TV Shows')
    keyboard.doModal()
    
    if keyboard.isConfirmed():
        query = keyboard.getText()
        if query:
            show_search_results(query, scraper_id)

def show_search_results(query, scraper_id=None):
    """Show search results"""
    xbmcplugin.setContent(ADDON_HANDLE, 'movies')
    
    # Show progress dialog
    progress = xbmcgui.DialogProgress()
    progress.create('Searching', 'Searching for: ' + query)
    progress.update(0)
    
    try:
        # Search using specified scraper or all scrapers
        if scraper_id:
            results = search_all_scrapers(query, scraper_ids=[scraper_id])
        else:
            results = search_all_scrapers(query)
        
        progress.update(50)
        
        if not results:
            xbmcgui.Dialog().notification('No Results', 'No results found for: ' + query, xbmcgui.NOTIFICATION_INFO)
            xbmcplugin.endOfDirectory(ADDON_HANDLE)
            return
        
        # Display results
        for i, result in enumerate(results):
            progress.update(50 + int(50 * i / len(results)))
            
            url = build_url({
                'mode': 'play',
                'scraper_id': result['scraper_id'],
                'title': result['title'],
                'year': result.get('year', ''),
                'season': result.get('season', ''),
                'episode': result.get('episode', ''),
                'url': base64.b64encode(result['url'])
            })
            
            li = xbmcgui.ListItem(result['title'])
            
            # Set metadata
            info = {
                'title': result['title'],
                'year': result.get('year'),
            }
            
            if result.get('season') and result.get('episode'):
                info['episode'] = result['episode']
                info['season'] = result['season']
                xbmcplugin.setContent(ADDON_HANDLE, 'episodes')
            
            li.setInfo('video', info)
            
            # Set artwork
            if result.get('poster'):
                li.setArt({'thumb': result['poster'], 'poster': result['poster']})
            
            # Add context menu for quality selection
            if result.get('qualities'):
                quality_menu = []
                for quality in result['qualities']:
                    quality_url = build_url({
                        'mode': 'play',
                        'scraper_id': result['scraper_id'],
                        'title': result['title'],
                        'year': result.get('year', ''),
                        'season': result.get('season', ''),
                        'episode': result.get('episode', ''),
                        'url': base64.b64encode(quality['url']),
                        'quality': quality.get('quality', '')
                    })
                    quality_menu.append((quality.get('quality', 'Unknown'), 'RunPlugin(' + quality_url + ')'))
                
                li.addContextMenuItems(quality_menu)
            
            xbmcplugin.addDirectoryItem(ADDON_HANDLE, url, li, False)
        
        progress.close()
        xbmcplugin.endOfDirectory(ADDON_HANDLE)
        
    except Exception as e:
        progress.close()
        xbmcgui.Dialog().notification('Error', 'Search failed: ' + str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(ADDON_HANDLE)

def play_stream(params):
    """Play video stream"""
    try:
        url = base64.b64decode(params['url'])
        quality = params.get('quality', '')
        
        # Create list item
        li = xbmcgui.ListItem(params['title'])
        li.setPath(url)
        
        # Set metadata
        info = {
            'title': params['title'],
        }
        
        if params.get('year'):
            info['year'] = int(params['year'])
        
        if params.get('season') and params.get('episode'):
            info['episode'] = int(params['episode'])
            info['season'] = int(params['season'])
        
        li.setInfo('video', info)
        
        # Set quality label if available
        if quality:
            li.setLabel(params['title'] + ' [COLOR blue][' + quality + ')[/COLOR]')
        
        # Play the video
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, True, li)
        
    except Exception as e:
        xbmcgui.Dialog().notification('Error', 'Failed to play: ' + str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.setResolvedUrl(ADDON_HANDLE, False, xbmcgui.ListItem())

def router():
    """Main router function"""
    params = get_params()
    mode = params.get('mode', [None])[0]
    
    if mode is None:
        show_main_menu()
    elif mode == 'scraper_menu':
        scraper_id = params.get('scraper_id', [None])[0]
        show_scraper_menu(scraper_id)
    elif mode == 'search':
        scraper_id = params.get('scraper_id', [None])[0]
        show_search_dialog(scraper_id)
    elif mode == 'browse':
        # Placeholder for browse functionality
        xbmcgui.Dialog().notification('Info', 'Browse functionality coming soon!', xbmcgui.NOTIFICATION_INFO)
    elif mode == 'play':
        play_stream(params)

if __name__ == '__main__':
    router()
