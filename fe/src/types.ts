export interface GraphNode {
  id: string;
  label: string;
  full_name: string;
  x: number;
  y: number;
  size: number;
  color: string;
  _color?: string;
  age_group?: string;
  onset_date: string;
  announce_date: string;
  pagerank: number;
}

export interface GraphEdge {
  id: string;
  source: string;
  target: string;
  weight: number;
  type: string;
  size: number;
  color: string;
  _color?: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface PatientInfo {
  full_name: string;
  onset_date: string;
  announce_date: string;
  pagerank: number;
}
