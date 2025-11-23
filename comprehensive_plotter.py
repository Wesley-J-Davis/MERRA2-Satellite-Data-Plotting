import xarray as xr
from pathlib import Path
import pandas as pd

# Import 2D plotting functions
from plot_2d_geographic import create_overview_plot_geographic, create_detailed_plots_geographic

# Import 3D plotting functions  
from main_3d_plotter import create_3d_plots_offline_natural_earth

# Import QC utilities
from qc_utilities import generate_stats_summary, create_qc_checklist

def create_comprehensive_plots(ds, var_name, output_dir):
    """Create both 2D and 3D plots for a variable"""
    print(f"      Creating 2D overview plot...")
    create_overview_plot_geographic(ds, var_name, output_dir)
    
    print(f"      Creating detailed 2D plots...")
    create_detailed_plots_geographic(ds, var_name, output_dir)
    
    print(f"      Creating 3D plots with basemaps...")
    create_3d_plots_offline_natural_earth(ds, var_name, output_dir)

def comprehensive_qc_viewer(file_list, output_dir='comprehensive_qc_review'):
    """
    Create comprehensive QC plots (both 2D and 3D) for all files
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # Create QC log
    qc_log = []
    
    for file_idx, netcdf_file in enumerate(file_list):
        file_path = Path(netcdf_file)
        print(f"\nProcessing {file_idx+1}/{len(file_list)}: {file_path.name}")
        
        try:
            ds = xr.open_dataset(netcdf_file)
            
            # Verify coordinate ranges
            print(f"  Coordinate ranges:")
            print(f"    Longitude: {ds.longitude.min().values:.2f}° to {ds.longitude.max().values:.2f}°")
            print(f"    Latitude: {ds.latitude.min().values:.2f}° to {ds.latitude.max().values:.2f}°")
            print(f"    Levels: {len(ds.levels)} channels")
            
            # Create subdirectory for this file
            file_output_dir = output_path / file_path.stem
            file_output_dir.mkdir(exist_ok=True)
            
            # Get variables with latitude/longitude/levels dimensions
            plot_vars = [var for var in ds.data_vars 
                        if all(dim in ds[var].dims for dim in ['latitude', 'longitude', 'levels'])]
            
            print(f"  Variables to plot: {plot_vars}")
            
            for var_name in plot_vars:
                print(f"    Processing {var_name}...")
                var_data = ds[var_name]
                
                # Create comprehensive plots
                create_comprehensive_plots(ds, var_name, file_output_dir)
                
                # Generate statistics summary
                stats = generate_stats_summary(var_data, var_name)
                qc_log.append({
                    'file': file_path.name,
                    'variable': var_name,
                    **stats
                })
            
            ds.close()
            print(f"  ✓ All plots saved to {file_output_dir}")
            
        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {e}")
            qc_log.append({
                'file': file_path.name,
                'variable': 'ERROR',
                'error': str(e)
            })
            import traceback
            traceback.print_exc()
    
    # Save QC summary log
    qc_df = pd.DataFrame(qc_log)
    qc_df.to_csv(output_path / 'qc_summary_comprehensive.csv', index=False)
    
    # Create comprehensive QC checklist
    create_qc_checklist(file_list, output_path)
    
    print(f"\n🎯 Comprehensive QC Review Complete!")
    print(f"📁 All plots saved to: {output_path}")
    print(f"📊 Summary log: {output_path}/qc_summary_comprehensive.csv")
    print(f"📋 QC Checklist: {output_path}/qc_checklist.html")
    
    print(f"\n📋 Generated visualizations per variable:")
    print(f"   • 2D Overview: All channels in one plot")
    print(f"   • 2D Detailed: Individual high-resolution plots per channel")
    print(f"   • 3D Realistic: 3D surface plots with detailed basemaps")
    
    return output_path
