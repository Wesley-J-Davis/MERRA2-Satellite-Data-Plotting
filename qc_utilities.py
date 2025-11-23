import pandas as pd
from pathlib import Path
import numpy as np

def generate_stats_summary(data, var_name):
    """Generate numerical statistics for QC log"""
    flat_data = data.values.flatten()
    valid_data = flat_data[~np.isnan(flat_data)]
    
    return {
        'min': np.min(valid_data) if len(valid_data) > 0 else np.nan,
        'max': np.max(valid_data) if len(valid_data) > 0 else np.nan,
        'mean': np.mean(valid_data) if len(valid_data) > 0 else np.nan,
        'std': np.std(valid_data) if len(valid_data) > 0 else np.nan,
        'n_valid': len(valid_data),
        'n_total': len(flat_data),
        'pct_valid': len(valid_data) / len(flat_data) * 100 if len(flat_data) > 0 else 0
    }

def create_qc_checklist(file_list, output_dir):
    """Create an HTML checklist for QC tracking"""
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>QC Review Checklist</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .file-block {{ border: 1px solid #ccc; margin: 10px 0; padding: 10px; }}
            .approved {{ background-color: #d4edda; }}
            .rejected {{ background-color: #f8d7da; }}
            input[type="checkbox"] {{ margin-right: 10px; }}
            .timestamp {{ font-size: 0.9em; color: #666; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1>Quality Control Review Checklist</h1>
        <p>Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary">
            <h3>Summary</h3>
            <p><strong>Total files to review:</strong> {len(file_list)}</p>
            <p><strong>Instructions:</strong> Review each product's plots and check the appropriate box.</p>
            <p><strong>Available visualizations:</strong></p>
            <ul>
                <li>2D Geographic plots (overview and detailed)</li>
                <li>3D plots with realistic basemaps</li>
                <li>Statistical summaries on each plot</li>
            </ul>
        </div>
    """
    
    for i, file_path in enumerate(file_list):
        file_name = Path(file_path).name
        html_content += f"""
        <div class="file-block" id="file_{i}">
            <h3>{file_name}</h3>
            <p><strong>Plot locations:</strong></p>
            <ul>
                <li>2D Overview: <code>{Path(file_path).stem}/[variable]_overview_geographic.png</code></li>
                <li>2D Detailed: <code>{Path(file_path).stem}/[variable]_detailed_2d/</code></li>
                <li>3D Realistic: <code>{Path(file_path).stem}/[variable]_3d_offline_ne/</code></li>
            </ul>
            
            <label><input type="checkbox" name="approved_{i}" onclick="markApproved({i})"> ✅ APPROVED for release</label><br>
            <label><input type="checkbox" name="rejected_{i}" onclick="markRejected({i})"> ❌ REJECTED - needs revision</label><br>
            
            <h4>Quality Check Items:</h4>
            <label><input type="checkbox" name="spatial_{i}"> Spatial patterns look reasonable</label><br>
            <label><input type="checkbox" name="values_{i}"> Data values within expected ranges</label><br>
            <label><input type="checkbox" name="coverage_{i}"> Data coverage is adequate</label><br>
            <label><input type="checkbox" name="artifacts_{i}"> No obvious artifacts or anomalies</label><br>
            <label><input type="checkbox" name="channels_{i}"> All channels show consistent behavior</label><br>
            
            <textarea placeholder="Notes/Issues/Observations:" style="width: 100%; margin-top: 5px;" rows="3"></textarea>
            <div class="timestamp" id="timestamp_{i}"></div>
        </div>
        """
    
    html_content += """
        <div class="summary">
            <h3>Final Review Summary</h3>
            <p><strong>Reviewer:</strong> <input type="text" placeholder="Your name" style="width: 200px;"></p>
            <p><strong>Review Date:</strong> <input type="date" value="" style="width: 150px;"></p>
            <p><strong>Overall Assessment:</strong></p>
            <textarea placeholder="Overall comments about this batch of products..." style="width: 100%;" rows="4"></textarea>
            <br><br>
            <button onclick="window.print()" style="padding: 10px 20px; font-size: 16px;">🖨️ Print/Save Review</button>
        </div>
        
        <script>
        // Set today's date
        document.querySelector('input[type="date"]').value = new Date().toISOString().split('T')[0];
        
        function markApproved(i) {
            document.getElementById('file_' + i).className = 'file-block approved';
            document.querySelector('input[name="rejected_' + i + '"]').checked = false;
            document.getElementById('timestamp_' + i).innerHTML = 'Approved: ' + new Date().toLocaleString();
        }
        function markRejected(i) {
            document.getElementById('file_' + i).className = 'file-block rejected';
            document.querySelector('input[name="approved_' + i + '"]').checked = false;
            document.getElementById('timestamp_' + i).innerHTML = 'Rejected: ' + new Date().toLocaleString();
        }
        </script>
    </body>
    </html>
    """
    
    with open(output_dir / 'qc_checklist.html', 'w') as f:
        f.write(html_content)
