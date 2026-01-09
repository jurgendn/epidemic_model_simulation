"""
Graph-based epidemic model calculator.

This module implements PageRank-based influence computation for epidemic spread
networks, following the approach described in the HUST report on graph-based
epidemic modeling.
"""

from neo4j import GraphDatabase
from igraph import Graph
import pandas as pd
import json
import random
import os
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EpidemicGraphCalculator:
    """Calculate epidemic spread metrics using graph-based PageRank analysis."""
    
    def __init__(self, neo4j_uri: str, username: str, password: str):
        """
        Initialize calculator with Neo4j connection.
        
        Args:
            neo4j_uri: Neo4j database URI
            username: Database username
            password: Database password
        """
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
        self.graph = None
        logger.info(f"Connected to Neo4j at {neo4j_uri}")
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def parse_neo4j_date(date_obj) -> datetime:
    """
    Parse Neo4j date object to Python datetime.
    
    Args:
        date_obj: Neo4j date object
    
    Returns:
        Python datetime object
    """
    date_str = '/'.join([str(date_obj.year), str(date_obj.month), str(date_obj.day)])
    return datetime.strptime(date_str, '%Y/%m/%d')


def fetch_all_nodes(calculator: EpidemicGraphCalculator) -> List[Any]:
    """
    Fetch all nodes from Neo4j database.
    
    Args:
        calculator: EpidemicGraphCalculator instance
    
    Returns:
        List of node records
    """
    with calculator.driver.session() as session:
        query = "MATCH (n) RETURN n"
        result = session.run(query).values()
    logger.info(f"Fetched {len(result)} nodes from Neo4j")
    return result


def fetch_all_edges(calculator: EpidemicGraphCalculator) -> List[Any]:
    """
    Fetch all edges (relationships) from Neo4j database.
    
    Args:
        calculator: EpidemicGraphCalculator instance
    
    Returns:
        List of edge records (source, target, relationship)
    """
    with calculator.driver.session() as session:
        query = """
        MATCH (s)-[r]->(t)
        RETURN s, t, r
        """
        result = session.run(query).values()
    logger.info(f"Fetched {len(result)} edges from Neo4j")
    return result


def build_igraph_nodes(graph: Graph, nodes: List[Any]) -> None:
    """
    Add nodes to igraph Graph with attributes.
    
    Args:
        graph: igraph Graph object
        nodes: List of node records from Neo4j
    """
    for i, node_record in enumerate(nodes):
        node = node_record[0]
        
        # Add vertex
        graph.add_vertex(name=node['name'])
        
        # Set attributes
        graph.vs[i]['age_group'] = node['age_group']
        graph.vs[i]['full_name'] = node['full_name']
        graph.vs[i]['label'] = node.labels
        graph.vs[i]['onset_date'] = parse_neo4j_date(node['onset_date'])
        graph.vs[i]['announce_date'] = parse_neo4j_date(node['announce_date'])
        graph.vs[i]['pagerank'] = 0.0  # Will be computed later
    
    logger.info(f"Built {len(nodes)} nodes in igraph")


def build_igraph_edges(graph: Graph, edges: List[Any]) -> None:
    """
    Add edges to igraph Graph with attributes.
    
    Args:
        graph: igraph Graph object
        edges: List of edge records from Neo4j
    """
    for edge_record in edges:
        source_node = edge_record[0]
        target_node = edge_record[1]
        relationship = edge_record[2]
        
        # Add edge with random weight and relationship type
        graph.add_edge(
            source_node['name'],
            target_node['name'],
            weight=random.random(),
            r_type=relationship.type
        )
    
    logger.info(f"Built {len(edges)} edges in igraph")


