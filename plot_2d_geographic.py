import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
from color_mapping import generate_stats_text

def safe_pcolormesh_geographic(ax, ds, data_slice, **kwargs):
    """
    Safely create pcolormesh for geographic lat/lon projection
    """
    lon = ds.longitude.values
    lat = ds.latitude.values
    
    # Squeeze out singleton dimensions to get 2D data
    data_2d = data_slice.squeeze()
    
    # Check for valid data
    if not has_valid_data_2d(data_2d):
        # Create a dummy plot for empty data
        return ax.pcolormesh(lon, lat, np.zeros_like(data_2d.values),
                           transform=ccrs.PlateCarree(),
                           shading='nearest', alpha=0.3, **kwargs)
    
    # For geographic projection, use the coordinates directly
    return ax.pcolormesh(lon, lat, data_2d, 
                        transform=ccrs.PlateCarree(),
                        shading='nearest', **kwargs)

def has_valid_data_2d(data_slice):
    """Check if 2D data slice has any valid (non-NaN) values"""
    if data_slice.size == 0:
        return False
    
    valid_data = data_slice.values[~np.isnan(data_slice.values)]
    return len(valid_data) > 0

def create_overview_plot_geographic(ds, var_name, output_dir):
    """Create overview plot for geographic lat/lon projection"""
    var_data = ds[var_name]
    n_levels = len(ds.levels)
    
    # Calculate subplot grid
    cols = min(6, n_levels)
    rows = (n_levels + cols - 1) // cols
    
    fig, axes = plt.subplots(rows, cols, figsize=(4*cols, 2.5*rows),
                            subplot_kw={'projection': ccrs.PlateCarree()})
    
    if n_levels == 1:
        axes = np.array([axes])
    axes = axes.flatten() if axes.ndim > 0 else [axes]
    
    # Global min/max for consistent colorbar - with NaN handling
    all_valid_data = []
    for i in range(n_levels):
        data_slice = var_data.isel(levels=i)
        if has_valid_data_2d(data_slice):
            valid_vals = data_slice.values[~np.isnan(data_slice.values)]
            all_valid_data.extend(valid_vals)
    
    if len(all_valid_data) > 0:
        vmin, vmax = np.percentile(all_valid_data, [2, 98])
    else:
        vmin, vmax = 0, 1  # Default range for all-NaN data
        print(f"    Warning: {var_name} has no valid data across all levels")
    
    plotted_any = False
    last_valid_im = None
    
    for i, lev_val in enumerate(ds.levels.values):
        if i >= len(axes):
            break
            
        ax = axes[i]
        
        # Add geographic features
        ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        ax.add_feature(cfeature.BORDERS, linewidth=0.3, alpha=0.7)
        ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.3)
        ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.3)
        
        # Add gridlines with lat/lon labels
        gl = ax.gridlines(draw_labels=True, dms=False, x_inline=False, y_inline=False,
                         linewidth=0.5, alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        
        data_slice = var_data.isel(levels=i)
        
        # Plot the data
        try:
            im = safe_pcolormesh_geographic(ax, ds, data_slice,
                                          vmin=vmin, vmax=vmax)
            if has_valid_data_2d(data_slice):
                last_valid_im = im
                plotted_any = True
            
            # Add title with data info
            valid_count = np.sum(~np.isnan(data_slice.values))
            total_count = data_slice.size
            ax.set_title(f'Ch {i+1}: {lev_val}\n({valid_count}/{total_count} valid)', fontsize=9)
            
        except Exception as e:
            ax.set_title(f'Ch {i+1}: {lev_val}\n(Error: {str(e)[:20]}...)', fontsize=9)
            print(f"      Error plotting channel {i+1}: {e}")
        
        # Set extent to data bounds
        ax.set_extent([ds.longitude.min(), ds.longitude.max(), 
                      ds.latitude.min(), ds.latitude.max()], 
                     crs=ccrs.PlateCarree())
    
    # Hide unused subplots
    for j in range(i+1, len(axes)):
        axes[j].set_visible(False)
    
    # Add colorbar if we have valid plots
    if plotted_any and last_valid_im is not None:
        plt.tight_layout()
        cbar = fig.colorbar(last_valid_im, ax=axes[:i+1], shrink=0.6, pad=0.02)
        cbar.set_label(f'{var_name}')
    file_name = ds.attrs.get('GranuleID') 
    plt.suptitle(f'{var_name} - All Channels (Geographic Projection) - {file_name}', y=0.98)
    
    # Save
    filename = f'{var_name}_overview_geographic.png'
    plt.savefig(output_dir / filename, dpi=150, bbox_inches='tight')
    plt.close()

def create_detailed_plots_geographic(ds, var_name, output_dir):
    """Create detailed individual plots for geographic projection"""
    var_data = ds[var_name]
    
    detail_dir = output_dir / f'{var_name}_detailed_2d'
    detail_dir.mkdir(exist_ok=True)
    
    for i, lev_val in enumerate(ds.levels.values):
        try:
            data_slice = var_data.isel(levels=i)
            
            # Skip if no valid data
            if not has_valid_data_2d(data_slice):
                print(f"      Skipping detailed 2D plot for channel {i+1} - no valid data")
                continue
            
            fig = plt.figure(figsize=(14, 10))
            ax = plt.axes(projection=ccrs.PlateCarree())
            
            # Add detailed geographic features
            ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
            ax.add_feature(cfeature.BORDERS, linewidth=0.5)
            ax.add_feature(cfeature.OCEAN, color='lightblue', alpha=0.4)
            ax.add_feature(cfeature.LAND, color='lightgray', alpha=0.4)
            ax.add_feature(cfeature.LAKES, color='lightblue', alpha=0.4)
            ax.add_feature(cfeature.RIVERS, linewidth=0.3)
            
            # Add detailed gridlines
            gl = ax.gridlines(draw_labels=True, dms=False, x_inline=False, y_inline=False,
                             linewidth=0.5, alpha=0.7, linestyle='-', color='gray')
            gl.top_labels = False
            gl.right_labels = False
            
            # Plot the data
            im = safe_pcolormesh_geographic(ax, ds, data_slice)
            
            # Set proper extent
            ax.set_extent([ds.longitude.min(), ds.longitude.max(), 
                          ds.latitude.min(), ds.latitude.max()], 
                         crs=ccrs.PlateCarree())
            
            # Colorbar with stats
            cbar = plt.colorbar(im, ax=ax, shrink=0.7, pad=0.05)
            cbar.set_label(f'{var_name}', fontsize=12)
            
            # Add statistics text box
            stats_text = generate_stats_text(data_slice)
            ax.text(0.02, 0.98, stats_text, transform=ax.transAxes,
                    verticalalignment='top', fontsize=10,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.9))
            
            # Add coordinate info
            coord_text = f"""Coordinates:
Lon: {ds.longitude.min().values:.2f}° to {ds.longitude.max().values:.2f}°
Lat: {ds.latitude.min().values:.2f}° to {ds.latitude.max().values:.2f}°
Grid: {len(ds.longitude)} × {len(ds.latitude)}"""
            
            ax.text(0.98, 0.02, coord_text, transform=ax.transAxes,
                    verticalalignment='bottom', horizontalalignment='right', fontsize=9,
                    bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            file_name = ds.attrs.get('GranuleID')
            plt.title(f'{var_name} - Channel {i+1} (Level: {lev_val})\nGeographic Projection (Lat/Lon)\n{file_name}', 
                     fontsize=14, pad=20)
            
            # Save
            filename = f'ch_{i+1:03d}_{var_name}_geographic_2d.png'
            plt.savefig(detail_dir / filename, dpi=200, bbox_inches='tight')
            plt.close()
            
        except Exception as e:
            print(f"      Error creating detailed 2D plot for channel {i+1}: {e}")
            plt.close('all')
            continue
