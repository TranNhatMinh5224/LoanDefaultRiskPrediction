import React, { useState } from 'react';
import MainLayout from '../components/layout/MainLayout';
import PredictForm from '../features/prediction/components/PredictForm';
import BatchPredictForm from '../features/prediction/components/BatchPredictForm';

const DashboardPage = () => {
  const [activeTab, setActiveTab] = useState('single');

  const tabStyle = (isActive) => ({
    padding: '0.85rem 1.5rem',
    cursor: 'pointer',
    borderBottom: isActive ? '3px solid #2563eb' : '3px solid transparent',
    color: isActive ? '#2563eb' : '#64748b',
    fontWeight: isActive ? '700' : '500',
    background: 'none',
    borderTop: 'none',
    borderLeft: 'none',
    borderRight: 'none',
    fontSize: '1rem',
    transition: 'all 0.2s',
  });

  return (
    <MainLayout>
      <div style={{ maxWidth: '1000px', margin: '0 auto 1.5rem auto', display: 'flex', gap: '1rem', borderBottom: '1px solid #e2e8f0' }}>
        <button style={tabStyle(activeTab === 'single')} onClick={() => setActiveTab('single')}>
          Dự đoán Đơn lẻ (Từng khách)
        </button>
        <button style={tabStyle(activeTab === 'batch')} onClick={() => setActiveTab('batch')}>
          Dự đoán Hàng loạt (Upload Excel)
        </button>
      </div>

      {activeTab === 'single' ? <PredictForm /> : <BatchPredictForm />}
    </MainLayout>
  );
};

export default DashboardPage;
