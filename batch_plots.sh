#!/bin/bash
#SBATCH --job-name=satellite_qc_plots
#SBATCH --output=plots_%j.log
#SBATCH --time=2:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1

# Email notifications
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=wesley.j.davis@nasa.gov

# Load necessary modules
source /etc/profile
module purge
module load python/GEOSpyD/24.3.0-0/3.11

# Set environment variables if needed
export PYTHONUNBUFFERED=1

# Script directory
SCRIPT_DIR="/gpfsm/dhome/dao_ops/operations/GIT-OPS/MERRA2-Satellite-Data-Plotting"

# Define parameters
SATELLITE=$1
YEAR=$2
MONTH=$3
TAU=$4

# Print job information
echo "===== Satellite QC Plot Generation ====="
echo "Job ID: $SLURM_JOB_ID"
echo "Node: $SLURMD_NODENAME"
echo "Start time: $(date)"
echo "Parameters:"
echo "  Satellite: $SATELLITE"
echo "  Year: $YEAR" 
echo "  Month: $MONTH"
echo "  Tau: $TAU"
echo "======================================"

# Go to script directory
cd $SCRIPT_DIR

# Run the script
python ./main_comprehensive_plotter.py \
  -sat $SATELLITE \
  -year $YEAR \
  -month $MONTH \
  -tau $TAU \
  -plots_3d \
  --yes

# Print completion info
echo "======================================"
echo "Job completed at: $(date)"
echo "======================================"

exit 0
