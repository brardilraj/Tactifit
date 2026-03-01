import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from scipy.stats import zscore
import os # Import the os module

# --- Constants for Archetypes and Columns ---
ARCHETYPE_PLAYMAKER = "Playmaking Midfielder"
ARCHETYPE_B2B = "Box-to-Box Midfielder"
ARCHETYPE_DM = "Defensive Midfielder"

COL_MARKET_VALUE = "Market Value (M)" # The name our script will use
COL_MARKET_VALUE_RAW = "Market Value (€M)" # The name from the CSV
COL_PLAYER_NAME = "Name" # The name from the CSV (FIXED from 'Player Name')
COL_PLAYER_SCRIPT = "Player" # The name our script will use internally

METRIC_PROG_PASSES = "Progressive passes"
METRIC_XA = "XA"
METRIC_KEY_PASSES = "Key passes"
METRIC_TACKLES = "Tackles"
METRIC_INTERCEPTIONS = "Interceptions"
METRIC_AERIALS_WON = "Aerials Won"

def create_radar_chart(df_final, radar_metrics, script_dir, radar_path):
    """
    Creates and saves a radar chart comparing the average metrics for each cluster.
    """
    print("\nSTEP 7: Generating radar chart for cluster comparison...")
    
    # Calculate mean values for each archetype
    archetype_means = df_final.groupby('Archetype')[radar_metrics].mean()
    
    # Normalize to 0-100 scale for better visualization
    # (Use 95th percentile for max to avoid extreme outliers skewing the chart)
    archetype_means_normalized = archetype_means.copy()
    for col in radar_metrics:
        max_val = df_final[col].quantile(0.95) # Use 95th percentile
        if max_val > 0:
            archetype_means_normalized[col] = (archetype_means[col] / max_val) * 100
        else:
            archetype_means_normalized[col] = 0
            
    # Clip values at 100 just in case
    archetype_means_normalized = archetype_means_normalized.clip(lower=0, upper=100)
    
    # Create radar chart
    fig = go.Figure()
    
    colors = {
        ARCHETYPE_PLAYMAKER: '#636EFA', # Plotly Blue
        ARCHETYPE_B2B: '#EF553B',       # Plotly Red
        ARCHETYPE_DM: '#00CC96'         # Plotly Green
    }
    
    for archetype in archetype_means_normalized.index:
        if archetype in colors: # Only plot known archetypes
            fig.add_trace(go.Scatterpolar(
                r=archetype_means_normalized.loc[archetype].values.tolist() + [archetype_means_normalized.loc[archetype].values[0]],
                theta=radar_metrics + [radar_metrics[0]],
                fill='toself',
                name=archetype,
                line={'color': colors.get(archetype, '#999999')}, # FIX for S7498
                opacity=0.7
            ))
            
    fig.update_layout(
        polar={ # FIX for S7498
            'radialaxis': { # FIX for S7498
                'visible': True,
                'range': [0, 100]
            }
        },
        showlegend=True,
        title='Midfielder Archetype Comparison - Average Metrics (Normalized to 95th Percentile)',
        font={'size': 12} # FIX for S7498
    )
    
    # Save to HTML
    # radar_path = os.path.join(script_dir, 'midfielder_radar_comparison.html') # <-- REMOVED
    fig.write_html(radar_path) # <-- USES PASSED-IN PATH
    print(f"✓ Saved radar chart to {radar_path}")

def save_results(df_final, selected_metrics, script_dir, results_path):
    """
    Saves the final clustered data (with player names, archetypes, etc.) to a CSV.
    """
    print("\nSTEP 8: Saving final results to CSV...")
    
    # Define columns to save
    output_cols = [
        COL_PLAYER_SCRIPT, 'Club', COL_MARKET_VALUE, 
        'Archetype', 'Cluster', 'PC1', 'PC2'
    ]
    
    # Add all the metrics that were used in the clustering
    output_cols.extend(selected_metrics)
    
    # Filter to only existing columns
    output_cols = [col for col in output_cols if col in df_final.columns]
    
    output_df = df_final[output_cols].copy()
    
    # Sort by Archetype, then Market Value
    output_df = output_df.sort_values(by=['Archetype', COL_MARKET_VALUE], ascending=[True, False])
    
    # Save
    # results_path = os.path.join(script_dir, 'midfielder_clusters_results.csv') # <-- REMOVED
    output_df.to_csv(results_path, index=False) # <-- USES PASSED-IN PATH
    
    print(f"✓ Saved final results to {results_path}")
    print("\n" + "="*60)
    print("CLUSTER SUMMARY")
    print("="*60)
    print(output_df['Archetype'].value_counts())
    print("="*60)


