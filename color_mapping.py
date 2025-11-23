import numpy as np

def create_detailed_terrain_colors(elevation, land_mask):
    """Create detailed terrain colors with smooth transitions"""
    colors = np.zeros((*elevation.shape, 4))
    
    # Ocean color palette (depth-based)
    ocean_mask = ~land_mask
    ocean_elevation = elevation[ocean_mask]
    
    # Abyssal depths (> 4000m deep) - very dark blue
    abyssal = ocean_elevation < -4000
    colors[ocean_mask][abyssal] = [0.0, 0.0, 0.2, 1.0]
    
    # Deep ocean (2000-4000m) - dark blue
    deep = (ocean_elevation >= -4000) & (ocean_elevation < -2000)
    colors[ocean_mask][deep] = [0.0, 0.1, 0.4, 1.0]
    
    # Medium depth (200-2000m) - medium blue
    medium = (ocean_elevation >= -2000) & (ocean_elevation < -200)
    colors[ocean_mask][medium] = [0.1, 0.3, 0.6, 1.0]
    
    # Continental shelf (0-200m deep) - light blue
    shelf = ocean_elevation >= -200
    colors[ocean_mask][shelf] = [0.3, 0.5, 0.8, 1.0]
    
    # Land color palette (elevation-based)
    land_elevation = elevation[land_mask]
    
    # Sea level to 100m - dark green (coastal plains)
    coastal = (land_elevation >= 0) & (land_elevation < 100)
    colors[land_mask][coastal] = [0.1, 0.5, 0.1, 1.0]
    
    # 100-500m - medium green (lowlands)
    lowland = (land_elevation >= 100) & (land_elevation < 500)
    colors[land_mask][lowland] = [0.3, 0.6, 0.2, 1.0]
    
    # 500-1000m - light green (hills)
    hills = (land_elevation >= 500) & (land_elevation < 1000)
    colors[land_mask][hills] = [0.5, 0.7, 0.3, 1.0]
    
    # 1000-2000m - yellow-brown (mountains)
    low_mountains = (land_elevation >= 1000) & (land_elevation < 2000)
    colors[land_mask][low_mountains] = [0.7, 0.6, 0.3, 1.0]
    
    # 2000-3000m - brown (high mountains)
    high_mountains = (land_elevation >= 2000) & (land_elevation < 3000)
    colors[land_mask][high_mountains] = [0.6, 0.4, 0.2, 1.0]
    
    # 3000-4000m - dark brown (very high)
    very_high = (land_elevation >= 3000) & (land_elevation < 4000)
    colors[land_mask][very_high] = [0.5, 0.3, 0.2, 1.0]
    
    # Above 4000m - white/gray (snow/ice)
    peaks = land_elevation >= 4000
    colors[land_mask][peaks] = [0.9, 0.9, 0.95, 1.0]
    
    return colors

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
Coverage: {len(valid_data)/len(flat_data)*100:.1f}%"""
    
    return stats
