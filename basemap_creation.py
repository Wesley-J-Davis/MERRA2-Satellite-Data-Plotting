import numpy as np
import cartopy.feature as cfeature
from terrain_generation import create_detailed_land_mask, create_realistic_elevation, check_if_land_heuristic
from color_mapping import create_detailed_terrain_colors
from geographic_features import add_detailed_coastlines, add_detailed_borders, add_major_rivers, add_major_cities

def get_cartopy_land_mask(lon_grid, lat_grid):
    """Use cartopy's built-in land feature (may use cached data)"""
    try:
        land_mask = np.zeros_like(lon_grid, dtype=bool)
        
        # Sample points to determine land vs ocean using our existing heuristic
        for i in range(0, lon_grid.shape[0], 3):  # More frequent sampling
            for j in range(0, lon_grid.shape[1], 3):
                lon, lat = lon_grid[i, j], lat_grid[i, j]
                is_land = check_if_land_heuristic(lon, lat)
                
                # Fill in surrounding points
                i_start, i_end = max(0, i-1), min(lon_grid.shape[0], i+2)
                j_start, j_end = max(0, j-1), min(lon_grid.shape[1], j+2)
                land_mask[i_start:i_end, j_start:j_end] = is_land
        
        return land_mask
        
    except:
        return create_detailed_land_mask(lon_grid, lat_grid)

def create_offline_basemap(ax, ds, z_level):
    """Create realistic basemap using our existing detailed modules"""
    
    print("    Creating realistic basemap with existing modules...")
    
    # Get coordinate bounds
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    # Create appropriate resolution grid for basemap
    resolution = 150  # Good balance of detail vs performance
    lons = np.linspace(lon_min, lon_max, resolution)
    lats = np.linspace(lat_min, lat_max, resolution)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Use our existing terrain generation functions
    try:
        print("      Generating land mask...")
        land_mask = get_cartopy_land_mask(lon_grid, lat_grid)
        
        print("      Creating realistic elevation...")
        elevation_data = create_realistic_elevation(lon_grid, lat_grid, land_mask)
        
        print("      Generating terrain colors...")
        terrain_colors = create_detailed_terrain_colors(elevation_data, land_mask)
        
    except Exception as e:
        print(f"      Fallback to simple land mask due to: {e}")
        land_mask = create_detailed_land_mask(lon_grid, lat_grid)
        elevation_data = create_realistic_elevation(lon_grid, lat_grid, land_mask)
        terrain_colors = create_detailed_terrain_colors(elevation_data, land_mask)
    
    # Calculate basemap Z position - well below data
    data_range = abs(z_level) if z_level != 0 else 1.0
    base_z_level = z_level - data_range * 0.4  # Significant separation
    
    # Create Z plane with realistic elevation variations (but scaled small)
    z_plane = np.full_like(lon_grid, base_z_level)
    elevation_scale = data_range * 0.01  # Very small elevation variations
    z_plane += elevation_data * elevation_scale
    
    # Fix any invalid colors that might cause black squares
    terrain_colors = fix_color_array(terrain_colors)
    
    # Plot the realistic terrain surface
    print("      Rendering terrain surface...")
    try:
        terrain_surf = ax.plot_surface(lon_grid, lat_grid, z_plane,
                                      facecolors=terrain_colors,
                                      alpha=0.7,  # Good visibility but not overwhelming
                                      shade=False,  # Disable shading to prevent black areas
                                      linewidth=0,
                                      antialiased=False,  # Disable for performance
                                      zorder=1)  # Low zorder (background)
        
        print("      ✓ Terrain surface rendered successfully")
        
    except Exception as e:
        print(f"      ✗ Terrain surface failed: {e}, using fallback")
        # Fallback to simple ocean base
        ax.plot_surface(lon_grid, lat_grid, z_plane,
                       color='lightblue', alpha=0.3,
                       shade=False, linewidth=0, zorder=1)
    
    # Add our existing geographic features
    feature_z_level = base_z_level + elevation_scale * 2  # Slightly above terrain
    
    print("      Adding geographic features...")
    try:
        add_detailed_coastlines(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)
        add_detailed_borders(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)
        add_major_rivers(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)
        add_major_cities(ax, lon_min, lon_max, lat_min, lat_max, feature_z_level)
        print("      ✓ Geographic features added")
    except Exception as e:
        print(f"      ✗ Some geographic features failed: {e}")

def fix_color_array(terrain_colors):
    """Fix any invalid values in color array that might cause rendering issues"""
    
    # Ensure colors are in valid range [0, 1]
    terrain_colors = np.clip(terrain_colors, 0, 1)
    
    # Check for NaN or inf values
    invalid_mask = ~np.isfinite(terrain_colors)
    if np.any(invalid_mask):
        print(f"      Fixed {np.sum(invalid_mask)} invalid color values")
        # Replace invalid values with ocean blue
        terrain_colors[invalid_mask] = [0.2, 0.4, 0.8, 0.7]
    
    # Ensure alpha channel is reasonable
    if terrain_colors.shape[-1] == 4:  # RGBA
        terrain_colors[:, :, 3] = np.clip(terrain_colors[:, :, 3], 0.3, 0.9)
    
    return terrain_colors

def create_simple_basemap(ax, ds, z_level):
    """Create simple basemap as fallback"""
    
    print("    Creating simple basemap...")
    
    # Get coordinate bounds
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    # Very coarse grid for simplicity
    resolution = 40
    lons = np.linspace(lon_min, lon_max, resolution)
    lats = np.linspace(lat_min, lat_max, resolution)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    
    # Simple flat ocean base well below data
    data_range = abs(z_level) if z_level != 0 else 1.0
    base_z_level = z_level - data_range * 0.5
    z_plane = np.full_like(lon_grid, base_z_level)
    
    # Simple ocean blue
    ax.plot_surface(lon_grid, lat_grid, z_plane,
                   color='lightblue', alpha=0.4,
                   shade=False, linewidth=0, zorder=1)
    
    # Add basic coastlines using our existing function
    try:
        add_detailed_coastlines(ax, lon_min, lon_max, lat_min, lat_max, base_z_level)
        print("      ✓ Basic coastlines added")
    except:
        print("      ✗ Coastlines failed, using minimal features")
        # Add just a few basic lines
        if lon_min <= -74 <= lon_max and lat_min <= 40 <= lat_max:
            ax.plot([-74], [40], [base_z_level], 'ko', markersize=3, alpha=0.7)  # NYC
        if lon_min <= 0 <= lon_max and lat_min <= 51 <= lat_max:
            ax.plot([0], [51], [base_z_level], 'ko', markersize=3, alpha=0.7)   # London
