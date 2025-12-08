import xarray as xr
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np
from pathlib import Path
import pandas as pd
import glob
import cartopy.crs as ccrs
import cartopy.feature as cfeature
from matplotlib.ticker import MaxNLocator

# Import our custom modules
from color_mapping import generate_stats_text

def create_3d_plots_with_cartopy_wireframe(ds, var_name, output_dir):
    """Create 3D surface plots with Cartopy coastlines wireframe on bottom plane"""
    var_data = ds[var_name]
    
    detail_dir = output_dir / f'{var_name}_3d_coastlines'
    detail_dir.mkdir(exist_ok=True)
    
    # Create meshgrid for 3D plotting - NORMAL ORIENTATION
    lon_2d, lat_2d = np.meshgrid(ds.longitude.values, ds.latitude.values)
    
    # Extract date information from global attributes
    date_info = extract_date_info(ds)
    
    for i, lev_val in enumerate(ds.levels.values):
        try:
            # Get 2D data slice and squeeze - NORMAL ORIENTATION
            data_slice = var_data.isel(levels=i).squeeze()
            data_slice_normal = data_slice.values
            
            # Check if data is valid
            if not has_valid_data_array(data_slice_normal):
                print(f"      Skipping channel {i+1} (level {lev_val}) - no valid data")
                continue
            
            print(f"      Creating 3D plot with coastlines for channel {i+1}...")
            
            fig = plt.figure(figsize=(16, 12))
            ax = fig.add_subplot(111, projection='3d')
            
            # Find data range for positioning
            data_min, data_max = get_safe_data_range_array(data_slice_normal)
            data_range = data_max - data_min
            
            # Position wireframe map well below the data
            map_z_level = data_min - data_range * 0.4
            
            # FIRST: Create coastlines wireframe on bottom plane
            create_coastlines_basemap(ax, ds, map_z_level)
            
            # SECOND: Create the 3D data surface above the wireframe
            print("        Rendering 3D data surface...")
            surf = ax.plot_surface(lon_2d, lat_2d, data_slice_normal,
                                  cmap='viridis', alpha=0.85,
                                  linewidth=0, antialiased=True,
                                  zorder=10)  # High zorder to be above wireframe

           
            # Set Z limits to show both wireframe and data clearly
            z_padding = data_range * 0.3
            ax.set_zlim(map_z_level - z_padding, data_max + z_padding)
            ax.zaxis.set_major_locator(MaxNLocator(nbins=6))  # Limit to 6 tick marks maximum
            ax.tick_params(axis='z', labelsize=10, pad=8)  # Bigger font, more padding

            # Adjust subplot positioning
            plt.subplots_adjust(left=0.1, right=0.95, top=0.9, bottom=0.1)
            
            # Add colorbar
            cbar = fig.colorbar(surf, ax=ax, shrink=0.5, aspect=20, pad=0.1)
            cbar.set_label(f'{var_name}', fontsize=12)
            
            # Set labels and title with date information
            ax.set_xlabel('Longitude (°)', fontsize=12)
            ax.set_ylabel('Latitude (°)', fontsize=12)
            ax.set_zlabel(f'{var_name}', fontsize=12)
            
            # Create title with date information
            title = f'{var_name} - Channel {i+1} (Level: {lev_val})\n3D Surface with Coastlines\n{date_info}'
            ax.set_title(title, fontsize=14, pad=20)
            
            # Set viewing angle to see both data and wireframe
            ax.view_init(elev=77, azim=225)
            
            # Add statistics box
            stats_text = generate_stats_text_array(data_slice_normal)
            ax.text2D(0.02, 0.98, stats_text, transform=ax.transAxes,
                      verticalalignment='top', fontsize=10,
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.9),
                      zorder=200)

            # Add coordinate info
            coord_text = f"Lat: {ds.latitude.min().values:.1f}° to {ds.latitude.max().values:.1f}°\nLon: {ds.longitude.min().values:.1f}° to {ds.longitude.max().values:.1f}°"
            ax.text2D(0.98, 0.02, coord_text, transform=ax.transAxes,
                      verticalalignment='bottom', horizontalalignment='right', fontsize=9,
                      bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
            
            # Save
            filename = f'ch_{i+1:03d}_{var_name}_3d_coastlines.png'
            plt.savefig(detail_dir / filename, dpi=200, bbox_inches='tight', pad_inches=0.2)
            plt.close()
            
            print(f"        ✓ Saved 3D plot with coastlines for channel {i+1}")
            
        except Exception as e:
            print(f"      ✗ Error creating 3D plot for channel {i+1}: {e}")
            import traceback
            traceback.print_exc()
            plt.close('all')
            continue

def extract_date_info(ds):
    """Extract date and time information from dataset global attributes"""
    
    try:
        # Try to get date range information
        if hasattr(ds, 'RangeBeginningDate') and hasattr(ds, 'RangeEndingDate'):
            begin_date = ds.attrs.get('RangeBeginningDate', '')
            end_date = ds.attrs.get('RangeEndingDate', '')
            
            # Format dates nicely
            if begin_date and end_date:
                if begin_date == end_date:
                    return f"Date: {begin_date}"
                else:
                    return f"Date Range: {begin_date} to {end_date}"
        
        # Try alternative date fields
        if hasattr(ds, 'ProductionDateTime'):
            prod_date = ds.attrs.get('ProductionDateTime', '')
            if prod_date:
                # Extract just the date part (before 'T')
                if 'T' in prod_date:
                    date_part = prod_date.split('T')[0]
                    return f"Production Date: {date_part}"
                return f"Production Date: {prod_date}"
        
        # Try to extract from filename if present
        if hasattr(ds, 'Filename'):
            filename = ds.attrs.get('Filename', '')
            if filename:
                # Look for date pattern like 201808 or 2018-08
                import re
                date_match = re.search(r'(\d{4})(\d{2})', filename)
                if date_match:
                    year, month = date_match.groups()
                    return f"Date: {year}-{month}"
        
        # Try GranuleID
        if hasattr(ds, 'GranuleID'):
            granule_id = ds.attrs.get('GranuleID', '')
            if granule_id:
                import re
                date_match = re.search(r'(\d{4})(\d{2})', granule_id)
                if date_match:
                    year, month = date_match.groups()
                    return f"Date: {year}-{month}"
        
        # Fallback - no date information found
        return "Date: Not specified"
        
    except Exception as e:
        print(f"    Warning: Could not extract date info: {e}")
        return "Date: Unknown"

def create_coastlines_basemap(ax, ds, z_level):
    """Create coastlines wireframe basemap on bottom plane"""
    
    print("    Creating coastlines wireframe basemap...")
    
    # Get coordinate bounds - NORMAL ORIENTATION
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    try:
        # Add coordinate grid first
        add_coordinate_grid_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level)
        
        # Add coastlines
        print("      Adding Natural Earth coastlines...")
        add_cartopy_coastlines_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level)
        
        print("      ✓ Coastlines basemap created successfully")
        
    except Exception as e:
        print(f"      ✗ Coastlines failed: {e}")
        print("      ✓ Coordinate grid still available")

