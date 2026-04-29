/**
 * CareSlot — Disease Detection Page
 * Combined Skin Analysis + PCOD/PCOS Assessment with tab toggle.
 */

import { useState } from 'react';
import { useLocation } from 'react-router-dom';
import SkinAnalysis from './SkinAnalysis';
import PCODAssessment from './PCODAssessment';
import { ScanEye, ClipboardList } from 'lucide-react';

export default function Detection() {
  const location = useLocation();
  const initialTab = location.state?.tab || 'skin';
  const [tab, setTab] = useState(initialTab);

  return (
    <div className="detect-page">
      <div className="detect-header">
        <div>
          <h1 className="detect-title">Health Detection</h1>
          <p className="detect-subtitle">AI-powered disease detection and risk assessment</p>
        </div>
      </div>

      {/* Tab toggle */}
      <div className="detect-tabs">
        <button
          className={`detect-tab ${tab === 'skin' ? 'detect-tab-active' : ''}`}
          onClick={() => setTab('skin')}
        >
          <ScanEye size={16} />
          Skin Analysis
          <span className="detect-tab-badge">MobileNetV2</span>
        </button>
        <button
          className={`detect-tab ${tab === 'pcod' ? 'detect-tab-active' : ''}`}
          onClick={() => setTab('pcod')}
        >
          <ClipboardList size={16} />
          PCOS / PCOD
          <span className="detect-tab-badge">Risk Score</span>
        </button>
      </div>

      {/* Content */}
      <div className="detect-content">
        {tab === 'skin' ? <SkinAnalysis /> : <PCODAssessment />}
      </div>
    </div>
  );
}
