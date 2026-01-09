import { useEffect, useState } from 'react';
import { SigmaContainer, useRegisterEvents, useLoadGraph, useSigma } from '@react-sigma/core';
import Graph from 'graphology';
import type { GraphData, PatientInfo } from '../types';

interface GraphVisualizationProps {
  onNodeHover: (info: PatientInfo | null) => void;
}

const LoadGraph = ({ data }: { data: GraphData }) => {
  const loadGraph = useLoadGraph();
  const sigma = useSigma();

  useEffect(() => {
    const graph = new Graph({ multi: true });
    
    // Add nodes
    data.nodes.forEach((node) => {
      graph.addNode(String(node.id), {
        label: node.label,
        x: node.x,
        y: node.y,
        size: node.size,
        color: node.color || node._color || '#666',
        full_name: node.full_name,
        onset_date: node.onset_date,
        announce_date: node.announce_date,
        pagerank: node.pagerank,
      });
    });

    // Add edges
    data.edges.forEach((edge) => {
      try {
        graph.addEdgeWithKey(String(edge.id), String(edge.source), String(edge.target), {
          size: edge.size,
          color: edge.color || edge._color || '#ccc',
          type: 'curve',
          // Store original type as data if needed, but don't use it for rendering type unless valid
          relation_type: edge.type, 
          weight: edge.weight,
        });
      } catch (error) {
      console.error(`Failed to add edge ${edge.source} -> ${edge.target}:`, error);
    }
    });

    sigma.getGraph().clear();
    loadGraph(graph);
  }, [loadGraph, data, sigma]);

  return null;
};

const GraphEvents = ({ onNodeHover }: { onNodeHover: (info: PatientInfo | null) => void }) => {
  const registerEvents = useRegisterEvents();
  const sigma = useSigma();

  useEffect(() => {
    registerEvents({
      enterNode: (event) => {
        const nodeAttributes = sigma.getGraph().getNodeAttributes(event.node);
        onNodeHover({
          full_name: nodeAttributes.full_name,
          onset_date: nodeAttributes.onset_date,
          announce_date: nodeAttributes.announce_date,
          pagerank: nodeAttributes.pagerank,
        });
      },
      leaveNode: () => {
        onNodeHover(null);
      },
    });
  }, [registerEvents, sigma, onNodeHover]);

  return null;
};

export const GraphVisualization = ({ onNodeHover }: GraphVisualizationProps) => {
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('/data.json')
      .then((response) => {
        if (!response.ok) {
          throw new Error('Failed to load graph data');
        }
        return response.json();
      })
      .then((data: GraphData) => {
        setGraphData(data);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="loading">Loading graph data...</div>;
  }

    if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!graphData) {
    return <div className="error">No graph data available</div>;
  }

  return (
    <SigmaContainer
      style={{ height: '100%', width: '100%', position: 'absolute', top: 0, left: 0 }}
      graphOptions={{ multi: true }}
      settings={{
        defaultEdgeType: 'curve',
        renderEdgeLabels: false,
        enableEdgeEvents: true,
        allowInvalidContainer: true,
      }}
    >
      <LoadGraph data={graphData} />
      <GraphEvents onNodeHover={onNodeHover} />
    </SigmaContainer>
  );
};
