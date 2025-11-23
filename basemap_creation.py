import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import cartopy.crs as ccrs
import cartopy.feature as cfeature

def create_flat_map_basemap(ax, ds, z_level):
    """Project a flat map onto the bottom plane of the 3D plot"""
    
    print("    Creating flat map projection on bottom plane...")
    
    # Get coordinate bounds
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    # Create map grid matching your data resolution or slightly coarser
    map_lons = np.linspace(lon_min, lon_max, len(ds.longitude) // 2)  # Half resolution for performance
    map_lats = np.linspace(lat_min, lat_max, len(ds.latitude) // 2)
    lon_grid, lat_grid = np.meshgrid(map_lons, map_lats)
    
    # Create flat Z plane at the bottom
    z_plane = np.full_like(lon_grid, z_level)
    
    # Create a realistic land/ocean map for the bottom plane
    map_colors = create_flat_map_colors(lon_grid, lat_grid)
    
    # Project the map onto the bottom plane
    try:
        map_surf = ax.plot_surface(lon_grid, lat_grid, z_plane,
                                  facecolors=map_colors,
                                  alpha=0.8,  # Semi-transparent so you can see it through data
                                  shade=False,
                                  linewidth=0,
                                  antialiased=True,
                                  zorder=1)  # Low zorder (bottom layer)
        
        print("      ✓ Flat map projected successfully")
        
        # Add political boundaries and coastlines on the flat plane
        add_flat_map_features(ax, lon_min, lon_max, lat_min, lat_max, z_level)
        
    except Exception as e:
        print(f"      ✗ Map projection failed: {e}")
        # Fallback to simple colored base
        ax.plot_surface(lon_grid, lat_grid, z_plane,
                       color='lightblue', alpha=0.5,
                       shade=False, linewidth=0, zorder=1)

def create_flat_map_colors(lon_grid, lat_grid):
    """Create realistic map colors for flat projection"""
    colors = np.zeros((*lon_grid.shape, 4))  # RGBA
    
    # Default to ocean blue
    colors[:, :] = [0.4, 0.6, 1.0, 1.0]  # Light ocean blue
    
    # Add continental land masses with proper map colors
    continents = [
        # North America - green
        {'bounds': (-170, -50, 15, 75), 'color': [0.6, 0.8, 0.4, 1.0]},
        # South America - light green
        {'bounds': (-85, -30, -60, 15), 'color': [0.5, 0.7, 0.3, 1.0]},
        # Europe - yellow-green
        {'bounds': (-15, 50, 35, 75), 'color': [0.7, 0.8, 0.5, 1.0]},
        # Africa - tan/brown
        {'bounds': (-20, 55, -40, 40), 'color': [0.8, 0.7, 0.5, 1.0]},
        # Asia - light brown
        {'bounds': (30, 180, 10, 80), 'color': [0.7, 0.6, 0.4, 1.0]},
        # Australia - orange-tan
        {'bounds': (110, 160, -45, -10), 'color': [0.8, 0.6, 0.3, 1.0]},
        # Antarctica - white
        {'bounds': (-180, 180, -90, -60), 'color': [0.95, 0.95, 0.95, 1.0]},
    ]
    
    for continent in continents:
        lon_min, lon_max, lat_min, lat_max = continent['bounds']
        color = continent['color']
        
        # Create mask for this continent
        continent_mask = ((lon_grid >= lon_min) & (lon_grid <= lon_max) & 
                         (lat_grid >= lat_min) & (lat_grid <= lat_max))
        
        # Apply continental color
        colors[continent_mask] = color
    
    return colors

def add_flat_map_features(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add political boundaries, coastlines, etc. to the flat map plane"""
    
    # Major coastlines on the flat plane
    coastlines = [
        # US East Coast
        {'lons': [-81, -80, -79, -76, -74, -71, -70, -67],
         'lats': [24, 27, 32, 37, 40, 42, 43, 45]},
        # US West Coast
        {'lons': [-124, -123, -122, -121, -120, -118],
         'lats': [41, 43, 45, 36, 34, 32]},
        # European Coast
        {'lons': [-9, -5, 0, 5, 10
