import React, { useState, useMemo } from 'react';
import { gql, useQuery } from '@apollo/client';
import './Overview.css'; // We'll create this CSS file for styling

// Re-use the GraphQL queries from App.tsx (or move them to a separate file)
const GET_FITNESS_FUNCTIONS = gql`
  query GetFitnessFunctions {
    fitnessFunctions {
      id
      name
      domain
      description
      isPassing
      appCount
      providerType
      dataStatus
    }
  }
`;

// FitnessFunctionsList component (moved from App.tsx)
function FitnessFunctionsList() {
  const { loading, error, data } = useQuery(GET_FITNESS_FUNCTIONS);
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
    if (!data || !sortColumn) return data?.fitnessFunctions || [];

    const sorted = [...data.fitnessFunctions].sort((a: any, b: any) => {
      let aValue = a[sortColumn];
      let bValue = b[sortColumn];

      // Handle numeric values (like appCount)
      if (sortColumn === 'appCount') {
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

  if (loading) return <p>Loading fitness functions...</p>;
  if (error) return <p>Error loading fitness functions: {error.message}</p>;

  const getSortIndicator = (column: string) => {
    if (sortColumn !== column) return '';
    return sortDirection === 'asc' ? ' ▲' : ' ▼';
  };

  return (
    <div className="fitness-functions-list">
      <h2>Data Sets</h2>      <table>
        <thead>
          <tr>
            <th onClick={() => handleSort('name')} className="sortable">
              Name{getSortIndicator('name')}
            </th>
            <th onClick={() => handleSort('domain')} className="sortable">
              Domain{getSortIndicator('domain')}
            </th>
            <th onClick={() => handleSort('description')} className="sortable">
              Description{getSortIndicator('description')}
            </th>
            <th onClick={() => handleSort('appCount')} className="sortable">
              App Count{getSortIndicator('appCount')}
            </th>
            <th onClick={() => handleSort('dataStatus')} className="sortable">
              Data Status{getSortIndicator('dataStatus')}
            </th>
          </tr>
        </thead>
        <tbody>
          {sortedData.map((fn: any) => (
            <tr key={fn.id} className={fn.isPassing ? 'passing' : 'failing'}>
              <td>{fn.name}</td>
              <td>{fn.domain}</td>
              <td>{fn.description}</td>
              <td>{fn.appCount}</td>
              <td>
                <span className={`status-indicator ${fn.dataStatus.toLowerCase().replace(' ', '-')}`}>
                  {fn.dataStatus}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Overview() {
  return (
    <>
      <FitnessFunctionsList />
    </>
  );
}

export default Overview;
