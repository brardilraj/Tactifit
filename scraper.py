import sys
import json
import time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from bs4 import BeautifulSoup
from utils import (
    clean_player_name,
    create_output_dir,
    normalize_position
)
import csv
import random

class FBrefSeleniumScraper:
    def __init__(self, headless=True):
        self.base_url = "https://fbref.com"
        self.season = "2024-2025"
        
        # Load metrics configuration
        with open('metrics.json', 'r') as f:
            self.metrics_config = json.load(f)
        
        # Setup Chrome options
        chrome_options = Options()
        if headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Initialize driver
        print("Initializing Chrome browser...")
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print("✓ Browser initialized successfully\n")
        except Exception as e:
            print(f"Error initializing Chrome: {e}")
            print("\nPlease install ChromeDriver:")
            print("1. pip install selenium webdriver-manager")
            print("2. Or download from: https://chromedriver.chromium.org/")
            raise
    
    def close(self):
        """Close the browser"""
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("\n✓ Browser closed")
    
    def load_page(self, url, max_retries=3):
        """Load a page with retry logic"""
        for attempt in range(max_retries):
            try:
                print(f"  Loading page... (attempt {attempt + 1}/{max_retries})")
                self.driver.get(url)
                
                # Wait for page to load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                
                # Additional wait for dynamic content
                time.sleep(random.uniform(2, 4))
                
                # Check if we got blocked
                page_source = self.driver.page_source.lower()
                if 'access denied' in page_source or 'forbidden' in page_source:
                    raise Exception("Access denied by website")
                
                return True
                
            except TimeoutException:
                print(f"  Timeout loading page (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(3, 6))
                    continue
                else:
                    return False
            except Exception as e:
                print(f"  Error: {e}")
                if attempt < max_retries - 1:
                    time.sleep(random.uniform(3, 6))
                    continue
                else:
                    return False
        
        return False
    
    def get_player_info(self, soup):
        """Extract player information and club from the page"""
        try:
            # Get player name
            name_elem = soup.find('h1')
            player_name = name_elem.text.strip() if name_elem else "Unknown"
            
            # Get current club
            club = "Unknown"
            meta_div = soup.find('div', {'id': 'meta'})
            if meta_div:
                club_link = meta_div.find('a', href=lambda x: x and '/squads/' in x)
                if club_link:
                    club = club_link.text.strip()
            
            return player_name, club
            
        except Exception as e:
            print(f"  Error extracting player info: {e}")
            return "Unknown", "Unknown"
    
    def scrape_player_stats(self, player_url, position, save_html=False):
        """Scrape player statistics for the 2024/25 season"""
        print(f"  Scraping stats for position: {position}")
        
        try:
            # Load the page
            if not self.load_page(player_url):
                print("  Failed to load page")
                return None
            
            # Get page source and parse with BeautifulSoup
            page_source = self.driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            
            # Save HTML for debugging if requested
            if save_html:
                player_name_raw = player_url.split('/')[-1]
                debug_dir = Path('debug_html')
                debug_dir.mkdir(exist_ok=True)
                debug_file = debug_dir / f"{player_name_raw}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(page_source)
                print(f"  Saved HTML to: {debug_file}")
            
            # Get player info
            player_name, club = self.get_player_info(soup)
            print(f"  Player: {player_name} | Club: {club}")
            
            # Get metrics for the position
            metrics = self.metrics_config.get(position, [])
            if not metrics:
                print(f"  No metrics found for position: {position}")
                return None
            
            # Find all stat tables on the page
            stats_tables = soup.find_all('table', {'class': 'stats_table'})
            print(f"  Found {len(stats_tables)} stat tables")
            
            # Create a dictionary to store all stats
            all_stats = {}
            
            # Parse each table
            for idx, table in enumerate(stats_tables):
                table_id = table.get('id', f'table_{idx}')
                
                # Look for 2024-2025 season row
                rows = table.find_all('tr')
                for row in rows:
                    # Try multiple ways to find the season
                    season_cell = row.find('th', {'data-stat': 'season'})
                    
                    # Check if this row contains 2024-2025 data
                    is_current_season = False
                    if season_cell:
                        season_text = season_cell.text.strip()
                        if '2024-2025' in season_text or '2024-25' in season_text:
                            is_current_season = True
                    
                    # Also check for "Premier League" or current season in other cells
                    if not is_current_season:
                        comp_cell = row.find('td', {'data-stat': 'comp_level'})
                        if comp_cell:
                            # This might be a league-specific table
                            all_cells_text = ' '.join([cell.text for cell in row.find_all(['th', 'td'])])
                            if '2024-2025' in all_cells_text or '2024-25' in all_cells_text:
                                is_current_season = True
                    
                    if is_current_season:
                        # Extract all stats from this row
                        cells = row.find_all(['th', 'td'])
                        for cell in cells:
                            stat_name = cell.get('data-stat', '')
                            stat_value = cell.text.strip()
                            if stat_name and stat_value and stat_name != 'season':
                                # Don't overwrite if we already have a value
                                if stat_name not in all_stats or all_stats[stat_name] == '':
                                    all_stats[stat_name] = stat_value
            
            print(f"  Extracted {len(all_stats)} stats from 2024-2025 season")
            
            # Debug: Print some of the stats found
            if len(all_stats) > 0:
                print(f"  Sample stats found: {list(all_stats.keys())[:10]}")
            else:
                print("  WARNING: No stats found! Checking for alternative data sources...")
                
                # Try to find stats in any format
                all_tables = soup.find_all('table')
                print(f"  Total tables on page: {len(all_tables)}")
                
                # Look for any rows with stat data
                for table in all_tables[:5]:  # Check first 5 tables
                    rows = table.find_all('tr')
                    for row in rows[:3]:  # Check first 3 rows of each table
                        cells = row.find_all(['th', 'td'])
                        sample_stats = []
                        for cell in cells[:5]:
                            stat_name = cell.get('data-stat', '')
                            if stat_name:
                                sample_stats.append(stat_name)
                        if sample_stats:
                            print(f"    Sample data-stat attributes: {sample_stats}")
            
            # Match metrics to scraped stats
            results = []
            for metric in metrics:
                value = self.find_metric_value(metric, all_stats)
                results.append({
                    'Player Name': player_name,
                    'Club': club,
                    'Position': position,
                    'Metric': metric,
                    'Value': value
                })
            
            return results
            
        except Exception as e:
            print(f"  Error scraping player stats: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def find_metric_value(self, metric, stats_dict):
        """Find the value for a metric in the stats dictionary"""
        # Create mapping of metric names to FBref stat names
        metric_mapping = {
            'NPG': 'goals_pens',
            'NPXG': 'xg_non_penalty',
            'Assists': 'assists',
            'Goals': 'goals',
            'XG': 'xg',
            'XA': 'xg_assist',
            'Progressive passes': 'progressive_passes',
            'Progressive carries': 'progressive_carries',
            'Progressive Passes': 'progressive_passes',
            'Progressive Carries': 'progressive_carries',
            'Passes completed': 'passes_completed',
            'Passes attempted': 'passes',
            'Pass Completion': 'passes_pct',
            'Key passes': 'assisted_shots',
            'Through balls': 'through_balls',
            'Through Balls': 'through_balls',
            'Switches': 'switches',
            'Crosses': 'crosses',
            'Corners': 'corner_kicks',
            'Shot creating Actions': 'sca',
            'Shot Creating Actions': 'sca',
            'Shot creating actions': 'sca',
            'SCA Take Ons': 'sca_dribbles',
            'Goal Creating Actions': 'gca',
            'GCA Shots': 'gca_shots',
            'Tackles': 'tackles',
            'Tackles won': 'tackles_won',
            'Dribblers tackles': 'tackles_vs_dribbles_won',
            'Challenges won': 'challenges_won',
            'Challenges Lost': 'challenges_lost',
            'Shots blocked': 'blocked_shots',
            'Blocks': 'blocks',
            'Interceptions': 'interceptions',
            'Passes Recieved': 'passes_received',
            'Offsides': 'offsides',
            'Ball recoveries': 'ball_recoveries',
            'Errors': 'errors',
            'Touches': 'touches',
            'Miscontrols': 'miscontrols',
            'Dispossessed': 'dispossessed',
            'Yellow Cards': 'cards_yellow',
            'Red Cards': 'cards_red',
            'Fouls committed': 'fouls',
            'Fouls Committed': 'fouls',
            'Aerials Won': 'aerials_won',
            'Aerials won': 'aerials_won',
            'Aerial Duel win percentage': 'aerials_won_pct',
            'Save Percentage': 'save_pct',
            'Saves': 'saves',
            'Goals Against': 'goals_against_gk',
            'Clean Sheet Percentage': 'clean_sheets_pct',
            'Pass Completion percentage': 'passes_pct',
            'Pass Completion - Short': 'passes_pct_short',
            'Pass Completion - Medium': 'passes_pct_medium',
            'Pass Completion - Long': 'passes_pct_long',
            'Penalty kicks conceded': 'pens_conceded',
            'Passes into final third': 'passes_into_final_third',
            'Crosses Stopped': 'crosses_stopped_gk',
            'Post Shot Xg + goals Allowed (PSxG-GA)': 'psxg_net_gk',
            'Def Actions outside Pen area': 'def_actions_outside_pen_gk',
            'Avg distance of defensive actions': 'def_actions_distance_gk',
            'Avg Length Of goalkicks': 'goal_kicks_length_avg'
        }
        
        # Try to find the metric in the stats dictionary
        mapped_name = metric_mapping.get(metric)
        if mapped_name and mapped_name in stats_dict:
            return stats_dict[mapped_name]
        
        # Try alternative matches
        metric_lower = metric.lower().replace(' ', '_')
        for key, value in stats_dict.items():
            if metric_lower in key.lower():
                return value
        
        return "NA"

def save_player_csv(player_data, player_name):
    """Save individual player statistics to a separate CSV file"""
    if not player_data:
        raise ValueError("No data to save")
    
    output_dir = create_output_dir()
    
    # Clean player name for filename
    from utils import clean_player_name
    clean_name = clean_player_name(player_name)
    output_path = output_dir / f"{clean_name}.csv"
    
    # Define CSV headers
    headers = ['Player Name', 'Club', 'Position', 'Metric', 'Value']
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(player_data)
    
    return output_path

def save_combined_csv(all_data, output_filename='combined_players_stats.csv'):
    """Save all player statistics to a single combined CSV file"""
    if not all_data:
        raise ValueError("No data to save")
    
    output_dir = create_output_dir()
    output_path = output_dir / output_filename
    
    # Define CSV headers
    headers = ['Player Name', 'Club', 'Position', 'Metric', 'Value']
    
    # Write to CSV
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(all_data)
    
    return output_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python scraper.py '<player_url1>:<position1>' '<player_url2>:<position2>' ...")
        print("Example: python scraper.py 'https://fbref.com/en/players/.../Erling-Haaland:ST' 'https://fbref.com/en/players/.../Kevin-De-Bruyne:CAM_Winger'")
        print("\nPositions: GK, Fullback, CB, Midfielder, CAM_Winger, ST")
        print("\nYou can also use shortcuts like: GK, FB, CB, MF, CAM, ST, LW, RW, etc.")
        print("\nNote: This script uses Selenium and requires ChromeDriver to be installed.")
        sys.exit(1)
    
    # Create output directory
    create_output_dir()
    
    # Initialize scraper
    scraper = None
    try:
        scraper = FBrefSeleniumScraper(headless=True)
        
        # Store all player data
        all_player_data = []
        player_count = 0
        failed_players = []
        individual_files = []
        
        # Process each player
        for i, arg in enumerate(sys.argv[1:], 1):
            try:
                # Split by colon to get URL and position
                if ':' not in arg:
                    print(f"Error: Invalid format for '{arg}'. Use 'URL:POSITION'")
                    failed_players.append(arg)
                    continue
                
                player_url, position = arg.rsplit(':', 1)
                
                # Normalize position
                position = normalize_position(position)
                
                print(f"\n{'='*60}")
                print(f"Processing player {i}/{len(sys.argv)-1}")
                print(f"URL: {player_url}")
                print(f"Position: {position}")
                print(f"{'='*60}")
                
                # Scrape player stats (enable HTML saving for debugging)
                results = scraper.scrape_player_stats(player_url, position, save_html=True)
                
                if results:
                    # Save individual player CSV
                    player_name = results[0]['Player Name']
                    individual_file = save_player_csv(results, player_name)
                    individual_files.append(individual_file)
                    print(f"✓ Saved individual file: {individual_file}")
                    
                    # Add to combined data
                    all_player_data.extend(results)
                    player_count += 1
                    print(f"✓ Successfully scraped {len(results)} metrics")
                else:
                    print(f"✗ Failed to scrape stats for this player")
                    failed_players.append(player_url)
                
                # Add delay between requests
                if i < len(sys.argv) - 1:
                    wait_time = random.uniform(3, 6)
                    print(f"Waiting {wait_time:.1f} seconds before next request...")
                    time.sleep(wait_time)
                
            except Exception as e:
                print(f"Error processing player: {e}")
                failed_players.append(arg)
                continue
        
        if not all_player_data:
            print("\n✗ No data was scraped. Exiting.")
            sys.exit(1)
        
        # Save combined CSV
        output_file = save_combined_csv(all_player_data)
        
        print(f"\n{'='*60}")
        print("SCRAPING COMPLETE")
        print(f"{'='*60}")
        print(f"✓ Total players processed: {player_count}")
        print(f"✓ Total metrics scraped: {len(all_player_data)}")
        print(f"\n✓ Individual player files saved:")
        for file in individual_files:
            print(f"  - {file}")
        print(f"\n✓ Combined output file: {output_file}")
        if failed_players:
            print(f"\n⚠ Failed players ({len(failed_players)}):")
            for fp in failed_players:
                print(f"  - {fp}")
        print(f"{'='*60}\n")
        
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()