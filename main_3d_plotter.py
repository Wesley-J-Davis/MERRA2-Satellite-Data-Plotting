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
    """Create 3D surface plots with clean flat map projected on bottom plane"""
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
            
            print(f"      Creating 3D plot with clean flat map for channel {i+1}...")
            
            fig = plt.figure(figsize=(16, 12))
            ax = fig.add_subplot(111, projection='3d')
            
            # Find data range for positioning
            data_min, data_max = get_safe_data_range(data_slice)
            data_range = data_max - data_min
            
            # Position flat map well below the data
            map_z_level = data_min - data_range * 0.4
            
            # FIRST: Create clean flat map on bottom plane
            create_clean_flat_map(ax, ds, map_z_level)
            
            # SECOND: Create the 3D data surface above the map
            print("        Rendering 3D data surface...")
            surf = ax.plot_surface(lon_2d, lat_2d, data_slice.values,
                                  cmap='viridis', alpha=0.85,  # Semi-transparent to see map below
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
            ax.set_title(f'{var_name} - Channel {i+1} (Level: {lev_val})\n3D Surface with Geographic Base Map', 
                         fontsize=14, pad=20)
            
            # Set viewing angle to see both data and map
            ax.view_init(elev=30, azim=45)
            
            # Add statistics box
            stats_text = generate_stats_text(data_slice)
            ax.text2D(0.02, 0.98, stats_text, transform=ax.transAxes,
                      verticalalignment='top', fontsize=10,
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                      zorder=200)
            
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

def create_clean_flat_map(ax, ds, z_level):
    """Create a clean flat map projection on the bottom plane"""
    
    print("    Creating clean flat map projection...")
    
    # Get coordinate bounds
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    # Create a smooth ocean base first
    create_ocean_base(ax, lon_min, lon_max, lat_min, lat_max, z_level)
    
    # Add continental outlines
    add_continental_shapes(ax, lon_min, lon_max, lat_min, lat_max, z_level)
    
    # Add coastlines and borders
    add_geographic_lines(ax, lon_min, lon_max, lat_min, lat_max, z_level)
    
    # Add coordinate grid
    add_coordinate_grid(ax, lon_min, lon_max, lat_min, lat_max, z_level)

def create_ocean_base(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Create smooth ocean base"""
    
    # Create a simple grid for the ocean base
    ocean_lons = np.array([lon_min, lon_max, lon_max, lon_min, lon_min])
    ocean_lats = np.array([lat_min, lat_min, lat_max, lat_max, lat_min])
    ocean_z = np.full_like(ocean_lons, z_level)
    
    # Plot ocean as a simple rectangle
    ax.plot_surface(np.array([[lon_min, lon_max], [lon_min, lon_max]]),
                   np.array([[lat_min, lat_min], [lat_max, lat_max]]),
                   np.array([[z_level, z_level], [z_level, z_level]]),
                   color='lightblue', alpha=0.6, shade=False, zorder=1)

def add_continental_shapes(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add simplified continental shapes as filled areas"""
    
    # Define major continental regions with approximate boundaries
    continents = [
        {
            'name': 'North America',
            'bounds': (-170, -50, 15, 75),
            'color': 'lightgreen',
            'alpha': 0.7
        },
        {
            'name': 'South America', 
            'bounds': (-85, -30, -60, 15),
            'color': 'lightgreen',
            'alpha': 0.7
        },
        {
            'name': 'Europe',
            'bounds': (-15, 50, 35, 75),
            'color': 'wheat',
            'alpha': 0.7
        },
        {
            'name': 'Africa',
            'bounds': (-20, 55, -40, 40),
            'color': 'sandybrown', 
            'alpha': 0.7
        },
        {
            'name': 'Asia',
            'bounds': (30, 180, 10, 80),
            'color': 'tan',
            'alpha': 0.7
        },
        {
            'name': 'Australia',
            'bounds': (110, 160, -45, -10),
            'color': 'orange',
            'alpha': 0.7
        }
    ]
    
    for continent in continents:
        c_lon_min, c_lon_max, c_lat_min, c_lat_max = continent['bounds']
        
        # Check if continent intersects with our domain
        if (c_lon_max >= lon_min and c_lon_min <= lon_max and
            c_lat_max >= lat_min and c_lat_min <= lat_max):
            
            # Clip to our domain
            plot_lon_min = max(c_lon_min, lon_min)
            plot_lon_max = min(c_lon_max, lon_max)
            plot_lat_min = max(c_lat_min, lat_min)
            plot_lat_max = min(c_lat_max, lat_max)
            
            # Create continent rectangle
            cont_lons = np.array([[plot_lon_min, plot_lon_max], 
                                 [plot_lon_min, plot_lon_max]])
            cont_lats = np.array([[plot_lat_min, plot_lat_min], 
                                 [plot_lat_max, plot_lat_max]])
            cont_z = np.full_like(cont_lons, z_level + 0.001)
            
            ax.plot_surface(cont_lons, cont_lats, cont_z,
                           color=continent['color'], 
                           alpha=continent['alpha'],
                           shade=False, zorder=2)

def add_geographic_lines(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add coastlines, borders, and other geographic lines"""
    
    # Major coastlines as simple line segments
    coastlines = [
        # US East Coast
        {'lons': [-81, -75, -70], 'lats': [25, 40, 45], 'color': 'black', 'width': 1.5},
        # US West Coast  
        {'lons': [-125, -120, -115], 'lats': [30, 40, 50], 'color': 'black', 'width': 1.5},
        # European Coast
        {'lons': [-10, 0, 10], 'lats': [40, 50, 60], 'color': 'black', 'width': 1.5},
        # Mediterranean
        {'lons': [0, 10, 20, 30], 'lats': [35, 38, 35, 35], 'color': 'blue', 'width': 1.0},
    ]
    
    for line in coastlines:
        lons = np.array(line['lons'])
        lats = np.array(line['lats'])
        
        # Filter to domain
        mask = ((lons >= lon_min) & (lons <= lon_max) & 
               (lats >= lat_min) & (lats <= lat_max))
        
        if np.sum(mask) >= 2:  # Need at least 2 points for a line
            filtered_lons = lons[mask]
            filtered_lats = lats[mask]
            z_coords = np.full_like(filtered_lons, z_level + 0.002)
            
            ax.plot(filtered_lons, filtered_lats, z_coords,
                   color=line['color'], linewidth=line['width'], 
                   alpha=0.8, zorder=3)
    
    # Political borders
    borders = [
        # US-Canada
        {'lons': [-141, -95], 'lats': [49, 49], 'color': 'red', 'style': '--'},
        # US-Mexico
        {'lons': [-117, -97], 'lats': [32.5, 25.8], 'color': 'red', 'style': '--'},
    ]
    
    for border in borders:
        lons = np.array(border['lons'])
        lats = np.array(border['lats'])
        
        mask = ((lons >= lon_min) & (lons <= lon_max) & 
               (lats >= lat_min) & (lats <= lat_max))
        
        if np.any(mask):
            filtered_lons = lons[mask]
            filtered_lats = lats[mask]
            z_coords = np.full_like(filtered_lons, z_level + 0.002)
            
            ax.plot(filtered_lons, filtered_lats, z_coords,
                   color=border['color'], linestyle=border['style'], 
                   linewidth=1.0, alpha=0.7, zorder=3)

def add_coordinate_grid(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add lat/lon coordinate grid"""
    
    # Longitude lines (meridians)
    lon_spacing = 30 if (lon_max - lon_min) > 60 else 15
    lon_lines = np.arange(-180, 181, lon_spacing)
    lon_lines = lon_lines[(lon_lines >= lon_min) & (lon_lines <= lon_max)]
    
    for lon in lon_lines:
        lats = np.linspace(lat_min, lat_max, 50)
        lons = np.full_like(lats, lon)
        z_coords = np.full_like(lats, z_level + 0.001)
        ax.plot(lons, lats, z_coords, 'gray', linewidth=0.5, alpha=0.5, zorder=2)
    
    # Latitude lines (parallels)
    lat_spacing = 30 if (lat_max - lat_min) > 60 else 15  
    lat_lines = np.arange(-90, 91, lat_spacing)
    lat_lines = lat_lines[(lat_lines >= lat_min) & (lat_lines <= lat_max)]
    
    for lat in lat_lines:
        lons = np.linspace(lon_min, lon_max, 50)
        lats = np.full_like(lons, lat)
        z_coords = np.full_like(lons, z_level + 0.001)
        ax.plot(lons, lats, z_coords, 'gray', linewidth=0.5, alpha=0.5, zorder=2)

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
    print("🌍 3D Satellite Data Plotter with Clean Flat Map Base")
    print("=" * 60)
    
    # Configuration
    input_pattern = "merra2.*.nc4"
    output_directory = "qc_review_3d_clean_map"
    
    # Find input files
    file_list = glob.glob(input_pattern)
    
    if not file_list:
        print(f"❌ No files found matching pattern: {input_pattern}")
        return
    
    print(f"📁 Found {len(file_list)} files to process:")
    for f in file_list:
        print(f"   - {f}")
    
    print(f"\n🗺️  Creating 3D plots with clean geographic base map")
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
                    var_data = ds[var_name]
                    total_valid = np.sum(~np.isnan(var_data.values))
                    
                    if total_valid > 0:
                        create_3d_plots_with_flat_map(ds, var_name, file_output_dir)
                
                ds.close()
                
            except Exception as e:
                print(f"  ✗ Error processing {file_path.name}: {e}")
        
        print(f"\n🎉 Processing complete!")
        print(f"📁 Clean 3D plots with geographic base saved to: {output_directory}/")
        print(f"\n✨ Features include:")
        print(f"   • Light blue ocean base")
        print(f"   • Continental shapes in different colors")
        print(f"   • Major coastlines and political borders")
        print(f"   • Coordinate grid (lat/lon lines)")
        print(f"   • Your satellite data as transparent 3D surface above")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
