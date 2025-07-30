import React, { useState, useEffect } from 'react';
import { gql, useQuery, useLazyQuery, useMutation } from '@apollo/client';
import Editor from '@monaco-editor/react';
import './FitnessFunctionEditor.css';

// GraphQL queries
const LIST_FITNESS_FUNCTIONS = gql`
  query ListFitnessFunctions {
    fitnessFunctionList {
      id
      name
      description
      ruleId
      moduleName
      className
    }
  }
`;

const GET_FITNESS_FUNCTION_SOURCE = gql`
  query GetFitnessFunctionSource($moduleName: String!) {
    fitnessFunctionSource(moduleName: $moduleName) {
      moduleName
      sourceCode
      filePath
    }
  }
`;

const SAVE_FITNESS_FUNCTION = gql`
  mutation SaveFitnessFunction($moduleName: String!, $sourceCode: String!) {
    saveFitnessFunction(moduleName: $moduleName, sourceCode: $sourceCode) {
      status
      message
      line
      offset
      details
    }
  }
`;

interface FitnessFunction {
  id: string;
  name: string;
  description: string;
  ruleId: string;
  moduleName: string;
  className: string;
}

interface FitnessFunctionSource {
  moduleName: string;
  sourceCode: string;
  filePath: string;
}

interface DataSchema {
  [key: string]: {
    name: string;
    fields: { [key: string]: string };
    sample_apps: string[];
    total_apps: number;
  };
}

