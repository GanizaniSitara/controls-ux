import React, { useState, useMemo } from 'react';
import { gql, useQuery } from '@apollo/client';
import './Overview.css'; // Reuse the CSS for fitness functions styling

const GET_RULE_FITNESS_FUNCTIONS = gql`
  query GetRuleFitnessFunctions {
    ruleFitnessFunctions {
      id
      name
      description
      ruleId
      passingCount
      warningCount
      failingCount
      totalCount
      passingPercentage
    }
  }
`;

function FitnessFunctions() {
  const { loading, error, data } = useQuery(GET_RULE_FITNESS_FUNCTIONS);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  const sortedData = useMemo(() => {
    if (!data || !sortColumn) return data?.ruleFitnessFunctions || [];

    const sorted = [...data.ruleFitnessFunctions].sort((a: any, b: any) => {
      let aValue = a[sortColumn];
      let bValue = b[sortColumn];

      // Handle numeric values
      if (['passingPercentage', 'passingCount', 'warningCount', 'failingCount', 'totalCount'].includes(sortColumn)) {
        aValue = Number(aValue) || 0;
        bValue = Number(bValue) || 0;
      } else {
        // Convert to string for text comparison
        aValue = String(aValue || '').toLowerCase();
        bValue = String(bValue || '').toLowerCase();
      }

      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return sorted;
  }, [data, sortColumn, sortDirection]);

  const getSortIndicator = (column: string) => {
    if (sortColumn !== column) return '';
    return sortDirection === 'asc' ? ' ▲' : ' ▼';
  };

  if (loading) return <p>Loading fitness functions...</p>;
  if (error) return <p>Error loading fitness functions: {error.message}</p>;
  if (!data || !data.ruleFitnessFunctions || data.ruleFitnessFunctions.length === 0) {
    return (
      <div className="fitness-functions-table">
        <h2>Fitness Functions</h2>
        <p>No fitness functions available. Make sure the cache has been populated with rule results.</p>
      </div>
    );
  }

  return (
    <div className="fitness-functions-table">
      <h2>Fitness Functions</h2>
      <table>
        <thead>
          <tr>
            <th onClick={() => handleSort('name')} className="sortable">
              Name{getSortIndicator('name')}
            </th>
            <th onClick={() => handleSort('description')} className="sortable">
              Description{getSortIndicator('description')}
            </th>
            <th onClick={() => handleSort('passingPercentage')} className="sortable">
              Pass %{getSortIndicator('passingPercentage')}
            </th>
            <th onClick={() => handleSort('passingCount')} className="sortable">
              Passing{getSortIndicator('passingCount')}
            </th>
            <th onClick={() => handleSort('warningCount')} className="sortable">
              Warning{getSortIndicator('warningCount')}
            </th>
            <th onClick={() => handleSort('failingCount')} className="sortable">
              Failing{getSortIndicator('failingCount')}
            </th>
            <th onClick={() => handleSort('totalCount')} className="sortable">
              Total Apps{getSortIndicator('totalCount')}
            </th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((fn: any) => (
            <tr key={fn.id} className={fn.passingPercentage >= 80 ? 'good' : fn.passingPercentage >= 60 ? 'warning' : 'failing'}>
              <td className="function-name">{fn.name}</td>
              <td className="function-description">{fn.description}</td>
              <td className="percentage">
                <div className="percentage-bar">
                  <div 
                    className="percentage-fill"
                    style={{ 
                      width: `${fn.passingPercentage}%`,
                      backgroundColor: fn.passingPercentage >= 80 ? '#4caf50' : fn.passingPercentage >= 60 ? '#ff9800' : '#f44336'
                    }}
                  />
                  <span className="percentage-text">{Math.round(fn.passingPercentage)}%</span>
                </div>
              </td>
              <td className="count passing-count">{fn.passingCount}</td>
              <td className="count warning-count">{fn.warningCount}</td>
              <td className="count failing-count">{fn.failingCount}</td>
              <td className="count total-count">{fn.totalCount}</td>
              <td>
                <span className={`status-badge ${fn.passingPercentage >= 80 ? 'status-good' : fn.passingPercentage >= 60 ? 'status-warning' : 'status-failing'}`}>
                  {fn.passingPercentage >= 80 ? 'GOOD' : fn.passingPercentage >= 60 ? 'NEEDS ATTENTION' : 'CRITICAL'}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default FitnessFunctions;