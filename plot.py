import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from pathlib import Path
import pandas as pd

def comprehensive_qc_viewer(file_list, output_dir='qc_review'):
    """
    Create systematic QC plots for human review of all products
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
            
            # Create subdirectory for this file
            file_output_dir = output_path / file_path.stem
            file_output_dir.mkdir(exist_ok=True)
            
            # Get variables with lat/lon/lev dimensions
            plot_vars = [var for var in ds.data_vars 
                        if all(dim in ds[var].dims for dim in ['lat', 'lon', 'lev'])]
            
            for var_name in plot_vars:
                var_data = ds[var_name]
                
                # Create overview plot (all channels in one figure)
                create_overview_plot(ds, var_name, file_output_dir)
                
                # Create individual channel plots for detailed inspection
                create_detailed_plots(ds, var_name, file_output_dir)
                
                # Generate statistics summary
                stats = generate_stats_summary(var_data, var_name)
                qc_log.append({
                    'file': file_path.name,
                    'variable': var_name,
                    **stats
                })
            
            ds.close()
            print(f"  ✓ Plots saved to {file_output_dir}")
            
        except Exception as e:
            print(f"  ✗ Error processing {file_path.name}: {e}")
            qc_log.append({
                'file': file_path.name,
                'variable': 'ERROR',
                'error': str(e)
            })
    
    # Save QC summary log
    qc_df = pd.DataFrame(qc_log)
    qc_df.to_csv(output_path / 'qc_summary.csv', index=False)
    
    # Create QC checklist
    create_qc_checklist(file_list, output_path)
    
    print(f"\n🎯 QC Review Complete!")
    print(f"📁 All plots saved to: {output_path}")
    print(f"📊 Summary log: {output_path}/qc_summary.csv")
    print(f"📋 Checklist: {output_path}/qc_checklist.html")

def create_overview_plot(ds, var_name, output_dir):
    """Create overview plot showing all channels"""
    var_data = ds[var_name]
    n_levels = len(ds.lev)
    
    # Calculate subplot grid
    cols = min(6, n_levels)
    rows = (n_levels + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(3*cols, 2.5*rows),
                            subplot_kw={'projection': ccrs.PlateCarree()})
    
    if n_levels == 1:
        axes = np.array([axes])
    axes = axes.flatten() if axes.ndim > 0 else [axes]
    
    # Global min/max for consistent colorbar
    vmin, vmax = np.nanpercentile(var_data.values, [2, 98])
    
    for i, lev_val in enumerate(ds.lev.values):
        if i >= len(axes):
            break
            
        ax = axes[i]
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.5)
        
        data_slice = var_data.isel(lev=i)
        
        im = ax.pcolormesh(ds.lon, ds.lat, data_slice,
                          transform=ccrs.PlateCarree(),
                          vmin=vmin, vmax=vmax, shading='auto')
        
        ax.set_title(f'Ch {i+1}: {lev_val}', fontsize=10)
        ax.set_global()
    
    # Hide unused subplots
    for j in range(i+1, len(axes)):
        axes[j].set_visible(False)
    
    # Add single colorbar
    plt.tight_layout()
    cbar = fig.colorbar(im, ax=axes[:i+1], shrink=0.6, pad=0.02)
    cbar.set_label(f'{var_name}')
    
    plt.suptitle(f'{var_name} - All Channels Overview', y=0.98)
    
    # Save
    filename = f'{var_name}_overview.png'
    plt.savefig(output_dir / filename, dpi=150, bbox_inches='tight')
    plt.close()

def create_detailed_plots(ds, var_name, output_dir):
    """Create detailed individual plots for each channel"""
    var_data = ds[var_name]
    
    detail_dir = output_dir / f'{var_name}_detailed'
    detail_dir.mkdir(exist_ok=True)
    
    for i, lev_val in enumerate(ds.lev.values):
        fig = plt.figure(figsize=(12, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        
        # Add map features
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS)
        ax.add_feature(cfeature.OCEAN, alpha=0.3)
        ax.add_feature(cfeature.LAND, alpha=0.3)
        ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False)
        
        data_slice = var_data.isel(lev=i)
        
        # Plot with automatic scaling
        im = ax.pcolormesh(ds.lon, ds.lat, data_slice,
                          transform=ccrs.PlateCarree(), shading='auto')
        
        # Colorbar with stats
        cbar = plt.colorbar(im, ax=ax, shrink=0.7)
        cbar.set_label(f'{var_name}')
        
        # Add statistics text box
        stats_text = generate_stats_text(data_slice)
        ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                verticalalignment='top', bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
        
        plt.title(f'{var_name} - Channel {i+1} (Level: {lev_val})')
        
        # Save
        filename = f'ch_{i+1:03d}_{var_name}.png'
        plt.savefig(detail_dir / filename, dpi=150, bbox_inches='tight')
        plt.close()

def generate_stats_summary(data, var_name):
    """Generate numerical statistics for QC log"""
    flat_data = data.values.flatten()
    valid_data = flat_data[~np.isnan(flat_data)]
    
    return {
        'min': np.min(valid_data) if len(valid_data) > 0 else np.nan,
        'max': np.max(valid_data) if len(valid_data) > 0 else np.nan,
        'mean': np.mean(valid_data) if len(valid_data) > 0 else np.nan,
        'std': np.std(valid_data) if len(valid_data) > 0 else np.nan,
        'n_valid': len(valid_data),
        'n_total': len(flat_data),
        'pct_valid': len(valid_data) / len(flat_data) * 100 if len(flat_data) > 0 else 0
    }

def generate_stats_text(data_slice):
    """Generate stats text for plot annotation"""
    flat_data = data_slice.values.flatten()
    valid_data = flat_data[~np.isnan(flat_data)]
    
    if len(valid_data) == 0:
        return "No valid data"
    
    stats = f"""Statistics:
