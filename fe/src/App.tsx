import { useState } from 'react';
import { GraphVisualization } from './components/GraphVisualization';
import { PatientInfoPanel } from './components/PatientInfoPanel';
import type { PatientInfo } from './types';
import './App.css';

function App() {
  const [patientInfo, setPatientInfo] = useState<PatientInfo | null>(null);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Epidemic Transmission Network Visualization</h1>
        <p>Interactive COVID-19 case transmission network with PageRank analysis</p>
      </header>
      <div className="app-content">
        <GraphVisualization onNodeHover={setPatientInfo} />
        <PatientInfoPanel patientInfo={patientInfo} />
      </div>
    </div>
  );
}

export default App;