def add_cartopy_coastlines_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add coastlines using Cartopy's Natural Earth data as wireframe"""
    
    try:
        import cartopy.io.shapereader as shpreader
        from shapely.geometry import MultiLineString, LineString, Point, Polygon, MultiPoint, MultiPolygon, GeometryCollection
        
        # Get Natural Earth coastlines
        coastlines_shp = shpreader.natural_earth(resolution='50m',
                                                category='physical',
                                                name='coastline')
        
        for record in shpreader.Reader(coastlines_shp).records():
            geometry = record.geometry
            
            # Handle different geometry types
            coords_list = extract_coordinates_from_geometry(geometry)
            
            for coords in coords_list:
                if len(coords) >= 2:  # Need at least 2 points for a line
                    lons, lats = zip(*coords)
                    plot_geometry_wireframe(ax, lons, lats, z_level, 'black', 0.8, lon_min, lon_max, lat_min, lat_max)
        
        print("        ✓ Coastlines added")
        
    except Exception as e:
        print(f"        ✗ Coastlines failed: {e}")

def extract_coordinates_from_geometry(geometry):
    """Extract coordinate sequences from various geometry types"""
    
    coords_list = []
    
    try:
        from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection
        
        if isinstance(geometry, (Point, MultiPoint)):
            return coords_list
            
        elif isinstance(geometry, LineString):
            coords_list.append(list(geometry.coords))
            
        elif isinstance(geometry, Polygon):
            coords_list.append(list(geometry.exterior.coords))
            
        elif isinstance(geometry, MultiLineString):
            for line in geometry.geoms:
                coords_list.append(list(line.coords))
                
        elif isinstance(geometry, MultiPolygon):
            for polygon in geometry.geoms:
                coords_list.append(list(polygon.exterior.coords))
                
        elif isinstance(geometry, GeometryCollection):
            for geom in geometry.geoms:
                coords_list.extend(extract_coordinates_from_geometry(geom))
                
        elif hasattr(geometry, 'coords'):
            coords_list.append(list(geometry.coords))
            
        elif hasattr(geometry, 'geoms'):
            for geom in geometry.geoms:
                coords_list.extend(extract_coordinates_from_geometry(geom))
        
    except Exception as e:
        pass  # Skip problematic geometries
    
    return coords_list

def plot_geometry_wireframe(ax, lons, lats, z_level, color, alpha, lon_min, lon_max, lat_min, lat_max):
    """Plot geometry coordinates as wireframe lines on the bottom plane"""
    
    try:
        lons = np.array(lons)
        lats = np.array(lats)
        
        # Filter to domain bounds with buffer
        buffer = 5.0
        mask = ((lons >= lon_min - buffer) & (lons <= lon_max + buffer) & 
               (lats >= lat_min - buffer) & (lats <= lat_max + buffer))
        
        if np.sum(mask) >= 2:
            filtered_lons = lons[mask]
            filtered_lats = lats[mask]
            z_coords = np.full_like(filtered_lons, z_level)
            
            # Split into segments for better performance
            segments = split_into_segments(filtered_lons, filtered_lats, z_coords)
            
            for seg_lons, seg_lats, seg_z in segments:
                if len(seg_lons) >= 2:
                    ax.plot(seg_lons, seg_lats, seg_z,
                           color=color, linewidth=0.7, alpha=alpha, zorder=2)
    
    except Exception as e:
        pass

