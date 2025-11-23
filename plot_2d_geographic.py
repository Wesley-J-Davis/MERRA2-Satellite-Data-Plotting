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
    
    # For geographic projection, use the coordinates directly
    return ax.pcolormesh(lon, lat, data_2d, 
                        transform=ccrs.PlateCarree(),
                        shading='nearest', **kwargs)

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
    
    # Global min/max for consistent colorbar
    vmin, vmax = np.nanpercentile(var_data.values, [2, 98])
    
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
        im = safe_pcolormesh_geographic(ax, ds, data_slice,
                                      vmin=vmin, vmax=vmax)
        
        ax.set_title(f'Ch {i+1}: {lev_val}', fontsize=10)
        
        # Set extent to data bounds
        ax.set_extent([ds.longitude.min(), ds.longitude.max(), 
                      ds.latitude.min(), ds.latitude.max()], 
                     crs=ccrs.PlateCarree())
    
    # Hide unused subplots
    for j in range(i+1, len(axes)):
        axes[j].set_visible(False)
    
    # Add single colorbar
    plt.tight_layout()
    cbar = fig.colorbar(im, ax=axes[:i+1], shrink=0.6, pad=0.02)
    cbar.set_label(f'{var_name}')
    
    plt.suptitle(f'{var_name} - All Channels (Geographic Projection)', y=0.98)
    
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
        
        data_slice = var_data.isel(levels=i)
        
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
        
        plt.title(f'{var_name} - Channel {i+1} (Level: {lev_val})\nGeographic Projection (Lat/Lon)', 
                 fontsize=14, pad=20)
        
        # Save
        filename = f'ch_{i+1:03d}_{var_name}_geographic_2d.png'
        plt.savefig(detail_dir / filename, dpi=200, bbox_inches='tight')
        plt.close()
