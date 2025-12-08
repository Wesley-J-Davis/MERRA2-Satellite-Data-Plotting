import glob
from pathlib import Path
from comprehensive_plotter import comprehensive_qc_viewer
import argparse
import os

def validate_year(value):

    ivalue = int(value)
    if not (1900 <= ivalue <= 2099):
        raise argparse.ArgumentTypeError(f"Year must be between 1900-2099, got {ivalue}")
    return ivalue

def validate_month(value):

    ivalue = int(value)
    if not (1 <= ivalue <= 12):
        raise argparse.ArgumentTypeError(f"Month must be between 1-12, got {ivalue}")
    return f"{ivalue:02d}"  # Returns zero-padded string
    
def validate_tau(value):
    if not value:  # If no value is provided
        return "*" # select monthly 
    if value.lower() == "all":
        return "" # this selects the combined monthly file
        
    ivalue = int(value)
    if ivalue in [0, 6, 12, 18]:
        return f"_{ivalue:02d}z" # this selects the individual tau
    else:
        raise argparse.ArgumentTypeError(f"Tau must be one of: 0, 6, 12, 18, got {ivalue}")
        
def main():
    """Main execution function for comprehensive plotting"""
    parser = argparse.ArgumentParser(description='Comprehensive Satellite Data QC Plotter')
    parser.add_argument('-sat', '--satellite', required=True, 
                        help='Satellite name (e.g., metop-a, metop-b, noaa-18)')
    parser.add_argument('-year', '--year', required=True, type=validate_year,
                        help='Year (4 digits, e.g., 2023)',
                        metavar='YYYY')
    parser.add_argument('-month', '--month', required=True, type=validate_month,
                        help='Month (1-12, returns zero-padded)',
                        metavar='MM')
    parser.add_argument('-tau', '--tau', required=False, type=validate_tau,
                        help='Tau value (00,06,12,18, returns _XX format)',
                        metavar='TAU',
                        default="")
    parser.add_argument('-plots_3d', '--plots_3d', action='store_true', help="this flag enables 3d plots")
    parser.add_argument('-y', '--yes', action='store_true',
                        help='Skip confirmation prompts (for batch processing)')    
    args = parser.parse_args()
    
    """
    GIT-OPS/MERRA2-Satellite-Data-Plotting> ls /discover/nobackup/projects/gmao/merra2/data/obs/.WORK/products_GES-DISC/airs_aqua/merra2.airs_aqua.201301*
    /discover/nobackup/projects/gmao/merra2/data/obs/.WORK/products_GES-DISC/airs_aqua/merra2.airs_aqua.201301_00z.nc4
    /discover/nobackup/projects/gmao/merra2/data/obs/.WORK/products_GES-DISC/airs_aqua/merra2.airs_aqua.201301_06z.nc4
    /discover/nobackup/projects/gmao/merra2/data/obs/.WORK/products_GES-DISC/airs_aqua/merra2.airs_aqua.201301_12z.nc4
    /discover/nobackup/projects/gmao/merra2/data/obs/.WORK/products_GES-DISC/airs_aqua/merra2.airs_aqua.201301_18z.nc4
    /discover/nobackup/projects/gmao/merra2/data/obs/.WORK/products_GES-DISC/airs_aqua/merra2.airs_aqua.201301.nc4
    """

    print("🌍📊 Comprehensive Satellite Data QC Plotter")
    print("=" * 60)
    print("Creates both 2D geographic and 3D realistic basemap visualizations")
    print()
    base_dir = "/discover/nobackup/projects/gmao/merra2/data/obs/.WORK/"
    
    # Configuration using arguments
    input_pattern = f"{base_dir}/products_GES-DISC/{args.satellite}/merra2.{args.satellite}.{args.year}{args.month}{args.tau}.nc4"
    output_directory = f"{base_dir}/comprehensive_qc_review/{args.satellite}/{args.year}/{args.month}"
    os.makedirs(output_directory, exist_ok=True)    
    # Find input files
    file_list = glob.glob(input_pattern)
    
    if not file_list:
        print(f"❌ No files found matching pattern: {input_pattern}")
        print("Please check your file pattern and current directory.")
        return
    
    print(f"📁 Found {len(file_list)} files to process:")
    for f in file_list:
        print(f"   - {f}")
    
    print(f"\n📊 Output will be saved to: {output_directory}/")
    print(f"\n🎨 Will create for each variable:")
    print(f"   • 2D Overview plots (all channels)")
    print(f"   • 2D Detailed plots (individual channels)")
    if args.plots_3d == True:
        print(f"   • 3D Surface plots with realistic basemaps")
    print(f"   • Statistical summaries")
    print(f"   • QC checklist for human review")
    
    # Ask for confirmation
    if args.yes:
        print(f"\nAutomatic confirmation: Processing {len(file_list)} files")
    else:
        try:
            response = input(f"\nProceed with processing {len(file_list)} files? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Processing cancelled.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\nProcessing cancelled.")
            return
    
    # Process files
    try:
        output_path = comprehensive_qc_viewer(file_list, output_dir=output_directory,plots_3d=args.plots_3d)
        
        print(f"\n🎉 Processing complete!")
        print(f"📁 All visualizations saved to: {output_path}/")
        print(f"\n📋 Next steps for QC review:")
        print(f"   1. Open: {output_path}/qc_checklist.html")
        print(f"   2. Review generated plots for each file/variable")
        print(f"   3. Check quality control items in the checklist")
        print(f"   4. Approve or reject each product")
        print(f"   5. Print/save the completed checklist")
        
        print(f"\n🔍 Plot types generated:")
        print(f"   • Overview: Quick visual scan of all channels")
        print(f"   • Detailed 2D: High-resolution geographic plots")
        print(f"   • 3D Basemaps: Realistic terrain context")
        
    except KeyboardInterrupt:
        print("\n⏹️  Processing interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during processing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