def split_into_segments(lons, lats, z_coords, max_gap=10.0):
    """Split coordinates into segments when there are large gaps"""
    
    segments = []
    
    if len(lons) < 2:
        return segments
    
    start_idx = 0
    
    for i in range(1, len(lons)):
        dist = np.sqrt((lons[i] - lons[i-1])**2 + (lats[i] - lats[i-1])**2)
        
        if dist > max_gap:
            if i - start_idx >= 2:
                segments.append((lons[start_idx:i], lats[start_idx:i], z_coords[start_idx:i]))
            start_idx = i
    
    if len(lons) - start_idx >= 2:
        segments.append((lons[start_idx:], lats[start_idx:], z_coords[start_idx:]))
    
    return segments

def add_coordinate_grid_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add lat/lon coordinate grid as wireframe"""
    
    # Determine appropriate spacing
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min
    
    lon_spacing = 30 if lon_range > 120 else (15 if lon_range > 60 else 10)
    lat_spacing = 30 if lat_range > 120 else (15 if lat_range > 60 else 10)
    
    # Longitude lines
    lon_lines = np.arange(-180, 181, lon_spacing)
    lon_lines = lon_lines[(lon_lines >= lon_min - 10) & (lon_lines <= lon_max + 10)]
    
    for lon in lon_lines:
        lats = np.linspace(lat_min, lat_max, 100)
        lons = np.full_like(lats, lon)
        z_coords = np.full_like(lats, z_level)
        ax.plot(lons, lats, z_coords, 'gray', linewidth=0.3, alpha=0.4, zorder=1)
    
    # Latitude lines
    lat_lines = np.arange(-90, 91, lat_spacing)
    lat_lines = lat_lines[(lat_lines >= lat_min - 10) & (lat_lines <= lat_max + 10)]
    
    for lat in lat_lines:
        lons = np.linspace(lon_min, lon_max, 100)
        lats = np.full_like(lons, lat)
        z_coords = np.full_like(lons, z_level)
        ax.plot(lons, lats, z_coords, 'gray', linewidth=0.3, alpha=0.4, zorder=1)

def has_valid_data_array(data_array):
    """Check if data array has any valid (non-NaN) values"""
    if data_array.size == 0:
        return False
    
    valid_data = data_array[~np.isnan(data_array)]
    return len(valid_data) > 0

def get_safe_data_range_array(data_array):
    """Get data range with proper NaN handling for numpy array"""
    flat_data = data_array.flatten()
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

def generate_stats_text_array(data_array):
    """Generate stats text for numpy array"""
    flat_data = data_array.flatten()
    valid_data = flat_data[~np.isnan(flat_data)]
    
    if len(valid_data) == 0:
        return "No valid data"
    
    stats = f"""Statistics:
Min: {np.min(valid_data):.3f}
Max: {np.max(valid_data):.3f}
Mean: {np.mean(valid_data):.3f}
Std: {np.std(valid_data):.3f}
Valid: {len(valid_data):,} / {len(flat_data):,}
Coverage: {len(valid_data)/len(flat_data)*100:.1f}%"""
    
    return stats

def main():
    """Main execution function"""
    print("🌍 3D Satellite Data Plotter with Coastlines")
    print("=" * 60)
    
    # Configuration
    input_pattern = "merra2.*.nc4"
    output_directory = "qc_review_3d_coastlines"
    
    # Find input files
    file_list = glob.glob(input_pattern)
    
    if not file_list:
        print(f"❌ No files found matching pattern: {input_pattern}")
        return
    
    print(f"📁 Found {len(file_list)} files to process:")
    for f in file_list:
        print(f"   - {f}")
    
    print(f"\n🗺️  Creating 3D plots with coastlines wireframe")
    print(f"📊 Normal geographic orientation (no coordinate reversals)")
    print(f"📊 Including date information in titles")
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
                        create_3d_plots_with_cartopy_wireframe(ds, var_name, file_output_dir)
                
                ds.close()
                
            except Exception as e:
                print(f"  ✗ Error processing {file_path.name}: {e}")
        
        print(f"\n🎉 Processing complete!")
        print(f"📁 3D plots with coastlines saved to: {output_directory}/")
        print(f"\n✨ Features include:")
        print(f"   • Normal geographic orientation")
        print(f"   • Natural Earth coastlines as wireframe")
        print(f"   • Coordinate grid (lat/lon lines)")
        print(f"   • Date information in plot titles")
        print(f"   • Your satellite data as surface above wireframe")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
