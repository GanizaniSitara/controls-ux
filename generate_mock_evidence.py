import os
import json
import random
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

# Base path for evidence
EVIDENCE_PATH = Path("/mnt/c/git/control-ux/evidence")
EVIDENCE_PATH.mkdir(exist_ok=True)

# Control IDs to generate
CONTROL_IDS = [
    "CTRL-00042697",
    "CTRL-00042561", 
    "CTRL-00025821",
]

# Sample file types for control evidence
FILE_TEMPLATES = {
    "query_files": [
        ("STEP1_system_config.json", lambda run_time: {
            "instance": "P16",
            "status": "SUCCESS",
            "last_start": run_time.strftime("%Y/%m/%d %H:%M:%S"),
            "last_end": (run_time + timedelta(minutes=5)).strftime("%Y/%m/%d %H:%M:%S"),
            "definition": "borusj",
            "calendar_details": None
        }),
        ("STEP1_database_query.txt", lambda run_time: f"SELECT * FROM control_data WHERE date = '{run_time.strftime('%Y-%m-%d')}';"),
        ("STEP1_query_results_sample.csv", lambda run_time: f"id,value,timestamp\n1,100,{run_time}\n2,200,{run_time}\n3,300,{run_time}"),
    ],
    "summary_files": [
        ("STEP1_summary_statistics.txt", lambda run_time: f"Run Date: {run_time}\nTotal Records: {random.randint(1000, 5000)}\nProcessed: {random.randint(900, 4900)}\nErrors: {random.randint(0, 100)}"),
        ("STEP2_last_modified_date.txt", lambda run_time: (run_time - timedelta(days=random.randint(1, 7))).strftime("%Y-%m-%d %H:%M:%S")),
    ],
    "report_files": [
        ("STEP3_borusj_report_execution.txt", lambda run_time: f"Report executed at {run_time}\nStatus: {'SUCCESS' if random.random() > 0.1 else 'WARNING'}\nDuration: {random.randint(10, 300)}s"),
        ("CTRL-00042697_Evidence_Report.html", lambda run_time: f"<html><body><h1>Evidence Report</h1><p>Generated: {run_time}</p><p>Status: PASS</p></body></html>"),
    ],
    "data_files": [
        ("STEP4_control_data.csv", lambda run_time: "\n".join([f"row{i},{random.randint(100, 1000)},{run_time}" for i in range(10)])),
        ("STEP4_net_zero_analysis.txt", lambda run_time: f"Analysis Date: {run_time}\nNet Zero Score: {random.randint(70, 100)}%"),
    ],
    "status_files": [
        ("STEP3_job_status_all.json", lambda run_time: json.dumps({
            "control_batch_job_001": {
                "instance": "P16", 
                "status": "SUCCESS",
                "last_start": run_time.strftime("%Y/%m/%d %H:%M:%S"),
                "last_end": (run_time + timedelta(minutes=15)).strftime("%Y/%m/%d %H:%M:%S"),
                "definition": "<html>\\n <head>\\n  <link href=\\\"/ATS/htdocs/stylesheet/barcap.css\\\" rel=\\\"STYLESHEET\\\" type=\\\"text/css\\\">\\n",
                "calendar_details": None
            }
        }, indent=2)),
        ("STEP3a_job_schedule.csv", lambda run_time: "job_name,calendar_name,next_run\nscheduled_job_1,DAILY," + (run_time + timedelta(days=1)).strftime("%Y-%m-%d")),
    ]
}

def generate_evidence_for_run(control_id, run_time):
    """Generate evidence files for a single control run"""
    # Create folder name
    folder_name = f"{control_id}_{run_time.strftime('%Y-%m-%d_%H-%M')}"
    folder_path = EVIDENCE_PATH / folder_name
    folder_path.mkdir(exist_ok=True)
    
    # Randomly select which files to include (simulate real variation)
    all_files = []
    for category, files in FILE_TEMPLATES.items():
        # Include 60-100% of files from each category
        num_files = random.randint(int(len(files) * 0.6), len(files))
        selected_files = random.sample(files, num_files)
        all_files.extend(selected_files)
    
    # Generate files
    for filename, content_generator in all_files:
        file_path = folder_path / filename
        content = content_generator(run_time)
        
        # Write content
        if isinstance(content, dict):
            with open(file_path, 'w') as f:
                json.dump(content, f, indent=2)
        else:
            with open(file_path, 'w') as f:
                f.write(str(content))
    
    print(f"Created: {folder_name} with {len(all_files)} files")
    return folder_path

def create_duplicate_run(original_folder, new_time):
    """Create a duplicate run with same file content"""
    new_folder_name = f"{original_folder.name.rsplit('_', 2)[0]}_{new_time.strftime('%Y-%m-%d_%H-%M')}"
    new_folder_path = EVIDENCE_PATH / new_folder_name
    new_folder_path.mkdir(exist_ok=True)
    
    # Copy all files
    for file_path in original_folder.iterdir():
        if file_path.is_file():
            content = file_path.read_text()
            (new_folder_path / file_path.name).write_text(content)
    
    print(f"Created duplicate: {new_folder_name}")
    return new_folder_path

def main():
    print("Generating mock evidence data...")
    
    # Start time - let's generate data for the last 3 days
    start_time = datetime.now() - timedelta(days=3)
    
    for control_id in CONTROL_IDS:
        print(f"\nGenerating evidence for {control_id}...")
        
        # Generate runs at various intervals
        current_time = start_time
        folders_created = []
        
        while current_time < datetime.now():
            # Create a run
            folder = generate_evidence_for_run(control_id, current_time)
            folders_created.append((folder, current_time))
            
            # Sometimes create a duplicate run within the same 2-hour window
            if random.random() < 0.3 and control_id == CONTROL_IDS[0]:  # 30% chance for first control
                duplicate_time = current_time + timedelta(minutes=random.randint(10, 50))
                create_duplicate_run(folder, duplicate_time)
            
            # Sometimes skip a run (simulate failures)
            if random.random() < 0.1:  # 10% chance to skip
                current_time += timedelta(hours=random.randint(4, 8))
            else:
                # Normal interval - every 2-4 hours with some variation
                current_time += timedelta(hours=2, minutes=random.randint(-30, 30))
        
        # For the first control, let's modify some recent files to show changes
        if control_id == CONTROL_IDS[0] and len(folders_created) > 2:
            recent_folder = folders_created[-1][0]
            prev_folder = folders_created[-2][0]
            
            # Modify a file in the recent run
            status_file = recent_folder / "STEP3_job_status_all.json"
            if status_file.exists():
                data = json.loads(status_file.read_text())
                # Change the timestamp slightly
                for job in data.values():
                    if "last_end" in job:
                        end_time = datetime.strptime(job["last_end"], "%Y/%m/%d %H:%M:%S")
                        job["last_end"] = (end_time + timedelta(minutes=5)).strftime("%Y/%m/%d %H:%M:%S")
                status_file.write_text(json.dumps(data, indent=2))
                print(f"Modified {status_file.name} in recent run to show changes")
    
    print("\nMock evidence generation complete!")
    print(f"Evidence location: {EVIDENCE_PATH}")
    
    # Show summary
    total_folders = len(list(EVIDENCE_PATH.iterdir()))
    print(f"Total evidence folders created: {total_folders}")

if __name__ == "__main__":
    main()