# MERRA2-Satellite-Data-Plotting  
## Usage: main_comprehensive_plotter.py -sat airs_aqua -year [1900-2099 or leave empty] -month [01-12 or leave empty] -tau [0,6,12,18,all, or leave empty] 
├── main_comprehensive_plotter.py  # NEW: Both 2D+3D execution  
%├── comprehensive_plotter.py   # Combined 2D+3D plotting  
%%├── plot_2d_geographic.py      # 2D plotting functions  
%%├── main_3d_plotter.py         # 3D-only execution (original)  
%%%├── terrain_generation.py       # Terrain and elevation  
%%%├── color_mapping.py           # Colors and statistics 
%%%├── geographic_features.py     # Coastlines, borders, etc.  
%%%├── basemap_creation.py        # 3D basemap assembly  
%%%├── qc_utilities.py            # QC checklist and utilities  #as of now unused. makes html checklist

