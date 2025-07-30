import React from 'react';
import { useParams } from 'react-router-dom';

const ControlDetail: React.FC = () => {
  const { controlId } = useParams<{ controlId: string }>();
  
  return (
    <div className="control-detail">
      <h2>Control Detail: {controlId}</h2>
      <p className="text-muted">Detailed control information coming soon...</p>
    </div>
  );
};

export default ControlDetail;