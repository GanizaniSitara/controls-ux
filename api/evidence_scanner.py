import os
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
from pathlib import Path
from collections import defaultdict

class EvidenceScanner:
    def __init__(self, evidence_base_path: str):
        self.evidence_base_path = Path(evidence_base_path)
        
    def scan_evidence_folders(self) -> Dict[str, List[Dict[str, Any]]]:
        """Scan evidence folder structure and extract run information"""
        runs = defaultdict(list)
        
        if not self.evidence_base_path.exists():
            return dict(runs)
            
        # Pattern: CONTROL_ID_YYYY-MM-DD_HH-MM
        for folder in self.evidence_base_path.iterdir():
            if folder.is_dir() and '_' in folder.name:
                # Split by the date pattern to separate control ID from timestamp
                parts = folder.name.rsplit('_', 2)  # Split from right, max 2 splits
                if len(parts) == 3:
                    control_id = parts[0]
                    date_str = parts[1]  # YYYY-MM-DD
                    time_str = parts[2]  # HH-MM
                    
                    try:
                        # Parse timestamp
                        timestamp_str = f"{date_str}_{time_str}"
                        timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d_%H-%M")
                        
                        # Get file hashes
                        file_hashes = self._calculate_folder_hashes(folder)
                        
                        run_info = {
                            'folder_name': folder.name,
                            'control_id': control_id,
                            'timestamp': timestamp.isoformat(),
                            'files': file_hashes,
                            'file_count': len(file_hashes),
                            'total_hash': self._calculate_combined_hash(file_hashes)
                        }
                        
                        runs[control_id].append(run_info)
                    except ValueError:
                        # Skip folders that don't match expected format
                        continue
                        
        # Sort runs by timestamp for each control
        for control_id in runs:
            runs[control_id].sort(key=lambda x: x['timestamp'])
            
        return dict(runs)
    
    def bucketize_runs(self, runs: Dict[str, List[Dict]], bucket_hours: int = 2) -> Dict[str, Dict[str, List[Dict]]]:
        """Group runs into time buckets"""
        bucketized = defaultdict(lambda: defaultdict(list))
        
        for control_id, control_runs in runs.items():
            for run in control_runs:
                timestamp = datetime.fromisoformat(run['timestamp'])
                # Round down to bucket start
                bucket_start = timestamp.replace(
                    hour=(timestamp.hour // bucket_hours) * bucket_hours,
                    minute=0,
                    second=0,
                    microsecond=0
                )
                bucket_key = bucket_start.isoformat()
                bucketized[control_id][bucket_key].append(run)
                
        return dict(bucketized)
    
    def detect_duplicates(self, bucketized_runs: Dict[str, Dict[str, List[Dict]]]) -> Dict[str, List[Dict]]:
        """Detect duplicate runs within buckets"""
        duplicates = defaultdict(list)
        
        for control_id, buckets in bucketized_runs.items():
            for bucket_key, bucket_runs in buckets.items():
                if len(bucket_runs) > 1:
                    # Check for exact duplicates based on total hash
                    hash_groups = defaultdict(list)
                    for run in bucket_runs:
                        hash_groups[run['total_hash']].append(run)
                    
                    for hash_val, duplicate_runs in hash_groups.items():
                        if len(duplicate_runs) > 1:
                            duplicates[control_id].append({
                                'bucket': bucket_key,
                                'duplicate_hash': hash_val,
                                'runs': duplicate_runs
                            })
                            
        return dict(duplicates)
    
    def calculate_deltas(self, runs: Dict[str, List[Dict]]) -> Dict[str, List[Dict]]:
        """Calculate file hash deltas between consecutive runs"""
        deltas = defaultdict(list)
        
        for control_id, control_runs in runs.items():
            for i in range(1, len(control_runs)):
                prev_run = control_runs[i-1]
                curr_run = control_runs[i]
                
                prev_files = {f['name']: f['hash'] for f in prev_run['files']}
                curr_files = {f['name']: f['hash'] for f in curr_run['files']}
                
                # Find changes
                added_files = set(curr_files.keys()) - set(prev_files.keys())
                removed_files = set(prev_files.keys()) - set(curr_files.keys())
                common_files = set(prev_files.keys()) & set(curr_files.keys())
                
                changed_files = []
                unchanged_files = []
                
                for file in common_files:
                    if prev_files[file] != curr_files[file]:
                        changed_files.append({
                            'name': file,
                            'prev_hash': prev_files[file],
                            'curr_hash': curr_files[file]
                        })
                    else:
                        unchanged_files.append(file)
                
                delta = {
                    'from_run': prev_run['folder_name'],
                    'to_run': curr_run['folder_name'],
                    'from_timestamp': prev_run['timestamp'],
                    'to_timestamp': curr_run['timestamp'],
                    'added': list(added_files),
                    'removed': list(removed_files),
                    'changed': changed_files,
                    'unchanged': unchanged_files,
                    'summary': {
                        'added_count': len(added_files),
                        'removed_count': len(removed_files),
                        'changed_count': len(changed_files),
                        'unchanged_count': len(unchanged_files),
                        'total_files_prev': len(prev_files),
                        'total_files_curr': len(curr_files)
                    }
                }
                
                deltas[control_id].append(delta)
                
        return dict(deltas)
    
    def _calculate_folder_hashes(self, folder_path: Path) -> List[Dict[str, str]]:
        """Calculate hashes for all files in a folder"""
        file_hashes = []
        
        for file_path in sorted(folder_path.iterdir()):
            if file_path.is_file():
                file_hash = self._calculate_file_hash(file_path)
                file_hashes.append({
                    'name': file_path.name,
                    'hash': file_hash,
                    'size': file_path.stat().st_size
                })
                
        return file_hashes
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        sha256_hash = hashlib.sha256()
        
        try:
            with open(file_path, 'rb') as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            # Return a placeholder for unreadable files
            return "error_reading_file"
    
    def _calculate_combined_hash(self, file_hashes: List[Dict[str, str]]) -> str:
        """Calculate a combined hash of all file hashes"""
        combined = hashlib.sha256()
        
        for file_info in sorted(file_hashes, key=lambda x: x['name']):
            combined.update(f"{file_info['name']}:{file_info['hash']}".encode())
            
        return combined.hexdigest()
    
    def get_latest_analysis(self, bucket_hours: int = 2) -> Dict[str, Any]:
        """Get complete analysis of evidence folders"""
        # Scan all folders
        runs = self.scan_evidence_folders()
        
        # Bucketize runs
        bucketized = self.bucketize_runs(runs, bucket_hours)
        
        # Detect duplicates
        duplicates = self.detect_duplicates(bucketized)
        
        # Calculate deltas
        deltas = self.calculate_deltas(runs)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'evidence_path': str(self.evidence_base_path),
            'bucket_hours': bucket_hours,
            'runs': runs,
            'bucketized': bucketized,
            'duplicates': duplicates,
            'deltas': deltas,
            'summary': {
                'total_controls': len(runs),
                'total_runs': sum(len(control_runs) for control_runs in runs.values()),
                'controls_with_duplicates': len(duplicates),
                'total_duplicate_sets': sum(len(dup_list) for dup_list in duplicates.values())
            }
        }