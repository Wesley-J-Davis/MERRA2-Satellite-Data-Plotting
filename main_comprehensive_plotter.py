import glob
from pathlib import Path
from comprehensive_plotter import comprehensive_qc_viewer

def main():
    """Main execution function for comprehensive plotting"""
    print("🌍📊 Comprehensive Satellite Data QC Plotter")
    print("=" * 60)
    print("Creates both 2D geographic and 3D realistic basemap visualizations")
    print()
    
    # Configuration
    input_pattern = "merra2.mhs_metop-*.nc4"  # Modify this pattern as needed
    output_directory = "comprehensive_qc_review"
    
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
    print(f"   • 3D Surface plots with realistic basemaps")
    print(f"   • Statistical summaries")
    print(f"   • QC checklist for human review")
    
    # Ask for confirmation
    try:
        response = input(f"\nProceed with processing {len(file_list)} files? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Processing cancelled.")
            return
    except KeyboardInterrupt:
        print("\nProcessing cancelled.")
        return
    
    # Process files
    try:
        output_path = comprehensive_qc_viewer(file_list, output_dir=output_directory)
        
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
