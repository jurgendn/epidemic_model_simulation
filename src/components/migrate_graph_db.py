import pandas as pd
from neo4j import GraphDatabase
from typing import List, Dict, Optional
import logging
import os
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Neo4jGraphMigrator:
    """Handles migration of epidemic data to Neo4j graph database."""
    
    RELATIONSHIP_TYPES = {
        '0': 'Unknown',
        '1': 'Staff_Patience',
        '2': 'Fellow',
        '3': 'Relatives',
        '4': 'Social'
    }
    
    def __init__(self, uri: str, username: str, password: str):
        """
        Initialize Neo4j connection.
        
        Args:
            uri: Neo4j database URI (e.g., 'bolt://localhost:7687')
            username: Database username
            password: Database password
        """
        self.driver = GraphDatabase.driver(uri, auth=(username, password))
        logger.info(f"Connected to Neo4j at {uri}")
    
    def close(self):
        """Close the database connection."""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def load_relationship_data(filepath: str) -> pd.DataFrame:
    """Load relationship data from CSV file."""
    return pd.read_csv(filepath)


def generate_node_properties(
    name: str,
    full_name: str,
    onset_date: str,
    announce_date: str,
    age_group: str
) -> str:
    """
    Generate Cypher properties string for a node.
    
    Args:
        name: Case identifier
        full_name: Full name of the person
        onset_date: Date of symptom onset
        announce_date: Date case was announced
        age_group: Age group category
    
    Returns:
        Formatted properties string for Cypher query
    """
    return (
        f'{{name:"{name}", full_name:"{full_name}", age_group:{age_group}, '
        f'onset_date:date("{onset_date}"), announce_date:date("{announce_date}")}}'
    )


def generate_node_query(
    name: str,
    full_name: str,
    onset_date: str,
    announce_date: str,
    age_group: str
) -> str:
    """
    Generate Cypher query to create a node.
    
    Args:
        name: Case identifier
        full_name: Full name of the person
        onset_date: Date of symptom onset
        announce_date: Date case was announced
        age_group: Age group category
    
    Returns:
        Cypher CREATE query string
    """
    properties = generate_node_properties(name, full_name, onset_date, announce_date, age_group)
    return f"CREATE (n:G{age_group}{properties})"


def generate_relationship_query(
    source: str,
    target: str,
    relationship_id: str,
    relationship_types: Dict[str, str]
) -> str:
    """
    Generate Cypher query to create a relationship between nodes.
    
    Args:
        source: Source case identifier
        target: Target case identifier
        relationship_id: ID representing relationship type
        relationship_types: Dictionary mapping IDs to relationship names
    
    Returns:
        Cypher MATCH-CREATE query string
    """
    rel_type = relationship_types.get(str(relationship_id), 'Unknown')
    
    return f"""
    MATCH (s), (t)
    WHERE s.name = "{source}" AND t.name = "{target}"
    CREATE (s)-[r:{rel_type}]->(t)
    """


def import_nodes(
    migrator: Neo4jGraphMigrator,
    names: List[str],
    full_names: List[str],
    onset_dates: List[str],
    announce_dates: List[str],
    age_groups: List[str]
) -> int:
    """
    Import nodes into Neo4j database.
    
    Args:
        migrator: Neo4jGraphMigrator instance
        names: List of case identifiers
        full_names: List of full names
        onset_dates: List of onset dates
        announce_dates: List of announcement dates
        age_groups: List of age groups
    
    Returns:
        Number of nodes successfully imported
    """
    success_count = 0
    
    with migrator.driver.session() as session:
        for name, full_name, onset_date, announce_date, age_group in zip(
            names, full_names, onset_dates, announce_dates, age_groups
        ):
            try:
                query = generate_node_query(name, full_name, onset_date, announce_date, age_group)
                session.run(query)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to create node {name}: {e}")
    
    logger.info(f"Successfully imported {success_count}/{len(names)} nodes")
    return success_count


def import_relationships(
    migrator: Neo4jGraphMigrator,
    source_nodes: List[str],
    target_nodes: List[str],
    relationship_ids: List[str]
) -> int:
    """
    Import relationships into Neo4j database.
    
    Args:
        migrator: Neo4jGraphMigrator instance
        source_nodes: List of source case identifiers
        target_nodes: List of target case identifiers
        relationship_ids: List of relationship type IDs
    
    Returns:
        Number of relationships successfully imported
    """
    success_count = 0
    
    with migrator.driver.session() as session:
        for source, target, rel_id in zip(source_nodes, target_nodes, relationship_ids):
            # Skip relationships from unknown source '0'
            if source == '0':
                continue
            
            try:
                query = generate_relationship_query(
                    source, target, rel_id, migrator.RELATIONSHIP_TYPES
                )
                session.run(query)
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to create relationship {source}->{target}: {e}")
    
    logger.info(f"Successfully imported {success_count} relationships")
    return success_count


def migrate_to_neo4j(
    csv_filepath: str,
    neo4j_uri: str,
    username: str,
    password: str
) -> Dict[str, int]:
    """
    Main function to migrate epidemic data from CSV to Neo4j.
    
    Args:
        csv_filepath: Path to CSV file containing relationship data
        neo4j_uri: Neo4j database URI
        username: Database username
        password: Database password
    
    Returns:
        Dictionary with counts of imported nodes and relationships
    """
    # Load data
    df = load_relationship_data(csv_filepath)
    logger.info(f"Loaded {len(df)} records from {csv_filepath}")
    
    # Extract data
    source_nodes = df['source'].tolist()
    target_nodes = df['target'].tolist()
    age_groups = df['age_group'].tolist()
    onset_dates = df['onset_date'].tolist()
    announce_dates = df['announce_date'].tolist()
    full_names = df['name'].tolist()
    relationship_ids = df['relationship'].tolist() if 'relationship' in df.columns else ['0'] * len(df)
    
    # Connect to Neo4j and import data
    with Neo4jGraphMigrator(neo4j_uri, username, password) as migrator:
        # Import nodes
        nodes_count = import_nodes(
            migrator,
            target_nodes,
            full_names,
            onset_dates,
            announce_dates,
            age_groups
        )
        
        # Import relationships
        relationships_count = import_relationships(
            migrator,
            source_nodes,
            target_nodes,
            relationship_ids
        )
    
    return {
        'nodes_imported': nodes_count,
        'relationships_imported': relationships_count
    }


if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Get configuration from environment
    csv_filepath = os.getenv('OUTPUT_RELATION_FILE', './relation_new.csv')
    neo4j_uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    username = os.getenv('NEO4J_USERNAME', 'neo4j')
    password = os.getenv('NEO4J_PASSWORD', '123')
    
    # Run migration
    results = migrate_to_neo4j(
        csv_filepath=csv_filepath,
        neo4j_uri=neo4j_uri,
        username=username,
        password=password
    )
    
    print(f"Migration complete: {results}")
