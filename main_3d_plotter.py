import xarray as xr
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pathlib import Path
import pandas as pd
import glob

# Import our custom modules
from color_mapping import generate_stats_text

def create_3d_plots_with_flat_map(ds, var_name, output_dir):
    """Create 3D surface plots with flat map projected on bottom plane"""
    var_data = ds[var_name]
    
    detail_dir = output_dir / f'{var_name}_3d_flat_map'
    detail_dir.mkdir(exist_ok=True)
    
    # Create meshgrid for 3D plotting
    lon_2d, lat_2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
    
    for i, lev_val in enumerate(ds.levels.values):
        try:
            # Get 2D data slice and squeeze
            data_slice = var_data.isel(levels=i).squeeze()
            
            # Check if data is valid
            if not has_valid_data(data_slice):
                print(f"      Skipping channel {i+1} (level {lev_val}) - no valid data")
                continue
            
            print(f"      Creating 3D plot with flat map for channel {i+1}...")
            
            fig = plt.figure(figsize=(16, 12))
            ax = fig.add_subplot(111, projection='3d')
            
            # Find data range for positioning
            data_min, data_max = get_safe_data_range(data_slice)
            data_range = data_max - data_min
            
            # Position flat map well below the data
            map_z_level = data_min - data_range * 0.3
            
            # FIRST: Create the flat map on the bottom plane
            create_flat_map_basemap(ax, ds, map_z_level)
            add_lat_lon_grid(ax, ds.longitude.min().values, ds.longitude.max().values,
                           ds.latitude.min().values, ds.latitude.max().values, map_z_level)
            
            # SECOND: Create the 3D data surface above the map
            print("        Rendering 3D data surface...")
            surf = ax.plot_surface(lon_2d, lat_2d, data_slice.values,
                                  cmap='viridis', alpha=0.8,  # Semi-transparent to see map below
                                  linewidth=0, antialiased=True,
                                  zorder=10)  # High zorder to be above map
            
            # Set Z limits to show both map and data clearly
            ax.set_zlim(map_z_level - data_range * 0.1, data_max + data_range * 0.1)
            
            # Add colorbar
            cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=20, pad=0.1)
            cbar.set_label(f'{var_name}', fontsize=12)
            
            # Set labels and title
            ax.set_xlabel('Longitude (°)', fontsize=12)
            ax.set_ylabel('Latitude (°)', fontsize=12)
            ax.set_zlabel(f'{var_name}', fontsize=12)
            ax.set_title(f'{var_name} - Channel {i+1} (Level: {lev_val})\n3D Surface with Flat Map Base', 
                         fontsize=14, pad=20)
            
            # Set viewing angle to see both data and map
            ax.view_init(elev=35, azim=45)
            
            # Add statistics box
            stats_text = generate_stats_text(data_slice)
            ax.text2D(0.02, 0.98, stats_text, transform=ax.transAxes,
                      verticalalignment='top', fontsize=10,
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                      zorder=200)
            
            # Add note about the flat map
            ax.text2D(0.02, 0.02, "Flat map projected on bottom plane", 
                      transform=ax.transAxes,
                      fontsize=9, style='italic', alpha=0.7)
            
            # Save
            filename = f'ch_{i+1:03d}_{var_name}_3d_flat_map.png'
            plt.savefig(detail_dir / filename, dpi=200, bbox_inches='tight')
            plt.close()
            
            print(f"        ✓ Saved 3D plot with flat map for channel {i+1}")
            
        except Exception as e:
            print(f"      ✗ Error creating 3D plot for channel {i+1}: {e}")
            import traceback
            traceback.print_exc()
            plt.close('all')
            continue

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
        {'lons': [-9, -5, 0, 5, 10, 15],
         'lats': [43, 45, 50, 54, 57, 60]},
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
            z_coords = np.full_like(filtered_lons, z_level + 0.001)
            
            ax.plot(filtered_lons, filtered_lats, z_coords, 
                   'k-', linewidth=1.5, alpha=0.9, zorder=2)

def add_lat_lon_grid(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add latitude/longitude grid lines to the flat map"""
    
    # Major latitude lines
    lat_lines = np.arange(-90, 91, 30)
    lat_lines = lat_lines[(lat_lines >= lat_min) & (lat_lines <= lat_max)]
    
    for lat in lat_lines:
        lons = np.linspace(lon_min, lon_max, 50)
        lats = np.full_like(lons, lat)
        z_coords = np.full_like(lons, z_level + 0.001)
        ax.plot(lons, lats, z_coords, 'gray', linewidth=0.5, alpha=0.4, zorder=2)
    
    # Major longitude lines  
    lon_lines = np.arange(-180, 181, 60)
    lon_lines = lon_lines[(lon_lines >= lon_min) & (lon_lines <= lon_max)]
    
    for lon in lon_lines:
        lats = np.linspace(lat_min, lat_max, 50)
        lons = np.full_like(lats, lon)
        z_coords = np.full_like(lats, z_level + 0.001)
        ax.plot(lons, lats, z_coords, 'gray', linewidth=0.5, alpha=0.4, zorder=2)

def has_valid_data(data_slice):
    """Check if data slice has any valid (non-NaN) values"""
    if data_slice.size == 0:
        return False
    
    valid_data = data_slice.values[~np.isnan(data_slice.values)]
    return len(valid_data) > 0

def get_safe_data_range(data_slice):
    """Get data range with proper NaN handling"""
    flat_data = data_slice.values.flatten()
    valid_data = flat_data[~np.isnan(flat_data)]
    
    if len(valid_data) == 0:
        return 0.0, 1.0
    
    data_min = np.min(valid_data)
    data_max = np.max(valid_data)
    
    if data_min == data_max:
        if data_min == 0:
            return -0.5, 0.5
        else:
            return data_min * 0.9, data_min * 1.1
    
    return data_min, data_max

def main():
    """Main execution function"""
    print("🌍 3D Satellite Data Plotter with Flat Map Projection")
    print("=" * 60)
    
    # Configuration
    input_pattern = "merra2.*.nc4"
    output_directory = "qc_review_3d_flat_map"
    
    # Find input files
    file_list = glob.glob(input_pattern)
    
    if not file_list:
        print(f"❌ No files found matching pattern: {input_pattern}")
        return
    
    print(f"📁 Found {len(file_list)} files to process:")
    for f in file_list:
        print(f"   - {f}")
    
    print(f"\n🗺️  Creating 3D plots with flat map projection on bottom plane")
    print(f"📊 Output will be saved to: {output_directory}/")
    
    try:
        output_path = Path(output_directory)
        output_path.mkdir(exist_ok=True)
        
        for file_idx, netcdf_file in enumerate(file_list):
            file_path = Path(netcdf_file)
            print(f"\nProcessing {file_idx+1}/{len(file_list)}: {file_path.name}")
            
            try:
                ds = xr.open_dataset(netcdf_file)
                
                file_output_dir = output_path / file_path.stem
                file_output_dir.mkdir(exist_ok=True)
                
                plot_vars = [var for var in ds.data_vars 
                            if all(dim in ds[var].dims for dim in ['latitude', 'longitude', 'levels'])]
                
                for var_name in plot_vars:
                    create_3d_plots_with_flat_map(ds, var_name, file_output_dir)
                
                ds.close()
                
            except Exception as e:
                print(f"  ✗ Error processing {file_path.name}: {e}")
        
        print(f"\n🎉 Processing complete!")
        print(f"📁 All 3D plots with flat maps saved to: {output_directory}/")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
