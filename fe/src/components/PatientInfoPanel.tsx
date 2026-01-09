import type { PatientInfo } from '../types';

interface PatientInfoPanelProps {
  patientInfo: PatientInfo | null;
}

export const PatientInfoPanel = ({ patientInfo }: PatientInfoPanelProps) => {
  return (
    <div className="info-box">
      <h3>Patient Information</h3>
      {patientInfo ? (
        <div className="info-content">
          <div className="info-row">
            <span className="info-label">Name:</span>
            <span className="info-value">{patientInfo.full_name}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Onset Date:</span>
            <span className="info-value">{patientInfo.onset_date}</span>
          </div>
          <div className="info-row">
            <span className="info-label">Announce Date:</span>
            <span className="info-value">{patientInfo.announce_date}</span>
          </div>
          <div className="info-row">
            <span className="info-label">PageRank:</span>
            <span className="info-value">{patientInfo.pagerank.toFixed(6)}</span>
          </div>
        </div>
      ) : (
        <p className="info-placeholder">Hover over a node to see patient details</p>
      )}
    </div>
  );
};
