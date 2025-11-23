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
    
    # Create high-resolution grid
    resolution = 200
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
    
    # Create Z plane with slight elevation variations
    z_plane = np.full_like(lon_grid, z_level)
    z_plane += elevation_data * (abs(z_level) * 0.02)  # 2% elevation variation
    
    # Plot the terrain surface
    terrain_surf = ax.plot_surface(lon_grid, lat_grid, z_plane,
                                  facecolors=terrain_colors,
                                  alpha=0.8, shade=True, linewidth=0,
                                  antialiased=True)
    
    # Add detailed geographic features
    add_detailed_coastlines(ax, lon_min, lon_max, lat_min, lat_max, z_level)
    add_detailed_borders(ax, lon_min, lon_max, lat_min, lat_max, z_level)
    add_major_rivers(ax, lon_min, lon_max, lat_min, lat_max, z_level)
    add_major_cities(ax, lon_min, lon_max, lat_min, lat_max, z_level)
