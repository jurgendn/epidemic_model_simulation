"""
Epidemic Model Simulation - End-to-End Pipeline

This module orchestrates the complete workflow:
1. Process raw epidemic data
2. Migrate to Neo4j graph database
3. Calculate PageRank metrics and export visualization
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from components.data_processing import process_epidemic_data
from components.migrate_graph_db import migrate_to_neo4j
from models.calculator import process_epidemic_graph

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_environment():
    """Validate that all required environment variables are set."""
    load_dotenv()
    
    required_vars = [
        'NEO4J_URI',
        'NEO4J_USERNAME',
        'NEO4J_PASSWORD',
        'INPUT_DATA_FILE',
        'OUTPUT_RELATION_FILE'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please configure .env file with all required variables")
        return False
    
    return True


def check_neo4j_connection(uri: str, username: str, password: str) -> bool:
    """Check if Neo4j is accessible."""
    try:
        from neo4j import GraphDatabase
        driver = GraphDatabase.driver(uri, auth=(username, password))
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        logger.info("✓ Neo4j connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Neo4j connection failed: {e}")
        logger.error("Please ensure Neo4j is running (try: docker-compose up -d)")
        return False


def run_data_processing(input_file: str, output_file: str, skip_existing: bool = False) -> bool:
    """
    Run data processing step.
    
    Args:
        input_file: Path to raw data CSV
        output_file: Path to output relationship CSV
        skip_existing: Skip if output already exists
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("STEP 1: DATA PROCESSING")
    logger.info("=" * 60)
    
    if skip_existing and os.path.exists(output_file):
        logger.info(f"Skipping - output file already exists: {output_file}")
        return True
    
    if not os.path.exists(input_file):
        logger.error(f"Input file not found: {input_file}")
        return False
    
    try:
        logger.info(f"Processing: {input_file}")
        df = process_epidemic_data(input_file, output_file)
        logger.info(f"✓ Generated {len(df)} relationships → {output_file}")
        return True
    except Exception as e:
        logger.error(f"✗ Data processing failed: {e}")
        return False


