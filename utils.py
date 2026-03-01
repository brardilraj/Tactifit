import csv
import re
from pathlib import Path

def clean_player_name(name):
    """Clean player name for file naming"""
    # Remove special characters and replace spaces with underscores
    cleaned = re.sub(r'[^\w\s-]', '', name)
    cleaned = cleaned.strip().replace(' ', '_')
    return cleaned

def clean_metric_name(metric):
    """Clean metric name for consistency"""
    return metric.strip()

def normalize_position(position):
    """Normalize position input to match metrics.json keys"""
    position_mapping = {
        'GK': 'GK',
        'GOALKEEPER': 'GK',
        'FB': 'Fullback',
        'FULLBACK': 'Fullback',
        'LB': 'Fullback',
        'RB': 'Fullback',
        'CB': 'CB',
        'CENTERBACK': 'CB',
        'MF': 'Midfielder',
        'MIDFIELDER': 'Midfielder',
        'CM': 'Midfielder',
        'CDM': 'Midfielder',
        'DM': 'Midfielder',
        'CAM': 'CAM_Winger',
        'WINGER': 'CAM_Winger',
        'CAM_WINGER': 'CAM_Winger',
        'LW': 'CAM_Winger',
        'RW': 'CAM_Winger',
        'AM': 'CAM_Winger',
        'ST': 'ST',
        'STRIKER': 'ST',
        'CF': 'ST',
        'FW': 'ST',
        'FORWARD': 'ST'
    }
    
    position_upper = position.upper().replace(' ', '_')
    return position_mapping.get(position_upper, position)

def create_output_dir():
    """Create output directory if it doesn't exist"""
    output_dir = Path('data/players')
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir

def format_stat_value(value):
    """Format statistical value for consistency"""
    if value is None or value == '':
        return 'NA'
    
    # Remove any extra whitespace
    value = str(value).strip()
    
    # Handle percentage signs
    if '%' in value:
        return value
    
    # Handle numeric values
    try:
        float_val = float(value)
        return value
    except ValueError:
        return value if value else 'NA'

def validate_metrics(metrics_file='metrics.json'):
    """Validate that metrics.json exists and is properly formatted"""
    import json
    
    try:
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
        
        required_positions = ['GK', 'Fullback', 'CB', 'Midfielder', 'CAM_Winger', 'ST']
        for pos in required_positions:
            if pos not in metrics:
                raise ValueError(f"Missing position in metrics.json: {pos}")
            if not isinstance(metrics[pos], list):
                raise ValueError(f"Metrics for {pos} must be a list")
        
        return True
    except FileNotFoundError:
        raise FileNotFoundError("metrics.json not found. Please ensure it exists in the same directory.")
    except json.JSONDecodeError:
        raise ValueError("metrics.json is not valid JSON")

def print_scraping_summary(data):
    """Print a summary of scraped data"""
    if not data:
        print("No data to summarize")
        return
    
    print("\n" + "="*50)
    print("SCRAPING SUMMARY")
    print("="*50)
    print(f"Player: {data[0]['Player Name']}")
    print(f"Club: {data[0]['Club']}")
    print(f"Position: {data[0]['Position']}")
    print(f"Total metrics: {len(data)}")
    
    # Count how many metrics were found
    found = sum(1 for item in data if item['Value'] != 'NA')
    missing = len(data) - found
    
    print(f"Found: {found}")
    print(f"Missing: {missing}")
    print("="*50 + "\n")