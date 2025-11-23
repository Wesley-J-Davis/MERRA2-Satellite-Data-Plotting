import numpy as np

def add_detailed_coastlines(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add detailed coastlines using coordinate-based approach"""
    
    # Major coastline segments (more detailed than before)
    coastlines = [
        # US East Coast (detailed)
        {'name': 'US_East', 'lons': [-81.5, -81.0, -80.0, -79.0, -77.5, -76.0, -75.5, -74.5, -73.5, -72.0, -71.0, -70.5, -70.0, -69.5, -69.0, -68.5, -67.5],
         'lats': [24.5, 25.5, 27.0, 32.0, 35.0, 36.5, 37.5, 39.5, 40.5, 41.5, 42.0, 42.5, 43.0, 43.5, 44.0, 44.5, 45.0]},
        
        # US West Coast
        {'name': 'US_West', 'lons': [-124.5, -124.0, -123.5, -123.0, -122.5, -122.0, -121.5, -120.5, -120.0, -119.0, -118.0, -117.5],
         'lats': [41.0, 42.0, 43.0, 44.0, 45.5, 46.5, 47.0, 36.0, 34.5, 33.0, 32.5, 30.0]},
        
        # European Atlantic Coast
        {'name': 'Europe_Atlantic', 'lons': [-9.5, -8.0, -6.0, -4.0, -2.0, 0.0, 2.0, 4.0, 6.0, 8.0, 10.0],
         'lats': [43.0, 44.5, 46.0, 48.0, 50.5, 51.0, 52.0, 54.0, 55.5, 57.0, 58.5]},
        
        # African West Coast
        {'name': 'Africa_West', 'lons': [-17.0, -16.5, -16.0, -15.0, -13.0, -10.0, -8.0, -5.0, -3.0, 0.0, 3.0, 7.0, 10.0],
         'lats': [21.0, 18.0, 15.0, 12.0, 8.0, 5.0, 2.0, -2.0, -8.0, -15.0, -25.0, -30.0, -35.0]},
        
        # South American East Coast
        {'name': 'SAmerica_East', 'lons': [-35.0, -36.0, -38.0, -40.0, -42.0, -45.0, -48.0, -50.0, -52.0, -55.0, -58.0, -60.0],
         'lats': [-8.0, -12.0, -16.0, -20.0, -24.0, -28.0, -32.0, -36.0, -40.0, -44.0, -48.0, -52.0]},
        
        # Australian Coast (partial)
        {'name': 'Australia', 'lons': [113.0, 115.0, 118.0, 122.0, 126.0, 130.0, 135.0, 140.0, 145.0, 150.0, 153.0],
         'lats': [-32.0, -30.0, -28.0, -25.0, -20.0, -15.0, -12.0, -15.0, -20.0, -28.0, -35.0]},
    ]
    
    for coastline in coastlines:
        lons = np.array(coastline['lons'])
        lats = np.array(coastline['lats'])
        
        # Filter to domain bounds
        mask = ((lons >= lon_min) & (lons <= lon_max) & 
               (lats >= lat_min) & (lats <= lat_max))
        
        if np.any(mask):
            filtered_lons = lons[mask]
            filtered_lats = lats[mask]
            z_coords = np.full_like(filtered_lons, z_level + 0.005)
            
            ax.plot(filtered_lons, filtered_lats, z_coords, 
                   'k-', linewidth=1.2, alpha=0.9)

def add_detailed_borders(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add major political borders"""
    
    borders = [
        # US-Canada border
        {'name': 'US-Canada', 'lons': np.linspace(-141, -95, 25), 'lats': np.full(25, 49)},
        # US-Mexico border
        {'name': 'US-Mexico', 'lons': [-117, -115, -112, -110, -108, -106, -104, -102, -100, -98, -97],
         'lats': [32.5, 31.5, 31.3, 31.3, 31.8, 32.0, 29.7, 28.0, 26.0, 25.8, 25.8]},
        # India-Pakistan
        {'name': 'India-Pakistan', 'lons': [61, 65, 70, 74, 75], 'lats': [25, 28, 32, 34, 37]},
        # Germany-Poland
        {'name': 'Germany-Poland', 'lons': [14.1, 14.5, 15.0, 15.5], 'lats': [53.0, 52.5, 51.5, 50.5]},
    ]
    
    for border in borders:
        lons = np.array(border['lons'])
        lats = np.array(border['lats'])
        
        mask = ((lons >= lon_min) & (lons <= lon_max) & 
               (lats >= lat_min) & (lats <= lat_max))
        
        if np.any(mask):
            filtered_lons = lons[mask]
            filtered_lats = lats[mask]
            z_coords = np.full_like(filtered_lons, z_level + 0.003)
            
            ax.plot(filtered_lons, filtered_lats, z_coords, 
                   'r-', linewidth=0.8, alpha=0.7)

def add_major_rivers(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add major world rivers"""
    
    rivers = [
        # Mississippi River
        {'name': 'Mississippi', 'lons': [-90, -91, -92, -93, -94, -95], 
         'lats': [29, 32, 35, 38, 41, 44]},
        # Amazon River
        {'name': 'Amazon', 'lons': [-50, -55, -60, -65, -70], 'lats': [-3, -3, -3, -4, -5]},
        # Nile River
        {'name': 'Nile', 'lons': [30, 31, 32, 33], 'lats': [31, 26, 22, 18]},
        # Rhine River
        {'name': 'Rhine', 'lons': [6, 7, 8, 9], 'lats': [47, 49, 51, 52]},
        # Yangtze River
        {'name': 'Yangtze', 'lons': [121, 115, 110, 105, 100], 'lats': [31, 30, 30, 29, 28]},
    ]
    
    for river in rivers:
        lons = np.array(river['lons'])
        lats = np.array(river['lats'])
        
        mask = ((lons >= lon_min) & (lons <= lon_max) & 
               (lats >= lat_min) & (lats <= lat_max))
        
        if np.any(mask):
            filtered_lons = lons[mask]
            filtered_lats = lats[mask]
            z_coords = np.full_like(filtered_lons, z_level + 0.002)
            
            ax.plot(filtered_lons, filtered_lats, z_coords, 
                   'cyan', linewidth=1.0, alpha=0.8)

def add_major_cities(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add major city markers"""
    
    cities = [
        {'name': 'New York', 'lon': -74.0, 'lat': 40.7},
        {'name': 'Los Angeles', 'lon': -118.2, 'lat': 34.1},
        {'name': 'London', 'lon': -0.1, 'lat': 51.5},
        {'name': 'Paris', 'lon': 2.3, 'lat': 48.9},
        {'name': 'Tokyo', 'lon': 139.7, 'lat': 35.7},
        {'name': 'Sydney', 'lon': 151.2, 'lat': -33.9},
        {'name': 'Cairo', 'lon': 31.2, 'lat': 30.0},
        {'name': 'Mumbai', 'lon': 72.8, 'lat': 19.1},
        {'name': 'Beijing', 'lon': 116.4, 'lat': 39.9},
        {'name': 'São Paulo', 'lon': -46.6, 'lat': -23.5},
    ]
    
    for city in cities:
        lon, lat = city['lon'], city['lat']
        
        if (lon_min <= lon <= lon_max) and (lat_min <= lat <= lat_max):
            ax.scatter([lon], [lat], [z_level + 0.01], 
                      c='red', s=30, alpha=0.8, marker='o')
