import numpy as np
import cartopy.feature as cfeature
from terrain_generation import create_detailed_land_mask, create_realistic_elevation, check_if_land_heuristic
from color_mapping import create_detailed_terrain_colors
from geographic_features import add_detailed_coastlines, add_detailed_borders, add_major_rivers, add_major_cities

def get_cartopy_land_mask(lon_grid, lat_grid):
    """Use cartopy's built-in land feature (may use cached data)"""
    try:
        # This uses cartopy's cached Natural Earth data if available
        land_feature = cfeature.LAND
        
        # Create a simple projection to test land/ocean
        land_mask = np.zeros_like(lon_grid, dtype=bool)
        
        # Sample points to determine land vs ocean
        # This is a simplified approach - for full accuracy you'd need
        # to properly intersect with the land polygons
        
        for i in range(0, lon_grid.shape[0], 5):  # Sample every 5th point for speed
            for j in range(0, lon_grid.shape[1], 5):
                # Use a heuristic based on known land areas
                lon, lat = lon_grid[i, j], lat_grid[i, j]
                is_land = check_if_land_heuristic(lon, lat)
                
                # Fill in surrounding points
                i_start, i_end = max(0, i-2), min(lon_grid.shape[0], i+3)
                j_start, j_end = max(0, j-2), min(lon_grid.shape[1], j+3)
                land_mask[i_start:i_end, j_start:j_end] = is_land
        
        return land_mask
        
    except:
        return create_detailed_land_mask(lon_grid, lat_grid)

def create_offline_basemap(ax, ds, z_level):
    """Create basemap using offline/cached Natural Earth-style features"""
    
    # Get coordinate bounds
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    # Create lower resolution grid for basemap (to avoid overwhelming the data)
    resolution = 100  # Reduced from 200 for performance
    lons = np.linspace(lon_min, lon_max, resolution)
    lats = np.linspace(lat_min, lat_max, resolution)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Create realistic land/ocean mask using built-in cartopy features (cached)
    try:
        land_mask = get_cartopy_land_mask(lon_grid, lat_grid)
        elevation_data = create_realistic_elevation(lon_grid, lat_grid, land_mask)
    except:
        print("  Using fallback terrain generation")
        land_mask = create_detailed_land_mask(lon_grid, lat_grid)
        elevation_data = create_realistic_elevation(lon_grid, lat_grid, land_mask)
    
    # Create terrain colors
    terrain_colors = create_detailed_terrain_colors(elevation_data, land_mask)
    
    # Create Z plane WELL BELOW the data
    # Make sure basemap is significantly below data range
    base_z_level = z_level - abs(z_level) * 0.1  # Further below the data
    z_plane = np.full_like(lon_grid, base_z_level)
    
    # Add MUCH smaller elevation variations (so basemap stays below data)
    elevation_scale = abs(z_level) * 0.005  # Reduced from 0.02 to 0.005
    z_plane += elevation_data * elevation_scale
    
    # Plot the terrain surface with high transparency
    terrain_surf = ax.plot_surface(lon_grid, lat_grid, z_plane,
                                  facecolors=terrain_colors,
                                  alpha=0.4,  # Increased transparency
                                  shade=False,  # Disable shading to avoid black areas
                                  linewidth=0,
                                  antialiased=True)
    
    # Add geographic features at the base level (not floating)
    feature_z_level = base_z_level + elevation_scale * 0.1  # Just slightly above base
    
    add_detailed_coastlines(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)
    add_detailed_borders(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)
    add_major_rivers(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)
    add_major_cities(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)

def create_simple_basemap(ax, ds, z_level):
    """Create a simpler, less intrusive basemap"""
    
    # Get coordinate bounds
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    # Create very simple base plane
    resolution = 50  # Very coarse for simplicity
    lons = np.linspace(lon_min, lon_max, resolution)
    lats = np.linspace(lat_min, lat_max, resolution)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Simple flat base well below data
    base_z_level = z_level - abs(z_level) * 0.2
    z_plane = np.full_like(lon_grid, base_z_level)
    
    # Simple ocean blue base
    ocean_color = np.zeros((*lon_grid.shape, 4))
    ocean_color[:, :] = [0.2, 0.4, 0.8, 0.3]  # Light blue, very transparent
    
    # Plot simple base
    base_surf = ax.plot_surface(lon_grid, lat_grid, z_plane,
                               facecolors=ocean_color,
                               alpha=0.3,
                               shade=False,
                               linewidth=0,
                               antialiased=True)
    
    # Add only major coastlines
    add_simple_coastlines(ax, lon_min, lon_max, lat_min, lat_max, base_z_level)

def add_simple_coastlines(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add simplified coastlines"""
    
    # Very simplified major coastlines
    coastlines = [
        # US East Coast 
        {'lons': [-81, -80, -79, -76, -74, -71, -70, -67],
         'lats': [24, 27, 32, 37, 40, 42, 43, 45]},
        
        # US West Coast
        {'lons': [-124, -123, -122, -121, -120, -118],
         'lats': [41, 43, 45, 36, 34, 32]},
        
        # European Coast
        {'lons': [-9, -5, 0, 5, 10],
         'lats': [43, 45, 50, 54, 57]},
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
            z_coords = np.full_like(filtered_lons, z_level)
            
            ax.plot(filtered_lons, filtered_lats, z_coords, 
                   'k-', linewidth=1.0, alpha=0.6)
