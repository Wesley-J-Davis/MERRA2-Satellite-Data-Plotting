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
            from basemap_creation import create_flat_map_basemap, add_lat_lon_grid
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
