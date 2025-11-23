import numpy as np

def create_detailed_land_mask(lon_grid, lat_grid):
    """Create detailed land mask with realistic coastlines"""
    land_mask = np.zeros_like(lon_grid, dtype=bool)
    
    # More detailed continental definitions
    continents = [
        # North America (detailed)
        {'bounds': (-170, -50, 25, 75), 'density': 0.8},
        # US East Coast detail
        {'bounds': (-85, -65, 25, 50), 'density': 0.9},
        # US West Coast detail  
        {'bounds': (-130, -115, 30, 50), 'density': 0.85},
        # Central America
        {'bounds': (-120, -75, 8, 35), 'density': 0.7},
        
        # South America (detailed)
        {'bounds': (-85, -30, -60, 15), 'density': 0.85},
        # Brazil detail
        {'bounds': (-75, -30, -35, 10), 'density': 0.9},
        
        # Europe (detailed)
        {'bounds': (-15, 50, 35, 75), 'density': 0.9},
        # Scandinavia
        {'bounds': (5, 35, 55, 75), 'density': 0.8},
        # Mediterranean
        {'bounds': (-10, 45, 30, 50), 'density': 0.6},
        
        # Africa (detailed)
        {'bounds': (-20, 55, -40, 40), 'density': 0.9},
        
        # Asia (detailed)
        {'bounds': (30, 180, 10, 80), 'density': 0.8},
        # India subcontinent
        {'bounds': (65, 100, 5, 40), 'density': 0.95},
        # Southeast Asia islands
        {'bounds': (90, 150, -15, 25), 'density': 0.4},
        
        # Australia
        {'bounds': (110, 160, -45, -10), 'density': 0.9},
        
        # Major islands
        # Japan
        {'bounds': (125, 150, 25, 50), 'density': 0.7},
        # British Isles
        {'bounds': (-12, 5, 48, 62), 'density': 0.8},
        # Madagascar
        {'bounds': (43, 51, -26, -11), 'density': 0.9},
        # New Zealand
        {'bounds': (165, 180, -50, -30), 'density': 0.8},
    ]
    
    for continent in continents:
        lon_min, lon_max, lat_min, lat_max = continent['bounds']
        density = continent['density']
        
        # Create mask for this region
        region_mask = ((lon_grid >= lon_min) & (lon_grid <= lon_max) & 
                      (lat_grid >= lat_min) & (lat_grid <= lat_max))
        
        # Add coastal variation using noise
        if np.any(region_mask):
            noise = np.random.random(lon_grid.shape)
            land_probability = np.where(region_mask, density, 0)
            
            # Create more realistic coastlines with distance-based probability
            center_lon, center_lat = (lon_min + lon_max) / 2, (lat_min + lat_max) / 2
            distance_from_center = np.sqrt((lon_grid - center_lon)**2 + (lat_grid - center_lat)**2)
            max_distance = np.sqrt((lon_max - lon_min)**2 + (lat_max - lat_min)**2) / 2
            
            # Higher probability near center, lower near edges (creates coastal effect)
            distance_factor = 1 - (distance_from_center / max_distance)
            distance_factor = np.clip(distance_factor, 0, 1)
            
            adjusted_probability = land_probability * distance_factor
            land_mask |= (region_mask & (noise < adjusted_probability))
    
    return land_mask

