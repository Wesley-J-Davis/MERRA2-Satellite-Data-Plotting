def add_cartopy_coastlines_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add coastlines using Cartopy's Natural Earth data as wireframe"""
    
    try:
        import cartopy.io.shapereader as shpreader
        from shapely.geometry import MultiLineString, LineString
        
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

def add_cartopy_borders_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add political boundaries using Cartopy's Natural Earth data as wireframe"""
    
    try:
        import cartopy.io.shapereader as shpreader
        
        # Get Natural Earth borders
        borders_shp = shpreader.natural_earth(resolution='50m',
                                            category='cultural',
                                            name='admin_0_boundary_lines_land')
        
        for record in shpreader.Reader(borders_shp).records():
            geometry = record.geometry
            
            # Handle different geometry types
            coords_list = extract_coordinates_from_geometry(geometry)
            
            for coords in coords_list:
                if len(coords) >= 2:
                    lons, lats = zip(*coords)
                    plot_geometry_wireframe(ax, lons, lats, z_level, 'red', 0.6, lon_min, lon_max, lat_min, lat_max)
        
        print("        ✓ Political borders added")
        
    except Exception as e:
        print(f"        ✗ Political borders failed: {e}")

def add_cartopy_rivers_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level):
    """Add major rivers using Cartopy's Natural Earth data as wireframe"""
    
    try:
        import cartopy.io.shapereader as shpreader
        
        # Get Natural Earth rivers
        rivers_shp = shpreader.natural_earth(resolution='50m',
                                           category='physical',
                                           name='rivers_lake_centerlines')
        
        for record in shpreader.Reader(rivers_shp).records():
            # Only major rivers
            if record.attributes.get('scalerank', 10) <= 4:
                geometry = record.geometry
                
                # Handle different geometry types
                coords_list = extract_coordinates_from_geometry(geometry)
                
                for coords in coords_list:
                    if len(coords) >= 2:
                        lons, lats = zip(*coords)
                        plot_geometry_wireframe(ax, lons, lats, z_level, 'blue', 0.5, lon_min, lon_max, lat_min, lat_max)
        
        print("        ✓ Major rivers added")
        
    except Exception as e:
        print(f"        ✗ Rivers failed: {e}")

def extract_coordinates_from_geometry(geometry):
    """Extract coordinate sequences from various geometry types"""
    
    coords_list = []
    
    try:
        # Import shapely geometry types
        from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection
        
        if isinstance(geometry, (Point, MultiPoint)):
            # Skip points for wireframe
            return coords_list
            
        elif isinstance(geometry, LineString):
            # Single LineString
            coords_list.append(list(geometry.coords))
            
        elif isinstance(geometry, Polygon):
            # Polygon - use exterior ring
            coords_list.append(list(geometry.exterior.coords))
            
        elif isinstance(geometry, MultiLineString):
            # Multiple LineStrings
            for line in geometry.geoms:
                coords_list.append(list(line.coords))
                
        elif isinstance(geometry, MultiPolygon):
            # Multiple Polygons - use exterior rings
            for polygon in geometry.geoms:
                coords_list.append(list(polygon.exterior.coords))
                
        elif isinstance(geometry, GeometryCollection):
            # Collection of geometries
            for geom in geometry.geoms:
                coords_list.extend(extract_coordinates_from_geometry(geom))
                
        elif hasattr(geometry, 'coords'):
            # Generic coordinate sequence
            coords_list.append(list(geometry.coords))
            
        elif hasattr(geometry, 'geoms'):
            # Generic multi-geometry
            for geom in geometry.geoms:
                coords_list.extend(extract_coordinates_from_geometry(geom))
        
    except Exception as e:
        print(f"          Warning: Could not extract coordinates from geometry: {e}")
    
    return coords_list

def plot_geometry_wireframe(ax, lons, lats, z_level, color, alpha, lon_min, lon_max, lat_min, lat_max):
    """Plot geometry coordinates as wireframe lines on the bottom plane"""
    
    try:
        lons = np.array(lons)
        lats = np.array(lats)
        
        # Filter to domain bounds with buffer
        buffer = 5.0  # degrees
        mask = ((lons >= lon_min - buffer) & (lons <= lon_max + buffer) & 
               (lats >= lat_min - buffer) & (lats <= lat_max + buffer))
        
        if np.sum(mask) >= 2:  # Need at least 2 points for a line
            filtered_lons = lons[mask]
            filtered_lats = lats[mask]
            z_coords = np.full_like(filtered_lons, z_level)
            
            # Split into segments if there are gaps (for better performance)
            segments = split_into_segments(filtered_lons, filtered_lats, z_coords)
            
            for seg_lons, seg_lats, seg_z in segments:
                if len(seg_lons) >= 2:
                    ax.plot(seg_lons, seg_lats, seg_z,
                           color=color, linewidth=0.5, alpha=alpha, zorder=2)
    
    except Exception as e:
        # Skip problematic geometries silently
        pass

def split_into_segments(lons, lats, z_coords, max_gap=10.0):
    """Split coordinates into segments when there are large gaps"""
    
    segments = []
    
    if len(lons) < 2:
        return segments
    
    start_idx = 0
    
    for i in range(1, len(lons)):
        # Calculate distance between consecutive points
        dist = np.sqrt((lons[i] - lons[i-1])**2 + (lats[i] - lats[i-1])**2)
        
        if dist > max_gap:  # Large gap detected
            # Save current segment
            if i - start_idx >= 2:
                segments.append((lons[start_idx:i], lats[start_idx:i], z_coords[start_idx:i]))
            start_idx = i
    
    # Add final segment
    if len(lons) - start_idx >= 2:
        segments.append((lons[start_idx:], lats[start_idx:], z_coords[start_idx:]))
    
    return segments

def create_cartopy_wireframe_basemap(ax, ds, z_level):
    """Create wireframe basemap using Cartopy features projected on bottom plane"""
    
    print("    Creating Cartopy wireframe basemap...")
    
    # Get coordinate bounds
    lon_min, lon_max = ds.longitude.min().values, ds.longitude.max().values
    lat_min, lat_max = ds.latitude.min().values, ds.latitude.max().values
    
    try:
        # Add coordinate grid first (always works)
        add_coordinate_grid_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level)
        
        # Try to add Cartopy features
        print("      Adding Natural Earth features...")
        add_cartopy_coastlines_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level)
        add_cartopy_borders_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level)
        add_cartopy_rivers_wireframe(ax, lon_min, lon_max, lat_min, lat_max, z_level)
        
        print("      ✓ Cartopy wireframe basemap created successfully")
        
    except Exception as e:
        print(f"      ✗ Some Cartopy features failed: {e}")
        print("      ✓ Coordinate grid still available")
