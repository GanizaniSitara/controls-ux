import React, { useState, useEffect } from 'react';
import './ControlScripts.css';

interface ControlStep {
  name: string;
  docstring: string;
  line_number: number;
  parameters: string[];
  script_name?: string;
}

type ControlScript = Record<string, ControlStep[]>;

interface ControlScriptsResponse {
  enabled: boolean;
  script_path?: string;
  scripts: ControlScript;
  total_scripts: number;
  total_steps: number;
}

const ControlScripts: React.FC = () => {
  const [scripts, setScripts] = useState<ControlScript>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedScripts, setExpandedScripts] = useState<Set<string>>(new Set());
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredScripts, setFilteredScripts] = useState<ControlScript>({});
  const [totalStats, setTotalStats] = useState({ scripts: 0, steps: 0 });

  useEffect(() => {
    fetchControlScripts();
  }, []);

  useEffect(() => {
    filterScripts();
  }, [scripts, searchQuery]);

  const fetchControlScripts = async () => {
    try {
      const response = await fetch('http://localhost:8002/api/control-scripts');
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data: ControlScriptsResponse = await response.json();
      
      if (!data.enabled) {
        setError('Control script discovery is disabled');
        setLoading(false);
        return;
      }
      
      setScripts(data.scripts);
      setTotalStats({ scripts: data.total_scripts, steps: data.total_steps });
      setFilteredScripts(data.scripts);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch control scripts');
    } finally {
      setLoading(false);
    }
  };

  const filterScripts = () => {
    if (!searchQuery.trim()) {
      setFilteredScripts(scripts);
      return;
    }

    const query = searchQuery.toLowerCase();
    const filtered: ControlScript = {};

    Object.entries(scripts).forEach(([scriptName, steps]) => {
      // Check if script name matches
      if (scriptName.toLowerCase().includes(query)) {
        filtered[scriptName] = steps as ControlStep[];
        return;
      }

      // Check if any step matches
      const typedSteps = steps as ControlStep[];
      const matchingSteps = typedSteps.filter((step: ControlStep) => 
        step.name.toLowerCase().includes(query) ||
        step.docstring.toLowerCase().includes(query) ||
        step.parameters.some((param: string) => param.toLowerCase().includes(query))
      );

      if (matchingSteps.length > 0) {
        filtered[scriptName] = steps as ControlStep[];
      }
    });

    setFilteredScripts(filtered);
  };

  const toggleScript = (scriptName: string) => {
    const newExpanded = new Set(expandedScripts);
    if (newExpanded.has(scriptName)) {
      newExpanded.delete(scriptName);
    } else {
      newExpanded.add(scriptName);
    }
    setExpandedScripts(newExpanded);
  };

  const getStepStatusClass = (stepName: string) => {
    // Mock status based on step name patterns
    if (stepName.includes('validate') || stepName.includes('check')) {
      return 'step-status-pass';
    } else if (stepName.includes('alert') || stepName.includes('breach')) {
      return 'step-status-warning';
    } else if (stepName.includes('error') || stepName.includes('fail')) {
      return 'step-status-fail';
    }
    return 'step-status-normal';
  };

  if (loading) {
    return (
      <div className="control-scripts-container">
        <h2>Control Scripts</h2>
        <div className="loading">Loading control scripts...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="control-scripts-container">
        <h2>Control Scripts</h2>
        <div className="error">Error: {error}</div>
      </div>
    );
  }

  const scriptEntries = Object.entries(filteredScripts);

  return (
    <div className="control-scripts-container">
      <div className="scripts-header">
        <h2>Control Scripts</h2>
        <div className="scripts-stats">
          <span className="stat">
            <span className="stat-value">{totalStats.scripts}</span>
            <span className="stat-label">Scripts</span>
          </span>
          <span className="stat">
            <span className="stat-value">{totalStats.steps}</span>
            <span className="stat-label">Total Steps</span>
          </span>
        </div>
      </div>

      <div className="search-bar">
        <input
          type="text"
          placeholder="Search scripts or steps..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="scripts-list">
        {scriptEntries.length === 0 ? (
          <div className="no-scripts">
            {searchQuery ? 'No scripts match your search' : 'No control scripts found'}
          </div>
        ) : (
          scriptEntries.map(([scriptName, steps]) => (
            <div key={scriptName} className="script-item">
              <div 
                className="script-header"
                onClick={() => toggleScript(scriptName)}
              >
                <span className="expand-icon">
                  {expandedScripts.has(scriptName) ? '▼' : '▶'}
                </span>
                <span className="script-name">{scriptName}</span>
                <span className="step-count">{steps.length} steps</span>
              </div>
              
              {expandedScripts.has(scriptName) && (
                <div className="steps-list">
                  {steps.map((step, index) => (
                    <div key={index} className="step-item">
                      <div className="step-header">
                        <span className={`step-name ${getStepStatusClass(step.name)}`}>
                          {step.name}
                        </span>
                        <span className="step-line">Line {step.line_number}</span>
                      </div>
                      <div className="step-description">{step.docstring}</div>
                      {step.parameters.length > 0 && (
                        <div className="step-parameters">
                          <span className="params-label">Parameters:</span>
                          {step.parameters.map((param, pIndex) => (
                            <span key={pIndex} className="parameter">{param}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default ControlScripts;