def create_realistic_elevation(lon_grid, lat_grid, land_mask):
    """Create realistic elevation data"""
    elevation = np.zeros_like(lon_grid)
    
    # Define major mountain systems with realistic parameters
    mountain_systems = [
        # Rocky Mountains
        {'center': (-110, 45), 'height': 4000, 'width': 8, 'orientation': 0},
        # Sierra Nevada / Cascades
        {'center': (-120, 40), 'height': 3000, 'width': 3, 'orientation': 20},
        # Appalachians
        {'center': (-80, 38), 'height': 1500, 'width': 4, 'orientation': 45},
        # Andes (multiple segments)
        {'center': (-70, -20), 'height': 6000, 'width': 4, 'orientation': 10},
        {'center': (-72, -35), 'height': 5500, 'width': 4, 'orientation': 5},
        # Alps
        {'center': (10, 47), 'height': 4000, 'width': 3, 'orientation': 60},
        # Himalayas
        {'center': (85, 30), 'height': 8000, 'width': 6, 'orientation': 80},
        # Urals
        {'center': (60, 55), 'height': 2000, 'width': 2, 'orientation': 10},
        # Atlas Mountains
        {'center': (-5, 32), 'height': 3000, 'width': 3, 'orientation': 45},
    ]
    
    for mountains in mountain_systems:
        center_lon, center_lat = mountains['center']
        height = mountains['height']
        width = mountains['width']
        orientation = np.radians(mountains['orientation'])
        
        # Rotate coordinates for mountain orientation
        cos_rot, sin_rot = np.cos(orientation), np.sin(orientation)
        
        # Translate to mountain center
        dx = lon_grid - center_lon
        dy = lat_grid - center_lat
        
        # Rotate
        rot_x = cos_rot * dx - sin_rot * dy
        rot_y = sin_rot * dx + cos_rot * dy
        
        # Calculate distance considering elliptical shape
        distance = np.sqrt((rot_x / width)**2 + (rot_y / (width * 0.3))**2)
        
        # Create mountain elevation profile
        mountain_elevation = height * np.exp(-distance**2 / 2)
        
        # Only add elevation on land
        land_mountain_mask = land_mask & (distance < width * 2)
        elevation[land_mountain_mask] = np.maximum(
            elevation[land_mountain_mask], 
            mountain_elevation[land_mountain_mask]
        )
    
    # Add general continental elevation variation
    continental_elevation = np.random.random(elevation.shape) * 800
    elevation[land_mask] += continental_elevation[land_mask]
    
    # Set ocean depths
    ocean_mask = ~land_mask
    ocean_depths = -200 - np.random.random(np.sum(ocean_mask)) * 3000
    elevation[ocean_mask] = ocean_depths
    
    # Add some seamounts and oceanic ridges
    add_oceanic_features(elevation, lon_grid, lat_grid, ocean_mask)
    
    return elevation

def add_oceanic_features(elevation, lon_grid, lat_grid, ocean_mask):
    """Add oceanic ridges and seamounts"""
    
    # Mid-Atlantic Ridge (simplified)
    ridge_lons = np.linspace(-45, -15, 100)
    ridge_lats = np.linspace(-60, 65, 100)
    
    for ridge_lon, ridge_lat in zip(ridge_lons, ridge_lats):
        distance = np.sqrt((lon_grid - ridge_lon)**2 + (lat_grid - ridge_lat)**2)
        ridge_mask = ocean_mask & (distance < 5)
        ridge_elevation = -1000 * np.exp(-distance**2 / 10)
        elevation[ridge_mask] = np.maximum(elevation[ridge_mask], ridge_elevation[ridge_mask])
    
    # Pacific Ring of Fire seamounts
    seamounts = [
        (-155, 20, -2000),  # Hawaiian area
        (-110, 25, -1500),  # East Pacific Rise
        (180, -15, -1800),  # Pacific-Antarctic Ridge
    ]
    
    for seamount_lon, seamount_lat, base_depth in seamounts:
        distance = np.sqrt((lon_grid - seamount_lon)**2 + (lat_grid - seamount_lat)**2)
        seamount_mask = ocean_mask & (distance < 3)
        seamount_elevation = base_depth + 1500 * np.exp(-distance**2 / 4)
        elevation[seamount_mask] = np.maximum(elevation[seamount_mask], seamount_elevation[seamount_mask])

def check_if_land_heuristic(lon, lat):
    """Heuristic to determine if a point is on land based on known geography"""
    
    # Major land masses (approximate bounding boxes)
    land_regions = [
        # North America
        (-170, -50, 15, 75),
        # South America
        (-85, -30, -60, 15),
        # Europe
        (-15, 50, 35, 75),
        # Africa
        (-20, 55, -40, 40),
        # Asia
        (30, 180, 10, 80),
        # Australia
        (110, 160, -45, -10),
        # Greenland
        (-75, -10, 60, 85),
        # Antarctica
        (-180, 180, -90, -60),
    ]
    
    for lon_min, lon_max, lat_min, lat_max in land_regions:
        if lon_min <= lon <= lon_max and lat_min <= lat <= lat_max:
            # Add some coastal variation
            if abs(lat) > 60:  # Polar regions - more land
                return True
            elif abs(lon) > 160:  # Pacific - less land
                return np.random.random() > 0.7
            else:
                return np.random.random() > 0.3  # General coastal probability
    
    return False  # Ocean by default
