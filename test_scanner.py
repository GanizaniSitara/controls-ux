from pathlib import Path
import os

evidence_path = Path("/mnt/c/git/control-ux/evidence")
print(f"Evidence path exists: {evidence_path.exists()}")
print(f"Evidence path is dir: {evidence_path.is_dir()}")
print(f"Evidence path absolute: {evidence_path.absolute()}")

folders = list(evidence_path.iterdir())
print(f"\nTotal items in evidence: {len(folders)}")
print("\nFirst 5 folders:")
for i, folder in enumerate(folders[:5]):
    print(f"  {folder.name} - is_dir: {folder.is_dir()}")
    if folder.is_dir():
        parts = folder.name.split('_')
        print(f"    Parts ({len(parts)}): {parts}")
        if len(parts) >= 5:
            control_id = '_'.join(parts[:-3])
            date_str = parts[-3]
            time_str = parts[-2] + '-' + parts[-1]
            print(f"    Control: {control_id}")
            print(f"    Date: {date_str}")
            print(f"    Time: {time_str}")
            print(f"    Timestamp str: {date_str}_{time_str}")

# Test the actual scanner
print("\n\nTesting actual scanner:")
from api.evidence_scanner import EvidenceScanner

scanner = EvidenceScanner("/mnt/c/git/control-ux/evidence")
runs = scanner.scan_evidence_folders()
print(f"Scanner found {len(runs)} controls")
for control_id, control_runs in runs.items():
    print(f"  {control_id}: {len(control_runs)} runs")