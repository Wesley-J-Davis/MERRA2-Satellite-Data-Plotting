import xarray as xr
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pathlib import Path
import pandas as pd
import glob

# Import our custom modules
from basemap_creation import create_offline_basemap, create_simple_basemap
from color_mapping import generate_stats_text

def create_3d_plots_offline_natural_earth(ds, var_name, output_dir, use_simple_basemap=False):
    """Create 3D surface plots using our existing realistic basemap modules"""
    var_data = ds[var_name]
    
    detail_dir = output_dir / f'{var_name}_3d_realistic'
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
            
            print(f"      Creating 3D plot for channel {i+1}...")
            
            fig = plt.figure(figsize=(16, 12))
            ax = fig.add_subplot(111, projection='3d')
            
            # Find data range for Z positioning with NaN handling
            data_min, data_max = get_safe_data_range(data_slice)
            data_range = data_max - data_min
            
            # Create basemap FIRST with proper Z separation
            z_offset = data_min - data_range * 0.6  # Good separation
            
            print(f"        Data range: {data_min:.3f} to {data_max:.3f}")
            print(f"        Basemap at: {z_offset:.3f}")
            
            if use_simple_basemap:
                create_simple_basemap(ax, ds, z_offset)
            else:
                create_offline_basemap(ax, ds, z_offset)  # Use our realistic basemap!
            
            # Create the main 3D surface AFTER basemap
            print("        Rendering data surface...")
            surf = ax.plot_surface(lon_2d, lat_2d, data_slice.values,
                                  cmap='viridis', alpha=0.95,
                                  linewidth=0, antialiased=True,
                                  zorder=100)  # High zorder to ensure it's on top
            
            # Set Z limits with good margins
            ax.set_zlim(z_offset - data_range * 0.1, data_max + data_range * 0.15)
            
            # Add colorbar
            cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=20, pad=0.1)
            cbar.set_label(f'{var_name}', fontsize=12)
            
            # Set labels and title
            ax.set_xlabel('Longitude (°)', fontsize=12)
            ax.set_ylabel('Latitude (°)', fontsize=12)
            ax.set_zlabel(f'{var_name}', fontsize=12)
            
            basemap_type = "Simple" if use_simple_basemap else "Realistic"
            ax.set_title(f'{var_name} - Channel {i+1} (Level: {lev_val})\n3D with {basemap_type} Basemap', 
                         fontsize=14, pad=20)
            
            # Set viewing angle for best basemap visibility
            ax.view_init(elev=25, azim=45)
            
            # Add statistics box
            stats_text = generate_stats_text(data_slice)
            ax.text2D(0.02, 0.98, stats_text, transform=ax.transAxes,
                      verticalalignment='top', fontsize=10,
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                      zorder=200)
            
            # Save
            basemap_suffix = "simple" if use_simple_basemap else "realistic"
            filename = f'ch_{i+1:03d}_{var_name}_3d_{basemap_suffix}.png'
            plt.savefig(detail_dir / filename, dpi=200, bbox_inches='tight')
            plt.close()
            
            print(f"        ✓ Saved 3D plot for channel {i+1}")
            
        except Exception as e:
            print(f"      ✗ Error creating 3D plot for channel {i+1}: {e}")
            import traceback
            traceback.print_exc()
            plt.close('all')
            continue

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

def comprehensive_qc_viewer_offline_ne(file_list, output_dir='qc_review_realistic', 
                                      use_realistic_basemap=True):
    """Main function using our existing realistic terrain modules"""
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    for file_idx, netcdf_file in enumerate(file_list):
        file_path = Path(netcdf_file)
        print(f"\nProcessing {file_idx+1}/{len(file_list)}: {file_path.name}")
        
        try:
            ds = xr.open_dataset(netcdf_file)
            
            # Verify coordinate ranges
            print(f"  Coordinate ranges:")
            print(f"    Longitude: {ds.longitude.min().values:.2f}° to {ds.longitude.max().values:.2f}°")
            print(f"    Latitude: {ds.latitude.min().values:.2f}° to {ds.latitude.max().values:.2f}°")
            
            # Create subdirectory for this file
            file_output_dir = output_path / file_path.stem
            file_output_dir.mkdir(exist_ok=True)
            
            # Get variables with latitude/longitude/levels dimensions
            plot_vars = [var for var in ds.data_vars 
                        if all(dim in ds[var].dims for dim in ['latitude', 'longitude', 'levels'])]
            
            print(f"  Variables to plot: {plot_vars}")
            
            for var_name in plot_vars:
                print(f"    Processing {var_name}...")
                
                # Check if variable has any valid data across all levels
                var_data = ds[var_name]
                total_valid = np.sum(~np.isnan(var_data.values))
                total_points = var_data.size
                
                if total_valid == 0:
                    print(f"      Skipping {var_name} - no valid data in any channel")
                    continue
                
                print(f"      Data coverage: {total_valid:,} / {total_points:,} points ({100*total_valid/total_points:.1f}%)")
                
                # Create realistic 3D plots using our existing modules
                create_3d_plots_offline_natural_earth(ds, var_name, file_output_dir, 
                                                     use_simple_basemap=not use_realistic_basemap)
            
            ds.close()
            print(f"  ✓ 3D plots saved to {file_output_dir}")
            
        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main execution function"""
    print("🌍 3D Satellite Data Plotter with Realistic Terrain")
    print("=" * 60)
    print("Using existing terrain_generation, color_mapping, and geographic_features modules")
    print()
    
    # Configuration
    input_pattern = "merra2.*.nc4"
    output_directory = "qc_review_realistic_terrain"
    use_realistic_basemap = True  # Use our detailed terrain modules!
    
    # Find input files
    file_list = glob.glob(input_pattern)
    
    if not file_list:
        print(f"❌ No files found matching pattern: {input_pattern}")
        return
    
    print(f"📁 Found {len(file_list)} files to process:")
    for f in file_list:
        print(f"   - {f}")
    
    basemap_type = "realistic terrain with mountains, coastlines, and rivers" if use_realistic_basemap else "simple"
    print(f"\n🗺️  Using {basemap_type}")
    print(f"📊 Output will be saved to: {output_directory}/")
    
    try:
        comprehensive_qc_viewer_offline_ne(file_list, 
                                         output_dir=output_directory,
                                         use_realistic_basemap=use_realistic_basemap)
        
        print(f"\n🎉 Processing complete!")
        print(f"📁 All realistic 3D plots saved to: {output_directory}/")
        print(f"\n✨ Your plots now include:")
        print(f"   • Realistic topographic terrain")
        print(f"   • Major mountain ranges (Rockies, Himalayas, Andes, Alps, etc.)")
        print(f"   • Detailed coastlines")
        print(f"   • Political borders")
        print(f"   • Major rivers and cities")
        print(f"   • Ocean depth variations")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