def create_igraph_from_csv(csv_filepath: str) -> Graph:
    """
    Create igraph Graph directly from CSV file (fallback when Neo4j is unavailable).
    
    Args:
        csv_filepath: Path to relationship CSV file
    
    Returns:
        igraph Graph object with nodes and edges
    """
    # Load data
    df = pd.read_csv(csv_filepath)
    logger.info(f"Loaded {len(df)} records from {csv_filepath}")
    
    # Create undirected graph
    graph = Graph(directed=False)
    
    # Get unique nodes
    all_nodes = set(df['source'].unique()) | set(df['target'].unique())
    all_nodes = sorted([n for n in all_nodes if n != '0'])  # Remove unknown source
    
    # Create node name to index mapping
    node_to_idx = {name: idx for idx, name in enumerate(all_nodes)}
    
    # Add vertices with attributes
    for node_name in all_nodes:
        # Get node data from first occurrence
        node_data = df[df['target'] == node_name].iloc[0] if len(df[df['target'] == node_name]) > 0 else None
        
        graph.add_vertex(name=node_name)
        idx = node_to_idx[node_name]
        
        if node_data is not None:
            graph.vs[idx]['age_group'] = str(node_data['age_group'])
            graph.vs[idx]['full_name'] = str(node_data['name'])
            graph.vs[idx]['onset_date'] = pd.to_datetime(node_data['onset_date'])
            graph.vs[idx]['announce_date'] = pd.to_datetime(node_data['announce_date'])
        else:
            graph.vs[idx]['age_group'] = '0'
            graph.vs[idx]['full_name'] = node_name
            graph.vs[idx]['onset_date'] = datetime.now()
            graph.vs[idx]['announce_date'] = datetime.now()
        
        graph.vs[idx]['label'] = [f'G{graph.vs[idx]["age_group"]}']
        graph.vs[idx]['pagerank'] = 0.0
    
    # Add edges
    for _, row in df.iterrows():
        source = row['source']
        target = row['target']
        
        # Skip unknown sources
        if source == '0' or source not in node_to_idx or target not in node_to_idx:
            continue
        
        # Add edge with attributes
        rel_type = row.get('relationship', '0')
        graph.add_edge(
            node_to_idx[source],
            node_to_idx[target],
            weight=random.random(),
            r_type=rel_type
        )
    
    logger.info(f"Created igraph with {len(graph.vs)} vertices and {len(graph.es)} edges")
    return graph


def create_igraph_from_neo4j(calculator: EpidemicGraphCalculator) -> Graph:
    """
    Create igraph Graph from Neo4j data.
    
    Args:
        calculator: EpidemicGraphCalculator instance
    
    Returns:
        igraph Graph object with nodes and edges
    """
    # Fetch data from Neo4j
    nodes = fetch_all_nodes(calculator)
    edges = fetch_all_edges(calculator)
    
    # Create undirected graph (as per the model)
    graph = Graph(directed=False)
    
    # Build graph structure
    build_igraph_nodes(graph, nodes)
    build_igraph_edges(graph, edges)
    
    logger.info(f"Created igraph with {len(graph.vs)} vertices and {len(graph.es)} edges")
    return graph


def find_node_cluster(clusters: List[List[int]], node_id: int) -> int:
    """
    Find which cluster a node belongs to.
    
    Args:
        clusters: List of clusters (each cluster is a list of node IDs)
        node_id: Node ID to find
    
    Returns:
        Cluster index
    """
    for i, cluster in enumerate(clusters):
        if node_id in cluster:
            return i
    return 0


def generate_cluster_colors(num_clusters: int) -> List[str]:
    """
    Generate random colors for each cluster.
    
    Args:
        num_clusters: Number of clusters
    
    Returns:
        List of hex color strings
    """
    colors = []
    for _ in range(num_clusters):
        random_number = random.randint(0, 16777215)
        hex_color = f'#{random_number:06x}'
        colors.append(hex_color)
    return colors


def compute_clusters(graph: Graph, mode: str = 'clusters') -> List[List[int]]:
    """
    Compute graph clusters.
    
    Args:
        graph: igraph Graph object
        mode: Clustering mode ('clusters' or 'age_group')
    
    Returns:
        List of clusters (each cluster is a list of node IDs)
    """
    if mode == 'clusters':
        return graph.clusters()
    elif mode == 'age_group':
        # TODO: Implement age-group based clustering
        logger.warning("Age group clustering not yet implemented, using default clusters")
        return graph.clusters()
    else:
        raise ValueError(f"Unknown clustering mode: {mode}")