def run_midfielder_analysis():
    """
    Main function to run the full data science workflow.
    """
    
    # --- Build robust file paths ---
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # --- NEW: Define paths for all 6 files ---
    am_base_path = os.path.join(script_dir, 'Attacking Midfielders.csv')
    dm_base_path = os.path.join(script_dir, 'Defensive Midfielders.csv')
    cm_base_path = os.path.join(script_dir, 'Midfielders.csv')
    
    am_combine_path = os.path.join(script_dir, 'CAM-Combine.csv')
    dm_combine_path = os.path.join(script_dir, 'CDM-Combine.csv')
    cm_combine_path = os.path.join(script_dir, 'CM-Combine.csv')
    
    # === STEP 1: Data Handling ===
    print("STEP 1: Loading and merging data...")
    # Load using the new, full paths
    try:
        # Load all 3 base files
        am_base_raw = pd.read_csv(am_base_path)
        dm_base_raw = pd.read_csv(dm_base_path)
        cm_base_raw = pd.read_csv(cm_base_path)
        
        # Load all 3 combine files
        am_combine_raw = pd.read_csv(am_combine_path)
        dm_combine_raw = pd.read_csv(dm_combine_path)
        cm_combine_raw = pd.read_csv(cm_combine_path)
        
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print("Please make sure all 6 files are in the same folder as the script:")
        print("  Attacking Midfielders.csv, Defensive Midfielders.csv, Midfielders.csv")
        print("  CAM-Combine.csv, CDM-Combine.csv, CM-Combine.csv")
        print(f"In directory: {script_dir}")
        return

    # --- NEW: Concatenate all base files ---
    print("Concatenating all base files (Market Value)...")
    df_base_all = pd.concat([am_base_raw, dm_base_raw, cm_base_raw], ignore_index=True)
    
    # --- NEW: Concatenate all combine files ---
    print("Concatenating all combine files (Metrics)...")
    df_combine_all = pd.concat([am_combine_raw, dm_combine_raw, cm_combine_raw], ignore_index=True)

    # --- Pre-merge diagnostic check ---
    print("\n--- Diagnostic Check ---")
    print(f"Total rows in combined base file: {len(df_base_all)}")
    print(f"Total rows in combined combine file: {len(df_combine_all)}")
    print("--------------------------\n")

    # --- FIX 1: Handle Market Value file ---
    # Select only the columns we need and rename Market Value
    try:
        # Process the COMBINED base dataframe
        df_mid = df_base_all[[COL_PLAYER_NAME, 'Club', COL_MARKET_VALUE_RAW]]
        df_mid = df_mid.rename(columns={COL_MARKET_VALUE_RAW: COL_MARKET_VALUE})
        # Remove potential duplicates from the concatenation
        df_mid = df_mid.drop_duplicates(subset=[COL_PLAYER_NAME, 'Club'])
    except KeyError:
        print("ERROR: Could not find required columns in one of the base files (Midfielders, etc.).")
        # FIX for S3457: Use .format() instead of f-string with constants
        print("Expected: ['{}', 'Club', '{}']".format(COL_PLAYER_NAME, COL_MARKET_VALUE_RAW))
        return
        
    # --- FIX 2: Handle "long" format CM-Combine.csv ---
    # Pivot the data from long to wide format
    try:
        print("Pivoting combined metrics from long to wide format...")
        # Process the COMBINED combine dataframe
        # Drop duplicates first in case a player is in multiple combine files
        df_combine_all_dedup = df_combine_all.drop_duplicates(subset=[COL_PLAYER_NAME, 'Club', 'Metric'])
        
        df_com_wide = df_combine_all_dedup.pivot_table(
            index=[COL_PLAYER_NAME, 'Club'], 
            columns='Metric', 
            values='Value', 
            aggfunc='first'
        ).reset_index()
    except KeyError:
        print("ERROR: Could not find required columns in one of the combine files (CAM, CDM, etc.).")
        # FIX for S3457: Use .format() instead of f-string with constants
        print("Expected: ['{}', 'Club', 'Metric', 'Value']".format(COL_PLAYER_NAME))
        return

    # --- FIX 3: Merge on 'Player Name' and 'Club' ---
    print(f"Merging {len(df_mid)} unique players with {len(df_com_wide)} unique players...")
    # --- EDIT: Relaxed merge to only use Name ---
    # This will find more players, even if their club is different (e.g., after a transfer)
    # We remove 'validate' because 'Name' may no longer be a unique key
    df_merged = pd.merge(
        df_mid, 
        df_com_wide, 
        on=[COL_PLAYER_NAME], # Merging ONLY on Name
        how='outer', # <-- CHANGED from 'inner' to 'outer' to keep all players
        # validate="one_to_one" # Removed this strict check
        suffixes=('_base', '_combine') # Add suffixes to handle duplicate 'Club' col
    )
    
    # --- Rename 'Player Name' to 'Player' for the rest of the script ---
    df_merged = df_merged.rename(columns={COL_PLAYER_NAME: COL_PLAYER_SCRIPT})
    
    # --- FIX for ValueError: Handle 'Club_x' and 'Club_y' created by the merge ---
    # We now use 'Club_base' and 'Club_combine' from the suffixes
    if 'Club_base' in df_merged.columns and 'Club_combine' in df_merged.columns:
        # Prioritize club from base files, but fall back to combine files
        df_merged['Club'] = df_merged['Club_base'].fillna(df_merged['Club_combine'])
        df_merged = df_merged.drop(columns=['Club_base', 'Club_combine'])
    elif 'Club_base' in df_merged.columns:
        df_merged['Club'] = df_merged['Club_base']
        df_merged = df_merged.drop(columns=['Club_base'])
    elif 'Club_combine' in df_merged.columns:
        df_merged['Club'] = df_merged['Club_combine']
        df_merged = df_merged.drop(columns=['Club_combine'])

    
    print(f"Loaded and merged data. Total unique players found: {df_merged.shape[0]}.")

    # === STEP 2: Select Metrics ===
    print("\nSTEP 2: Selecting relevant metrics for clustering...")
    # Define the list of metrics we want to use for clustering
    # These should be the column names *after* pivoting
    all_metrics = [
        "Goals", "Assists", "NPG", "XG", "XA", 
        "Progressive passes", "Progressive carries",
        "Passes completed", "Passes attempted", "Key passes", 
        "Through balls", "Switches", "Shot creating Actions", 
        "Goal Creating Actions", "Tackles", "Dribblers tackles",
        "Interceptions", "Touches", "Aerials Won", "Passes Received"
    ]
    
    # Find which of these metrics actually exist in our merged dataframe
    selected_metrics = [col for col in all_metrics if col in df_merged.columns]
    
    # Also check for the radar metrics, as they are key for labeling
    radar_metrics = [METRIC_PROG_PASSES, METRIC_XA, METRIC_KEY_PASSES, METRIC_TACKLES, METRIC_INTERCEPTIONS, METRIC_AERIALS_WON]
    missing_radar_metrics = [m for m in radar_metrics if m not in df_merged.columns]

    print(f"✓ Found {len(selected_metrics)} out of {len(all_metrics)} possible metrics.")
    if missing_radar_metrics:
        print(f"Warning: Missing key metrics for labeling: {missing_radar_metrics}")
        # Remove missing metrics from the radar list
        radar_metrics = [m for m in radar_metrics if m in df_merged.columns]

    if not selected_metrics:
        print("CRITICAL ERROR: No metrics found to cluster. Check your 'Metric' names in the Combine CSVs.")
        return
        
    # Create the features dataframe (X)
    X = df_merged[selected_metrics].copy()

    # === STEP 3: Preprocessing ===
    print("\nSTEP 3: Preprocessing data...")
    
    # 1. Handle missing values (Impute)
    # Use SimpleImputer to fill NaNs with the mean of the column
    # This is CRITICAL for players from the 'outer' merge who are missing stats
    print("  Imputing missing values with column mean...")
    imputer = SimpleImputer(strategy='mean')
    X_imputed = imputer.fit_transform(X)
    X = pd.DataFrame(X_imputed, columns=X.columns)

    # 2. Detect and remove outliers (Z-score)
    # |z| < 3 means we keep anything within 3 standard deviations of the mean
    # --- EDIT: This was removed as it was dropping too many players ---
    # print("  Skipping outlier removal to keep all players...")
    # z_scores = np.abs(zscore(X))
    # filtered_entries = (z_scores < 3).all(axis=1)
    # X_no_outliers = X[filtered_entries]
    # df_no_outliers = df_merged[filtered_entries].reset_index(drop=True)
    # print(f"  Removed {len(X) - len(X_no_outliers)} outliers.")
    # --- Using all data instead ---
    X_no_outliers = X
    df_no_outliers = df_merged.reset_index(drop=True)


    # 3. Normalize the data (StandardScaler)
    # This ensures all metrics are on the same scale (mean=0, std=1)
    print("  Normalizing data with StandardScaler...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_no_outliers)
    
    # === STEP 4: Dimensionality Reduction (PCA) ===
    print("\nSTEP 4: Applying PCA...")
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    # Store results in the final dataframe
    df_final = df_no_outliers.copy()
    df_final['PC1'] = X_pca[:, 0]
    df_final['PC2'] = X_pca[:, 1]
    
    # Add back the (unscaled) metrics for hover data
    for col in selected_metrics:
        df_final[col] = X_no_outliers[col]
        
    print(f"  PC1 explains {pca.explained_variance_ratio_[0]*100:.1f}% of variance.")
    print(f"  PC2 explains {pca.explained_variance_ratio_[1]*100:.1f}% of variance.")

    # === STEP 5: K-Means Clustering ===
    print("\nSTEP 5: Running K-Means Clustering (k=3)...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10) # Set n_init=10 explicitly
    df_final['Cluster'] = kmeans.fit_predict(X_scaled)
    
    # --- Assign descriptive names to clusters ---
    print("  Assigning cluster archetypes...")
    
    # Get the cluster centers (in scaled space)
    centers_scaled = kmeans.cluster_centers_
    
    # Convert centers back to original (unscaled) feature space
    # To do this, we need to create a "dummy" dataframe with scaled features
    # Then we can use the scaler's inverse_transform
    centers_df_scaled = pd.DataFrame(centers_scaled, columns=X_no_outliers.columns)
    centers_original = scaler.inverse_transform(centers_df_scaled)
    centers = pd.DataFrame(centers_original, columns=X_no_outliers.columns)
    
    cluster_map = {}
    
    # Check if we have the key metrics to perform labeling
    if all(m in centers.columns for m in [METRIC_PROG_PASSES, METRIC_TACKLES, METRIC_INTERCEPTIONS]):
        # Calculate scores for each cluster center
        scores = []
        for i in range(3):
            center = centers.iloc[i]
            score_playmaker = center.get(METRIC_PROG_PASSES, 0) + center.get(METRIC_XA, 0) + center.get(METRIC_KEY_PASSES, 0)
            score_dm = center.get(METRIC_TACKLES, 0) + center.get(METRIC_INTERCEPTIONS, 0) + center.get(METRIC_AERIALS_WON, 0)
            scores.append({'cluster': i, 'playmaker_score': score_playmaker, 'dm_score': score_dm})
        
        # Sort by playmaker score to find the best playmaker
        # *** THIS IS THE FIX ***
        playmaker_cluster = sorted(scores, key=lambda x: x['playmaker_score'], reverse=True)[0]['cluster']
        cluster_map[playmaker_cluster] = ARCHETYPE_PLAYMAKER
        
        # Sort by DM score to find the best DM
        dm_cluster = sorted(scores, key=lambda x: x['dm_score'], reverse=True)[0]['cluster']
        
        # Handle case where one cluster is best at both (unlikely, but possible)
        if dm_cluster in cluster_map:
             # If the best playmaker is ALSO the best DM, find the *second* best DM
             dm_cluster = sorted(scores, key=lambda x: x['dm_score'], reverse=True)[1]['cluster']
        
        cluster_map[dm_cluster] = ARCHETYPE_DM
        
        # The remaining cluster is the Box-to-Box
        for i in range(3):
            if i not in cluster_map:
                cluster_map[i] = ARCHETYPE_B2B
                break
        print(f"  ✓ Mapped clusters: {cluster_map}")
    else:
        print("  Warning: Missing key metrics for automatic labeling. Using generic labels.")
        cluster_map = {0: 'Cluster 0', 1: 'Cluster 1', 2: 'Cluster 2'}

    df_final['Archetype'] = df_final['Cluster'].map(cluster_map)

    # === STEP 6: Interactive Visualization ===
    print("\nSTEP 6: Generating interactive scatter plot...")
    
    # --- NEW: Define all output paths here for correct scope ---
    scatter_path = os.path.join(script_dir, 'midfielder_clusters_scatter.html')
    radar_path = os.path.join(script_dir, 'midfielder_radar_comparison.html')
    results_path = os.path.join(script_dir, 'midfielder_clusters_results.csv')
    
    # Define which columns to show on hover
    hover_data = [
        COL_PLAYER_SCRIPT, 'Club', COL_MARKET_VALUE,
        'XG', 'XA', 'Tackles', 'Interceptions', 'Progressive passes'
    ]
    # Filter hover_data to only include columns that actually exist
    hover_data_final = [col for col in hover_data if col in df_final.columns]
    
    fig = px.scatter(
        df_final,
        x='PC1',
        y='PC2',
        color='Archetype',
        hover_name=COL_PLAYER_SCRIPT,
        hover_data=hover_data_final,
        title="Midfielder Archetypes via K-Means Clustering (All Leagues)",
        labels={
            'PC1': f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%) - "Style"',
            'PC2': f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%) - "Performance"'
        },
        color_discrete_map={
            ARCHETYPE_PLAYMAKER: '#636EFA',
            ARCHETYPE_B2B: '#EF553B',
            ARCHETYPE_DM: '#00CC96',
            'Cluster 0': '#636EFA',
            'Cluster 1': '#EF553B',
            'Cluster 2': '#00CC96',
        }
    )
    
    fig.update_layout(legend_title_text='Midfielder Archetype')
    fig.update_traces(marker={'size': 10, 'opacity': 0.8, 'line': {'width': 1, 'color': 'DarkSlateGrey'}})
    
    # Save to HTML
    # scatter_path = os.path.join(script_dir, 'midfielder_clusters_scatter.html') # <-- MOVED UP
    fig.write_html(scatter_path)
    print(f"✓ Saved interactive scatter plot to {scatter_path}")
    
    # === STEP 7 & 8: Radar Chart and Save Results ===
    if radar_metrics: # Only create radar if we have the metrics
        create_radar_chart(df_final, radar_metrics, script_dir, radar_path) # <-- PASS PATH IN
    else:
        print("\nSTEP 7: Skipping radar chart (missing key metrics).")
        
    save_results(df_final, selected_metrics, script_dir, results_path) # <-- PASS PATH IN
    
    print("\n" + "="*60)
    print("✓✓✓ ANALYSIS COMPLETE! ✓✓✓")
    print("Generated files:")
    print(f"  1. {os.path.basename(scatter_path)}")
    if radar_metrics:
        print(f"  2. {os.path.basename(radar_path)}")
    print(f"  3. {os.path.basename(results_path)}") # <-- FIX: Use variable
    print("="*60)


if __name__ == "__main__":
    # Run the full analysis
    run_midfielder_analysis()

