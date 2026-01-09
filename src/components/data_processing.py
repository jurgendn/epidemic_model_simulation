import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import os
from dotenv import load_dotenv


def load_epidemic_data(filepath: str) -> pd.DataFrame:
    """Load epidemic data from CSV file with specified columns."""
    columns = ['MCB', 'Ngày công bố', 'Nhóm tuổi', 'G-Related-Cases', 'Ngày khởi phát', 'Họ và tên']
    return pd.read_csv(filepath, usecols=columns)


def parse_date(date_str: str) -> datetime:
    """Parse date string in DD/MM/YYYY format."""
    return datetime.strptime(date_str, '%d/%m/%Y')


def fill_missing_onset_dates(announce_date: str, onset_date: str, default_days: int = 5) -> datetime:
    """
    Fill missing onset dates by subtracting default_days from announcement date.
    
    Args:
        announce_date: Announcement date string
        onset_date: Onset date string (may be NaN)
        default_days: Days to subtract from announcement date if onset is missing
    
    Returns:
        Onset date as datetime object
    """
    if pd.isna(onset_date):
        return parse_date(announce_date) - timedelta(days=default_days)
    return parse_date(onset_date)


def process_dates(df: pd.DataFrame) -> Tuple[List[datetime], List[datetime]]:
    """Process and normalize onset and announcement dates."""
    onset_dates = []
    announce_dates = []
    
    for _, row in df.iterrows():
        onset = fill_missing_onset_dates(row['Ngày công bố'], row['Ngày khởi phát'])
        announce = parse_date(row['Ngày công bố'])
        
        onset_dates.append(onset)
        announce_dates.append(announce)
    
    return onset_dates, announce_dates


def extract_age_group(age_range: str) -> str:
    """Extract age group from range string (e.g., '20-30' -> '20')."""
    return age_range.split('.')[0]


def build_graph(df: pd.DataFrame, onset_dates: List[datetime], announce_dates: List[datetime]) -> Dict:
    """
    Build graph structure from epidemic data.
    
    Returns:
        Dictionary mapping case IDs to [related_cases, age_group, onset_date, announce_date, name]
    """
    graph = {}
    
    for idx, row in df.iterrows():
        case_id = row['MCB']
        related_cases = row['G-Related-Cases'].replace(" ", "").split(',')
        age_group = extract_age_group(row['Nhóm tuổi'])
        
        graph[case_id] = [
            related_cases,
            age_group,
            onset_dates[idx],
            announce_dates[idx],
            row['Họ và tên']
        ]
    
    return graph


def create_relationships(graph: Dict) -> pd.DataFrame:
    """
    Create relationships dataframe from graph structure.
    
    Each relationship represents a connection from source case to target case.
    """
    import random
    relationships = []
    
    for target_case, data in graph.items():
        source_cases, age_group, onset_date, announce_date, name = data
        
        for source_case in source_cases:
            relationships.append({
                'source': source_case,
                'target': target_case,
                'age_group': age_group,
                'onset_date': onset_date,
                'announce_date': announce_date,
                'name': name,
                'relationship': random.choice(['0', '1', '2', '3', '4'])  # Random relationship type
            })
    
    return pd.DataFrame(relationships)


def process_epidemic_data(input_file: str, output_file: str) -> pd.DataFrame:
    """
    Main function to process epidemic data and generate relationships.
    
    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file for relationships
    
    Returns:
        DataFrame containing relationships between cases
    """
    # Load data
    df = load_epidemic_data(input_file)
    
    # Process dates
    onset_dates, announce_dates = process_dates(df)
    
    # Build graph structure
    graph = build_graph(df, onset_dates, announce_dates)
    
    # Create relationships
    relationships_df = create_relationships(graph)
    
    # Save to CSV
    relationships_df.to_csv(output_file, index=False)
    
    return relationships_df


if __name__ == '__main__':
    # Load environment variables
    load_dotenv()
    
    # Get file paths from environment or use defaults
    input_file = os.getenv('INPUT_DATA_FILE', 'server/data/data.csv')
    output_file = os.getenv('OUTPUT_RELATION_FILE', 'server/data/relation_new.csv')
    
    # Process data
    relationships = process_epidemic_data(input_file, output_file)
    print(f"Generated {len(relationships)} relationships")
    print(f"Output saved to: {output_file}")
