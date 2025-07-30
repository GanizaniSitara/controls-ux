import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import './EvidenceGrid.css';

interface EvidenceGridProps {
  analysis: any;
  selectedControl?: string | null;
}

interface GridCell {
  status: 'present' | 'missing' | 'changed' | 'unchanged' | 'added' | 'not run';
  hash?: string;
  fileCount?: number;
}

const EvidenceGrid: React.FC<EvidenceGridProps> = ({ analysis, selectedControl }) => {
  const [gridData, setGridData] = useState<any>({});
  const [timeSlots, setTimeSlots] = useState<string[]>([]);
  const [controlSteps, setControlSteps] = useState<any[]>([]);
  const [slotToBucketMap, setSlotToBucketMap] = useState<Record<string, string>>({});
  const navigate = useNavigate();

  useEffect(() => {
    if (!analysis || !analysis.bucketized) return;

    // Build grid data structure
    const grid: any = {};
    const allTimeSlots = new Set<string>();
    const allControlSteps: any[] = [];
    const slotToBucket: Record<string, string> = {};

    // Process each control
    Object.entries(analysis.bucketized).forEach(([controlId, buckets]: [string, any]) => {
      const controlSteps = new Map<string, Set<string>>();
      
      // First pass - collect all steps across all buckets
      Object.entries(buckets).forEach(([bucketTime, runs]: [string, any]) => {
        runs.forEach((run: any) => {
          run.files.forEach((file: any) => {
            const stepMatch = file.name.match(/^(STEP\d+[a-z]?)_/);
            if (stepMatch) {
              const step = stepMatch[1];
              if (!controlSteps.has(step)) {
                controlSteps.set(step, new Set());
              }
              controlSteps.get(step)?.add(file.name);
            }
          });
        });
      });

      // Build grid for this control
      Object.entries(buckets).forEach(([bucketTime, runs]: [string, any]) => {
        const timeSlot = formatTimeSlot(bucketTime);
        allTimeSlots.add(timeSlot);
        slotToBucket[timeSlot] = bucketTime;

        // Process each step for this control
        controlSteps.forEach((fileNames, step) => {
          const gridKey = `${controlId}|${step}`;
          if (!grid[gridKey]) {
            grid[gridKey] = {
              controlId,
              step,
              cells: {}
            };
          }

          // Check status for this time slot
          if (runs.length === 0) {
            grid[gridKey].cells[timeSlot] = { status: 'not run' };
          } else {
            // Check files in the most recent run of this bucket
            const latestRun = runs[runs.length - 1];
            const stepFiles = latestRun.files.filter((f: any) => 
              fileNames.has(f.name)
            );

            if (stepFiles.length === 0) {
              grid[gridKey].cells[timeSlot] = { status: 'missing' };
            } else {
              // Check if changed from previous bucket
              const status = checkChangeStatus(
                controlId, 
                step, 
                bucketTime, 
                analysis
              );
              grid[gridKey].cells[timeSlot] = {
                status,
                fileCount: stepFiles.length,
                hash: latestRun.total_hash
              };
            }
          }
        });
      });

      // Add control steps to list
      // Filter by selected control if provided
      if (!selectedControl || selectedControl === controlId) {
        controlSteps.forEach((_, step) => {
          allControlSteps.push({ controlId, step });
        });
      }
    });

    // Sort time slots chronologically
    const sortedTimeSlots = Array.from(allTimeSlots).sort();
    
    // Sort control steps
    allControlSteps.sort((a, b) => {
      if (a.controlId !== b.controlId) {
        return a.controlId.localeCompare(b.controlId);
      }
      return a.step.localeCompare(b.step);
    });

    setTimeSlots(sortedTimeSlots);
    setControlSteps(allControlSteps);
    setGridData(grid);
    setSlotToBucketMap(slotToBucket);
  }, [analysis]);

  const formatTimeSlot = (isoTime: string) => {
    const date = new Date(isoTime);
    // Format as ISO-style: YYYY-MM-DD\nHH:MM
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}\n${hours}:${minutes}`;
  };

  const checkChangeStatus = (
    controlId: string, 
    step: string, 
    currentBucket: string,
    analysis: any
  ): 'present' | 'unchanged' | 'changed' | 'added' => {
    // Find deltas for this control
    const deltas = analysis.deltas[controlId] || [];
    
    // Get all bucket times sorted
    const bucketTimes = Object.keys(analysis.bucketized[controlId]).sort();
    const currentIndex = bucketTimes.indexOf(currentBucket);
    
    if (currentIndex === 0) {
      return 'present'; // First occurrence
    }

    // Check if files for this step changed
    const relevantDeltas = deltas.filter((d: any) => {
      const deltaTime = new Date(d.to_timestamp);
      const bucketTime = new Date(currentBucket);
      return Math.abs(deltaTime.getTime() - bucketTime.getTime()) < 2 * 60 * 60 * 1000; // Within 2 hours
    });

    for (const delta of relevantDeltas) {
      const stepFiles = [...delta.changed, ...delta.added].filter(f => 
        typeof f === 'string' ? f.startsWith(`${step}_`) : f.name?.startsWith(`${step}_`)
      );
      
      if (stepFiles.length > 0) {
        if (delta.added.some((f: any) => 
          typeof f === 'string' ? f.startsWith(`${step}_`) : f.name?.startsWith(`${step}_`)
        )) {
          return 'added';
        }
        return 'changed';
      }
    }

    return 'unchanged';
  };

  const getCellClass = (status: string) => {
    switch (status) {
      case 'present': return 'cell-present';
      case 'missing': return 'cell-missing';
      case 'changed': return 'cell-changed';
      case 'unchanged': return 'cell-unchanged';
      case 'added': return 'cell-added';
      case 'not run': return 'cell-not-run';
      default: return '';
    }
  };

  const getCellContent = (cell: GridCell | undefined) => {
    if (!cell) return '';
    
    switch (cell.status) {
      case 'present': return 'present';
      case 'missing': return 'missing';
      case 'changed': return 'changed';
      case 'unchanged': return 'unchanged';
      case 'added': return 'added';
      case 'not run': return 'not run';
      default: return '';
    }
  };

  return (
    <div className="evidence-grid-container">
      <h3>Control Execution Grid</h3>
      <div className="grid-wrapper">
        <table className="evidence-grid">
          <thead>
            <tr>
              <th className="control-header">CONTROL</th>
              <th className="step-header">STEP</th>
              {timeSlots.map(slot => (
                <th key={slot} className="time-header">
                  <div className="time-slot">{slot}</div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {controlSteps.map(({ controlId, step }, idx) => {
              const gridKey = `${controlId}|${step}`;
              const rowData = gridData[gridKey];
              
              return (
                <tr key={gridKey}>
                  {idx === 0 || controlSteps[idx - 1].controlId !== controlId ? (
                    <td className="control-cell" rowSpan={
                      controlSteps.filter(cs => cs.controlId === controlId).length
                    }>
                      {controlId}
                    </td>
                  ) : null}
                  <td className="step-cell">{step}_*</td>
                  {timeSlots.map(slot => {
                    const cell = rowData?.cells[slot];
                    return (
                      <td 
                        key={`${gridKey}-${slot}`} 
                        className={`status-cell ${getCellClass(cell?.status || '')} ${cell ? 'clickable' : ''}`}
                        onClick={() => {
                          if (cell && cell.status !== 'not run' && cell.status !== 'missing') {
                            // Find the corresponding run folder for this control and time slot
                            const bucketTime = slotToBucketMap[slot];
                            const runs = analysis.bucketized[controlId]?.[bucketTime];
                            if (runs && runs.length > 0) {
                              const latestRun = runs[runs.length - 1];
                              // Navigate to evidence report
                              const folderName = latestRun.folder_name || controlId;
                              window.open(`http://localhost:8002/evidence/${folderName}/Evidence_report.html`, '_blank');
                            }
                          }
                        }}
                      >
                        <span className="status-text">
                          {getCellContent(cell)}
                        </span>
                        {cell?.fileCount && (
                          <span className="file-count">({cell.fileCount})</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      
      <div className="grid-legend">
        <h4>Legend:</h4>
        <div className="legend-items">
          <span className="legend-item">
            <span className="legend-color cell-present"></span> present
          </span>
          <span className="legend-item">
            <span className="legend-color cell-missing"></span> missing
          </span>
          <span className="legend-item">
            <span className="legend-color cell-changed"></span> changed
          </span>
          <span className="legend-item">
            <span className="legend-color cell-unchanged"></span> unchanged
          </span>
          <span className="legend-item">
            <span className="legend-color cell-added"></span> added
          </span>
          <span className="legend-item">
            <span className="legend-color cell-not-run"></span> not run
          </span>
        </div>
      </div>
    </div>
  );
};

export default EvidenceGrid;