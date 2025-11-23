import xarray as xr
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pathlib import Path
import pandas as pd
import glob

# Import our custom modules
from basemap_creation import create_offline_basemap
from color_mapping import generate_stats_text

def create_3d_plots_offline_natural_earth(ds, var_name, output_dir):
    """Create 3D surface plots using offline Natural Earth features"""
    var_data = ds[var_name]
    
    detail_dir = output_dir / f'{var_name}_3d_offline_ne'
    detail_dir.mkdir(exist_ok=True)
    
    # Create meshgrid for 3D plotting
    lon_2d, lat_2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
    
    for i, lev_val in enumerate(ds.levels.values):
        fig = plt.figure(figsize=(16, 12))
        ax = fig.add_subplot(111, projection='3d')
        
        # Get 2D data slice and squeeze
        data_slice = var_data.isel(levels=i).squeeze()
        
        # Find data range for Z positioning
        data_min = np.nanmin(data_slice.values)
        data_max = np.nanmax(data_slice.values)
        z_offset = data_min - (data_max - data_min) * 0.15
        
        # Create the main 3D surface
        surf = ax.plot_surface(lon_2d, lat_2d, data_slice.values,
                              cmap='viridis', alpha=0.85,
                              linewidth=0, antialiased=True)
        
        # Create offline Natural Earth basemap
        create_offline_basemap(ax, ds, z_offset)
        
        # Add colorbar
        cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=20, pad=0.1)
        cbar.set_label(f'{var_name}', fontsize=12)
        
        # Set labels and title
        ax.set_xlabel('Longitude (°)', fontsize=12)
        ax.set_ylabel('Latitude (°)', fontsize=12)
        ax.set_zlabel(f'{var_name}', fontsize=12)
        ax.set_title(f'{var_name} - Channel {i+1} (Level: {lev_val})\n3D with Offline Natural Earth', 
                     fontsize=14, pad=20)
        
        # Set viewing angle and limits
        ax.view_init(elev=35, azim=45)
        ax.set_zlim(z_offset, data_max * 1.1)
        
        # Add statistics
        stats_text = generate_stats_text(data_slice)
        ax.text2D(0.02, 0.98, stats_text, transform=ax.transAxes,
                  verticalalignment='top', fontsize=10,
                  bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
        
        # Save
        filename = f'ch_{i+1:03d}_{var_name}_3d_offline_ne.png'
        plt.savefig(detail_dir / filename, dpi=200, bbox_inches='tight')
        plt.close()

def comprehensive_qc_viewer_offline_ne(file_list, output_dir='qc_review_offline_ne'):
    """Main function using offline Natural Earth-style features"""
    
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
                print(f"    Creating 3D plots for {var_name}...")
                create_3d_plots_offline_natural_earth(ds, var_name, file_output_dir)
            
            ds.close()
            print(f"  ✓ 3D plots saved to {file_output_dir}")
            
        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {e}")
            import traceback
            traceback.print_exc()

def main():
    """Main execution function"""
    print("🌍 3D Satellite Data Plotter with Realistic Basemaps")
    print("=" * 60)
    
    # Configuration
    input_pattern = "merra2.mhs_metop-*.nc4"  # Modify this pattern as needed
    output_directory = "qc_review_3d_realistic"
    
    # Find input files
    file_list = glob.glob(input_pattern)
    
    if not file_list:
        print(f"❌ No files found matching pattern: {input_pattern}")
        print("Please check your file pattern and current directory.")
        return
    
    print(f"📁 Found {len(file_list)} files to process:")
    for f in file_list:
        print(f"   - {f}")
    
    print(f"\n📊 Output will be saved to: {output_directory}/")
    
    # Process files
    try:
        comprehensive_qc_viewer_offline_ne(file_list, output_dir=output_directory)
        
        print(f"\n🎉 Processing complete!")
        print(f"📁 All 3D plots saved to: {output_directory}/")
        print(f"\n📋 Next steps:")
        print(f"   1. Navigate to {output_directory}/")
        print(f"   2. Review the 3D visualizations for each variable and channel")
        print(f"   3. Look for data quality issues, anomalies, or patterns")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