def export_graph_to_json(
    graph: Graph,
    output_path: str,
    cluster_mode: str = 'clusters',
    layout_iterations: int = 80
) -> bool:
    """
    Export igraph to Sigma.js JSON format with PageRank calculations.
    
    Args:
        graph: igraph Graph object
        output_path: Path to output JSON file
        cluster_mode: Clustering mode for node coloring
        layout_iterations: Number of iterations for Fruchterman-Reingold layout
    
    Returns:
        True if export successful, False otherwise
    """
    try:
        # Compute layout
        logger.info("Computing graph layout...")
        layout = graph.layout_fruchterman_reingold(niter=layout_iterations)
        
        # Compute clusters and colors
        clusters = compute_clusters(graph, cluster_mode)
        colors = generate_cluster_colors(len(clusters))
        logger.info(f"Found {len(clusters)} clusters")
        
        # Compute PageRank
        logger.info("Computing PageRank...")
        pagerank_values = graph.pagerank(weights=graph.es['weight'])
        
        # Build JSON structure
        graph_json = {'nodes': [], 'edges': []}
        
        # Export nodes
        for vertex, position, pr_value in zip(graph.vs, layout, pagerank_values):
            node = {
                'id': vertex.index,
                'label': vertex['name'],
                'full_name': vertex['full_name'],
                'x': position[0],
                'y': position[1],
                'age_group': vertex['age_group'],
                'onset_date': vertex['onset_date'].strftime('%d/%m/%Y'),
                'announce_date': vertex['announce_date'].strftime('%d/%m/%Y'),
                'pagerank': pr_value,
                'size': 700 * pr_value,  # Scale for visualization
                '_color': colors[find_node_cluster(clusters, vertex.index)]
            }
            graph_json['nodes'].append(node)
        
        # Export edges
        for edge in graph.es:
            edge_data = {
                'id': edge.index,
                'source': edge.source,
                'target': edge.target,
                'weight': edge['weight'],
                'type': edge['r_type'],
                'size': 20 * edge['weight'],  # Scale for visualization
                '_color': '#34c0eb'
            }
            graph_json['edges'].append(edge_data)
        
        # Write to file
        with open(output_path, 'w', encoding='utf8') as f:
            json.dump(graph_json, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully exported graph to {output_path}")
        logger.info(f"Exported {len(graph_json['nodes'])} nodes and {len(graph_json['edges'])} edges")
        return True
        
    except Exception as e:
        logger.error(f"Failed to export graph: {e}")
        return False


def compute_influence_metrics(graph: Graph) -> Dict[str, List[float]]:
    """
    Compute various influence metrics for the epidemic network.
    
    Args:
        graph: igraph Graph object
    
    Returns:
        Dictionary of metric names to values
    """
    metrics = {}
    
    # PageRank (primary influence measure)
    metrics['pagerank'] = graph.pagerank(weights=graph.es['weight'])
    
    # Degree centrality
    metrics['degree'] = graph.degree()
    
    # Betweenness centrality
    metrics['betweenness'] = graph.betweenness(weights=graph.es['weight'])
    
    # Closeness centrality
    metrics['closeness'] = graph.closeness(weights=graph.es['weight'])
    
    logger.info("Computed influence metrics for all nodes")
    return metrics


def process_epidemic_graph(
    csv_filepath: str,
    output_json_path: str,
    use_neo4j: bool = False,
    neo4j_uri: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> Dict[str, Any]:
    """
    Main function to process epidemic graph and export visualization data.
    
    Args:
        csv_filepath: Path to relationship CSV file
        output_json_path: Path to output JSON file
        use_neo4j: Whether to use Neo4j or load directly from CSV
        neo4j_uri: Neo4j database URI (if use_neo4j=True)
        username: Database username (if use_neo4j=True)
        password: Database password (if use_neo4j=True)
    
    Returns:
        Dictionary with processing results and metrics
    """
    # Build igraph
    if use_neo4j and neo4j_uri:
        with EpidemicGraphCalculator(neo4j_uri, username, password) as calculator:
            graph = create_igraph_from_neo4j(calculator)
    else:
        logger.info("Using CSV-based graph construction (Neo4j not required)")
        graph = create_igraph_from_csv(csv_filepath)
    
    # Compute influence metrics
    metrics = compute_influence_metrics(graph)
    
    # Export to JSON
    success = export_graph_to_json(graph, output_json_path)
    
    return {
        'success': success,
        'num_nodes': len(graph.vs),
        'num_edges': len(graph.es),
        'num_clusters': len(graph.clusters()),
        'avg_pagerank': sum(metrics['pagerank']) / len(metrics['pagerank']),
        'max_pagerank': max(metrics['pagerank']),
        'output_file': output_json_path
    }


if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Get configuration
    csv_filepath = os.getenv('OUTPUT_RELATION_FILE', 'server/data/relation_new.csv')
    output_json = 'visualization/data.json'
    
    # Try Neo4j first, fallback to CSV if connection fails
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', '123')
    
    try:
        # Test Neo4j connection
        driver = GraphDatabase.driver(neo4j_uri, auth=(username, password))
        driver.verify_connectivity()
        driver.close()
        use_neo4j = True
        logger.info("Neo4j connection successful, using Neo4j mode")
    except Exception as e:
        logger.warning(f"Neo4j not available ({e}), using CSV mode")
        use_neo4j = False
    
    # Process graph
    results = process_epidemic_graph(
        csv_filepath=csv_filepath,
        output_json_path=output_json,
        use_neo4j=use_neo4j,
        neo4j_uri=neo4j_uri if use_neo4j else None,
        username=username if use_neo4j else None,
        password=password if use_neo4j else None
    )
    
    print("\n=== Epidemic Graph Processing Results ===")
    print(f"Success: {results['success']}")
    print(f"Nodes: {results['num_nodes']}")
    print(f"Edges: {results['num_edges']}")
    print(f"Clusters: {results['num_clusters']}")
    print(f"Average PageRank: {results['avg_pagerank']:.6f}")
    print(f"Max PageRank: {results['max_pagerank']:.6f}")
    print(f"Output: {results['output_file']}")
