import pandas as pd
import os
import sys

def build_team_dna_database():
    """
    Main function to build the master team database.
    It loads all individual player archetype results, aggregates them by team,
    loads the main team-level stat file, preprocesses it, and merges
    everything into a single 'team_dna_database.csv'.
    """
    
    # --- Define all file paths ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 1. Player archetype result files (from our previous scripts)
    player_files = [
        'gk_clusters_results.csv',
        'cb_clusters_results.csv',
        'fb_clusters_results.csv',
        'midfielder_clusters_results.csv',
        'winger_clusters_results.csv',
        'striker_clusters_results.csv'
    ]
    player_paths = [os.path.join(script_dir, f) for f in player_files]
    
    # 2. Main team stat file (the one you just uploaded)
    team_stat_file = 'ScoutIQ Data - Teams And Stats.csv'
    team_stat_path = os.path.join(script_dir, team_stat_file)

    print("--- Phase 1: Building Team DNA Database ---")

    # --- Load and consolidate all player archetype results ---
    print("Loading all player archetype results...")
    all_player_dfs = []
    found_files_count = 0
    for path in player_paths:
        try:
            df = pd.read_csv(path)
            # Ensure 'Club' and 'Archetype' columns exist
            if 'Club' in df.columns and 'Archetype' in df.columns:
                all_player_dfs.append(df[['Club', 'Archetype']])
                print(f"  ✓ Loaded {os.path.basename(path)}")
                found_files_count += 1
            else:
                print(f"  Warning: Skipping '{os.path.basename(path)}' (missing 'Club' or 'Archetype' column).")
        except FileNotFoundError:
            print(f"  Warning: Could not find '{os.path.basename(path)}'. Skipping this file.")
            
    if not all_player_dfs:
        print("\nCRITICAL ERROR: No player archetype files found. Aborting.")
        print("Please make sure your `_results.csv` files are in the same folder.")
        sys.exit()

    master_player_df = pd.concat(all_player_dfs, ignore_index=True)
    print(f"\n✓ Consolidated {len(master_player_df)} players from {found_files_count} files.")

    # --- Aggregate player archetypes by team ---
    print("Aggregating player archetypes by team...")
    # Use crosstab to count archetypes for each club
    # This creates a DataFrame where index=Club, columns=Archetypes, values=Count
    df_archetype_counts = pd.crosstab(master_player_df['Club'], master_player_df['Archetype'])
    
    # Reset index to make 'Club' a column for merging
    df_archetype_counts = df_archetype_counts.reset_index()
    print(f"✓ Team archetype counts calculated for {len(df_archetype_counts)} teams.")

    # --- Load and preprocess the main team stat file ---
    print(f"\nLoading main team stat file: '{team_stat_file}'...")
    try:
        df_team_stats = pd.read_csv(team_stat_path)
    except FileNotFoundError:
        print(f"\nCRITICAL ERROR: Team stat file '{team_stat_file}' not found. Aborting.")
        sys.exit()

    # --- PREPROCESSING STEP: Convert text columns to numbers ---
    height_col = 'Defensive Line Height (High / Medium / Low)'
    if height_col in df_team_stats.columns:
        print(f"Converting '{height_col}' to numeric (3=High, 2=Medium, 1=Low)...")
        # Define the mapping
        height_map = {'High': 3, 'Medium': 2, 'Low': 1}
        
        # Create the new numeric column
        df_team_stats['Defensive Line Height'] = df_team_stats[height_col].map(height_map)
        
        # Fill any missing values with the neutral 'Medium' (2)
        df_team_stats['Defensive Line Height'] = df_team_stats['Defensive Line Height'].fillna(2).astype(int)
        print("✓ Conversion complete.")
    else:
        print(f"  Warning: Could not find column '{height_col}' for conversion.")
        
    print(f"✓ Loaded {len(df_team_stats)} teams from the stat file.")

    # --- Merge the two dataframes ---
    print("\nMerging team stats with archetype counts...")
    df_team_dna = pd.merge(
        df_team_stats,
        df_archetype_counts,
        left_on='Team Name', # Key from 'ScoutIQ Data - Teams And Stats.csv'
        right_on='Club',     # Key from our '_results.csv' files
        how='left'           # Keep all teams from the main stat file
    )
    
    # --- Clean up the merged dataframe ---
    # Drop the redundant 'Club' column
    if 'Club' in df_team_dna.columns:
        df_team_dna = df_team_dna.drop(columns='Club')
        
    # Fill any NaNs in archetype counts with 0 
    # (for teams in your stat file that had no players in our DB)
    archetype_cols = df_archetype_counts.columns.drop('Club')
    df_team_dna[archetype_cols] = df_team_dna[archetype_cols].fillna(0).astype(int)
    
    print("✓ Merge complete. Team DNA database is built.")

    # --- Save the final database ---
    output_path = os.path.join(script_dir, 'team_dna_database.csv')
    df_team_dna.to_csv(output_path, index=False)
    
    print("\n" + "="*60)
    print("✓✓✓ PHASE 1 COMPLETE! ✓✓✓")
    print(f"Master database saved to: {output_path}")
    print(f"This file now contains all team stats + counts for all player archetypes.")
    print("="*60)

if __name__ == "__main__":
    build_team_dna_database()