Min: {np.min(valid_data):.3f}
Max: {np.max(valid_data):.3f}
Mean: {np.mean(valid_data):.3f}
Std: {np.std(valid_data):.3f}
Valid: {len(valid_data):,} / {len(flat_data):,}
({len(valid_data)/len(flat_data)*100:.1f}%)"""
    
    return stats

def create_qc_checklist(file_list, output_dir):
    """Create an HTML checklist for QC tracking"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>QC Review Checklist</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .file-block {{ border: 1px solid #ccc; margin: 10px 0; padding: 10px; }}
            .approved {{ background-color: #d4edda; }}
            .rejected {{ background-color: #f8d7da; }}
            input[type="checkbox"] {{ margin-right: 10px; }}
            .timestamp {{ font-size: 0.9em; color: #666; }}
        </style>
    </head>
    <body>
        <h1>Quality Control Review Checklist</h1>
        <p>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Instructions:</strong> Review each product's plots and check the appropriate box.</p>
    """
    
    for i, file_path in enumerate(file_list):
        file_name = Path(file_path).name
        html_content += f"""
        <div class="file-block" id="file_{i}">
            <h3>{file_name}</h3>
            <label><input type="checkbox" name="approved_{i}" onclick="markApproved({i})"> ✅ APPROVED for release</label><br>
            <label><input type="checkbox" name="rejected_{i}" onclick="markRejected({i})"> ❌ REJECTED - needs revision</label><br>
            <textarea placeholder="Notes/Issues:" style="width: 100%; margin-top: 5px;" rows="2"></textarea>
            <div class="timestamp" id="timestamp_{i}"></div>
        </div>
        """
    
    html_content += """
        <script>
        function markApproved(i) {
            document.getElementById('file_' + i).className = 'file-block approved';
            document.querySelector('input[name="rejected_' + i + '"]').checked = false;
            document.getElementById('timestamp_' + i).innerHTML = 'Approved: ' + new Date().toLocaleString();
        }
        function markRejected(i) {
            document.getElementById('file_' + i).className = 'file-block rejected';
            document.querySelector('input[name="approved_' + i + '"]').checked = false;
            document.getElementById('timestamp_' + i).innerHTML = 'Rejected: ' + new Date().toLocaleString();
        }
        </script>
    </body>
    </html>
    """
    
    with open(output_dir / 'qc_checklist.html', 'w') as f:
        f.write(html_content)

# Usage example:
if __name__ == "__main__":
    # List all your NetCDF files
    import glob
    
    file_list = glob.glob("path/to/your/files/*.nc")
    
    comprehensive_qc_viewer(file_list, output_dir='human_qc_review')
