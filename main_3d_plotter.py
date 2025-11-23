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
        ax.set_