const FitnessFunctionEditor: React.FC = () => {
  const [selectedFunction, setSelectedFunction] = useState<FitnessFunction | null>(null);
  const [sourceCode, setSourceCode] = useState<string>('');
  const [editedCode, setEditedCode] = useState<string>('');
  const [isEditing, setIsEditing] = useState<boolean>(false);
  const [saveStatus, setSaveStatus] = useState<{ type: 'success' | 'error' | 'info' | null; message: string }>({ type: null, message: '' });
  const [dataSchema, setDataSchema] = useState<DataSchema>({});
  const [expandedFeeds, setExpandedFeeds] = useState<Set<string>>(new Set());
  const [showNewDialog, setShowNewDialog] = useState<boolean>(false);
  const [newFunctionName, setNewFunctionName] = useState<string>('');
  const [newFunctionDescription, setNewFunctionDescription] = useState<string>('');

  // Query to get list of fitness functions
  const { loading: listLoading, error: listError, data: listData } = useQuery(LIST_FITNESS_FUNCTIONS);

  // Lazy query to get source code when needed
  const [getSource, { loading: sourceLoading, data: sourceData }] = useLazyQuery(
    GET_FITNESS_FUNCTION_SOURCE,
    {
      onCompleted: (data) => {
        if (data.fitnessFunctionSource) {
          setSourceCode(data.fitnessFunctionSource.sourceCode);
          setEditedCode(data.fitnessFunctionSource.sourceCode);
          setIsEditing(false);
          setSaveStatus({ type: null, message: '' });
        }
      },
    }
  );

  // Mutation to save fitness function
  const [saveFitnessFunction, { loading: saveLoading }] = useMutation(SAVE_FITNESS_FUNCTION);

  // Fetch data schema on component mount
  useEffect(() => {
    fetch('http://localhost:8002/api/data-schema')
      .then(res => res.json())
      .then(data => {
        if (data.schema) {
          setDataSchema(data.schema);
        }
      })
      .catch(err => console.error('Error fetching data schema:', err));
  }, []);

  // Add class to body for full-width layout
  useEffect(() => {
    document.body.classList.add('fitness-editor-active');
    return () => {
      document.body.classList.remove('fitness-editor-active');
    };
  }, []);

  // Toggle feed expansion
  const toggleFeed = (feedId: string) => {
    const newExpanded = new Set(expandedFeeds);
    if (newExpanded.has(feedId)) {
      newExpanded.delete(feedId);
    } else {
      newExpanded.add(feedId);
    }
    setExpandedFeeds(newExpanded);
  };

  // Load source when a function is selected
  useEffect(() => {
    if (selectedFunction) {
      getSource({ variables: { moduleName: selectedFunction.moduleName } });
    }
  }, [selectedFunction, getSource]);

  if (listLoading) return <div className="loading">Loading fitness functions...</div>;
  if (listError) return <div className="error">Error loading fitness functions: {listError.message}</div>;

  const fitnessFunctions: FitnessFunction[] = listData?.fitnessFunctionList || [];

  return (
    <div className="fitness-function-editor">
      <h2>Fitness Function Editor</h2>
      
      <div className="editor-layout three-panel">
        {/* Left panel - Function list */}
        <div className="function-list-panel">
          <div className="panel-header-with-action">
            <h3>Available Functions</h3>
            <button 
              className="btn btn-new"
              onClick={() => setShowNewDialog(true)}
            >
              + New
            </button>
          </div>
          <div className="function-list">
            {fitnessFunctions.map((func) => (
              <div
                key={func.id}
                className={`function-item ${selectedFunction?.id === func.id ? 'selected' : ''}`}
                onClick={() => setSelectedFunction(func)}
              >
                <div className="function-name">{func.name}</div>
                <div className="function-module">{func.moduleName}.py</div>
                <div className="function-description">{func.description}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Right panel - Source code viewer */}
        <div className="source-code-panel">
          {selectedFunction ? (
            <>
              <div className="source-header">
                <h3>{selectedFunction.name}</h3>
                <div className="source-meta">
                  <span className="file-path">📁 {selectedFunction.moduleName}.py</span>
                  <span className="class-name">🏷️ {selectedFunction.className}</span>
                </div>
              </div>
              
              <div className="source-actions">
                <button 
                  className="btn btn-edit"
                  onClick={() => {
                    setIsEditing(!isEditing);
                    if (!isEditing) {
                      setEditedCode(sourceCode);
                    }
                  }}
                  disabled={sourceLoading}
                >
                  {isEditing ? 'Cancel Edit' : 'Edit'}
                </button>
                {isEditing && (
                  <button 
                    className="btn btn-save"
                    onClick={async () => {
                      setSaveStatus({ type: 'info', message: 'Saving...' });
                      try {
                        const result = await saveFitnessFunction({
                          variables: {
                            moduleName: selectedFunction.moduleName,
                            sourceCode: editedCode
                          }
                        });
                        
                        const saveResult = result.data.saveFitnessFunction;
                        if (saveResult.status === 'success') {
                          setSaveStatus({ type: 'success', message: saveResult.message });
                          setSourceCode(editedCode);
                          setIsEditing(false);
                          // Refresh the source after a successful save
                          setTimeout(() => {
                            getSource({ variables: { moduleName: selectedFunction.moduleName } });
                          }, 1000);
                        } else {
                          setSaveStatus({ 
                            type: 'error', 
                            message: `${saveResult.message}${saveResult.line ? ` (Line ${saveResult.line})` : ''}` 
                          });
                        }
                      } catch (error: any) {
                        setSaveStatus({ type: 'error', message: error.message || 'Failed to save' });
                      }
                    }}
                    disabled={saveLoading || editedCode === sourceCode}
                  >
                    {saveLoading ? 'Saving...' : 'Save'}
                  </button>
                )}
                {saveStatus.type && (
                  <div className={`save-status ${saveStatus.type}`}>
                    {saveStatus.message}
                  </div>
                )}
              </div>
              
              {sourceLoading ? (
                <div className="loading">Loading source code...</div>
              ) : (
                <div className="source-code-container">
                  {isEditing ? (
                    <Editor
                      height="100%"
                      defaultLanguage="python"
                      value={editedCode}
                      onChange={(value) => setEditedCode(value || '')}
                      theme="vs-dark"
                      options={{
                        minimap: { enabled: false },
                        fontSize: 14,
                        lineNumbers: 'on',
                        renderWhitespace: 'selection',
                        scrollBeyondLastLine: false,
                        automaticLayout: true,
                        tabSize: 4,
                      }}
                    />
                  ) : (
                    <pre className="source-code">
                      <code className="language-python">{sourceCode}</code>
                    </pre>
                  )}
                </div>
              )}
            </>
          ) : (
            <div className="no-selection">
              <p>Select a fitness function to view its source code</p>
            </div>
          )}
        </div>

        {/* Right panel - Data Dictionary */}
        <div className="data-dictionary-panel">
          <h3>Data Dictionary</h3>
          <div className="data-feeds-list">
            {Object.entries(dataSchema).map(([feedId, feed]) => (
              <div key={feedId} className="data-feed">
                <div 
                  className="feed-header"
                  onClick={() => toggleFeed(feedId)}
                >
                  <span className="feed-toggle">
                    {expandedFeeds.has(feedId) ? '▼' : '▶'}
                  </span>
                  <span className="feed-name">{feed.name}</span>
                  <span className="feed-count">({feed.total_apps} apps)</span>
                </div>
                {expandedFeeds.has(feedId) && (
                  <div className="feed-details">
                    <div className="feed-id">ID: {feedId}</div>
                    <div className="fields-section">
                      <h4>Fields:</h4>
                      <table className="fields-table">
                        <thead>
                          <tr>
                            <th>Field Name</th>
                            <th>Type</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(feed.fields).map(([fieldName, fieldType]) => (
                            <tr key={fieldName}>
                              <td className="field-name">{fieldName}</td>
                              <td className="field-type">{fieldType}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                    <div className="sample-apps">
                      <h4>Sample Apps:</h4>
                      <ul>
                        {feed.sample_apps.map((app, idx) => (
                          <li key={idx}>{app}</li>
                        ))}
                      </ul>
                    </div>
                    <div className="usage-example">
                      <h4>Usage Example:</h4>
                      <pre className="code-snippet">
                        <code>{`# Access data for this feed
data = rule_results.get('${feedId}', {})
for app_id, app_data in data.items():
    # Access fields
${Object.keys(feed.fields).slice(0, 2).map(field => `    ${field} = app_data.get('${field}')`).join('\n')}`}</code>
                      </pre>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="editor-info">
        <p>
          <strong>Fitness Function Editor:</strong> Click "Edit" to modify fitness functions. Changes are validated 
          and hot-reloaded on save. Invalid Python code will be automatically reverted.
        </p>
        <p style={{ marginTop: '10px' }}>
          <strong>Pro Tip:</strong> Use the CacheAccessor class for easy data access: 
          <code style={{ backgroundColor: '#f0f0f0', padding: '2px 6px', borderRadius: '3px', marginLeft: '5px' }}>
            from fitness_logic.cache_accessor import CacheAccessor
          </code>
        </p>
      </div>

      {/* New Function Dialog */}
      {showNewDialog && (
        <div className="dialog-overlay" onClick={() => setShowNewDialog(false)}>
          <div className="dialog" onClick={(e) => e.stopPropagation()}>
            <h3>Create New Fitness Function</h3>
            <div className="form-group">
              <label>Name:</label>
              <input
                type="text"
                value={newFunctionName}
                onChange={(e) => setNewFunctionName(e.target.value)}
                placeholder="e.g., Security Compliance Score"
                autoFocus
              />
            </div>
            <div className="form-group">
              <label>Description:</label>
              <textarea
                value={newFunctionDescription}
                onChange={(e) => setNewFunctionDescription(e.target.value)}
                placeholder="e.g., Evaluates applications for security compliance based on vulnerability scans and security policies"
                rows={3}
              />
            </div>
            <div className="dialog-actions">
              <button 
                className="btn btn-cancel"
                onClick={() => {
                  setShowNewDialog(false);
                  setNewFunctionName('');
                  setNewFunctionDescription('');
                }}
              >
                Cancel
              </button>
              <button 
                className="btn btn-create"
                onClick={async () => {
                  if (!newFunctionName.trim()) {
                    alert('Please enter a function name');
                    return;
                  }
                  
                  try {
                    const response = await fetch('http://localhost:8002/api/fitness-functions/create', {
                      method: 'POST',
                      headers: {
                        'Content-Type': 'application/json',
                      },
                      body: JSON.stringify({
                        name: newFunctionName,
                        description: newFunctionDescription
                      })
                    });
                    
                    const result = await response.json();
                    
                    if (response.ok) {
                      // Refresh the function list
                      window.location.reload();
                    } else {
                      alert(result.detail || 'Failed to create fitness function');
                    }
                  } catch (error) {
                    alert('Error creating fitness function');
                  }
                }}
                disabled={!newFunctionName.trim()}
              >
                Create
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default FitnessFunctionEditor;