def run_migration(csv_file: str, uri: str, username: str, password: str, force: bool = False) -> bool:
    """
    Run Neo4j migration step.
    
    Args:
        csv_file: Path to relationship CSV
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        force: Force re-import even if data exists
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("STEP 2: NEO4J MIGRATION")
    logger.info("=" * 60)
    
    if not os.path.exists(csv_file):
        logger.error(f"Relationship file not found: {csv_file}")
        return False
    
    # Check if data already exists
    if not force:
        try:
            from neo4j import GraphDatabase
            driver = GraphDatabase.driver(uri, auth=(username, password))
            with driver.session() as session:
                result = session.run("MATCH (n) RETURN count(n) as count")
                count = result.single()['count']
                if count > 0:
                    logger.info(f"Neo4j already contains {count} nodes")
                    response = input("Clear existing data and re-import? (y/N): ")
                    if response.lower() != 'y':
                        logger.info("Skipping migration - using existing data")
                        driver.close()
                        return True
                    else:
                        logger.info("Clearing existing data...")
                        session.run("MATCH (n) DETACH DELETE n")
            driver.close()
        except Exception as e:
            logger.warning(f"Could not check existing data: {e}")
    
    try:
        logger.info(f"Migrating: {csv_file} → Neo4j")
        results = migrate_to_neo4j(csv_file, uri, username, password)
        logger.info(f"✓ Imported {results['nodes_imported']} nodes")
        logger.info(f"✓ Imported {results['relationships_imported']} relationships")
        return True
    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        return False


def run_analysis(uri: str, username: str, password: str, output_json: str) -> bool:
    """
    Run graph analysis and export visualization.
    
    Args:
        uri: Neo4j URI
        username: Neo4j username
        password: Neo4j password
        output_json: Path to output JSON file
    
    Returns:
        True if successful, False otherwise
    """
    logger.info("=" * 60)
    logger.info("STEP 3: GRAPH ANALYSIS & VISUALIZATION")
    logger.info("=" * 60)
    
    try:
        logger.info("Computing PageRank and metrics...")
        results = process_epidemic_graph(uri, username, password, output_json)
        
        if results['success']:
            logger.info(f"✓ Exported visualization → {output_json}")
            logger.info(f"  Nodes: {results['num_nodes']}")
            logger.info(f"  Edges: {results['num_edges']}")
            logger.info(f"  Clusters: {results['num_clusters']}")
            logger.info(f"  Avg PageRank: {results['avg_pagerank']:.6f}")
            logger.info(f"  Max PageRank: {results['max_pagerank']:.6f}")
            return True
        else:
            logger.error("✗ Analysis failed")
            return False
    except Exception as e:
        logger.error(f"✗ Analysis failed: {e}")
        return False


def main():
    """Main entry point for the epidemic model simulation pipeline."""
    parser = argparse.ArgumentParser(
        description='Epidemic Model Simulation - End-to-End Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full pipeline
  python src/main.py
  
  # Run specific steps
  python src/main.py --step process
  python src/main.py --step migrate
  python src/main.py --step analyze
  
  # Force re-import
  python src/main.py --force
  
  # Skip confirmation prompts
  python src/main.py --yes
        """
    )
    
    parser.add_argument(
        '--step',
        choices=['process', 'migrate', 'analyze', 'all'],
        default='all',
        help='Pipeline step to run (default: all)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force re-import even if data exists'
    )
    
    parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompts'
    )
    
    parser.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip processing if output files already exist'
    )
    
    parser.add_argument(
        '--output-json',
        default='visualization/data.json',
        help='Output path for visualization JSON (default: visualization/data.json)'
    )
    
    args = parser.parse_args()
    
    # Validate environment
    if not validate_environment():
        sys.exit(1)
    
    # Load configuration
    load_dotenv()
    neo4j_uri = os.getenv('NEO4J_URI')
    neo4j_username = os.getenv('NEO4J_USERNAME')
    neo4j_password = os.getenv('NEO4J_PASSWORD')
    input_file = os.getenv('INPUT_DATA_FILE')
    output_file = os.getenv('OUTPUT_RELATION_FILE')
    
    logger.info("")
    logger.info("╔═══════════════════════════════════════════════════════════╗")
    logger.info("║     EPIDEMIC MODEL SIMULATION - PIPELINE EXECUTION        ║")
    logger.info("╚═══════════════════════════════════════════════════════════╝")
    logger.info("")
    logger.info("Configuration:")
    logger.info(f"  Neo4j URI: {neo4j_uri}")
    logger.info(f"  Input File: {input_file}")
    logger.info(f"  Output File: {output_file}")
    logger.info(f"  Visualization: {args.output_json}")
    logger.info("")
    
    # Check Neo4j connection if needed
    if args.step in ['migrate', 'analyze', 'all']:
        if not check_neo4j_connection(neo4j_uri, neo4j_username, neo4j_password):
            sys.exit(1)
    
    # Execute pipeline steps
    success = True
    
    if args.step in ['process', 'all']:
        success = run_data_processing(input_file, output_file, args.skip_existing)
        if not success:
            sys.exit(1)
        logger.info("")

    if args.step in ["migrate", "all"]:
        success = run_migration(output_file, neo4j_uri, neo4j_username, neo4j_password, args.force)
        if not success:
            sys.exit(1)
        logger.info("")
    
    if args.step in ['analyze', 'all']:
        success = run_analysis(neo4j_uri, neo4j_username, neo4j_password, args.output_json)
        if not success:
            sys.exit(1)
        logger.info("")
    
    # Final summary
    logger.info("=" * 60)
    logger.info("✓ PIPELINE COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next steps:")
    logger.info(f"  1. Open {args.output_json} to view the graph data")
    logger.info(f"  2. Open visualization/index.html in a browser")
    logger.info(f"  3. Explore the epidemic network visualization")
    logger.info("")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
