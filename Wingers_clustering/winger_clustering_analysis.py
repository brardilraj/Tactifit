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
ARCHETYPE_DRIBBLER = "Explosive Dribbler"
ARCHETYPE_CREATOR = "Inverted Creator"
ARCHETYPE_SCORER = "Goal-Scoring Inside Forward"

COL_MARKET_VALUE = "Market Value (M)" # The name our script will use
COL_MARKET_VALUE_RAW = "Market Value (€M)" # The name from the CSV
COL_PLAYER_NAME = "Name" # The name from the CSV
COL_PLAYER_SCRIPT = "Player" # The name our script will use internally

# --- NEW: Key metrics from the Winger image ---
METRIC_PROG_CARRIES = "Progressive carries"
METRIC_TAKE_ONS = "Take-ons"
METRIC_TOUCHES_FINAL_THIRD = "Touches in final third"
METRIC_CROSSES = "Crosses"
METRIC_BALL_RECOVERIES = "Ball Recoveries"
METRIC_PASS_COMPLETION = "Passes completed" # Will be divided by attempted
METRIC_PROG_PASSES = "Progressive passes"
METRIC_KEY_PASSES = "Key passes"
METRIC_XA = "XA"
METRIC_ASSISTS = "Assists"
METRIC_SCA = "Shot creating Actions"
METRIC_GOALS = "Goals"
METRIC_NPG = "NPG"
METRIC_XG = "XG"
METRIC_SHOTS = "Shots"
METRIC_GCA = "Goal Creating Actions"
METRIC_TACKLES = "Tackles"

def create_winger_radar_chart(df_final, radar_metrics, script_dir, radar_path):
    """
    Creates and saves a radar chart comparing the average metrics for each cluster.
    """
    print("\nSTEP 7: Generating radar chart for cluster comparison...")
    
    # Calculate mean values for each archetype
    archetype_means = df_final.groupby('Archetype')[radar_metrics].mean()
    
    # Normalize to 0-100 scale (95th percentile)
    archetype_means_normalized = archetype_means.copy()
    for col in radar_metrics:
        max_val = df_final[col].quantile(0.95)
        if max_val > 0:
            archetype_means_normalized[col] = (archetype_means[col] / max_val) * 100
        else:
            archetype_means_normalized[col] = 0
            
    archetype_means_normalized = archetype_means_normalized.clip(lower=0, upper=100)
    
    # Create radar chart
    fig = go.Figure()
    
    colors = {
        ARCHETYPE_DRIBBLER: '#EF553B', # Plotly Red
        ARCHETYPE_CREATOR: '#636EFA', # Plotly Blue
        ARCHETYPE_SCORER: '#00CC96'   # Plotly Green
    }
    
    for archetype in archetype_means_normalized.index:
        if archetype in colors:
            fig.add_trace(go.Scatterpolar(
                r=archetype_means_normalized.loc[archetype].values.tolist() + [archetype_means_normalized.loc[archetype].values[0]],
                theta=radar_metrics + [radar_metrics[0]],
                fill='toself',
                name=archetype,
                line={'color': colors.get(archetype, '#999999')},
                opacity=0.7
            ))
            
    fig.update_layout(
        polar={'radialaxis': {'visible': True, 'range': [0, 100]}},
        showlegend=True,
        title='Winger Archetype Comparison - Average Metrics (Normalized to 95th Percentile)',
        font={'size': 12}
    )
    
    fig.write_html(radar_path)
    print(f"✓ Saved radar chart to {radar_path}")

def save_winger_results(df_final, selected_metrics, script_dir, results_path):
    """
    Saves the final clustered data to a CSV.
    """
    print("\nSTEP 8: Saving final results to CSV...")
    
    output_cols = [
        COL_PLAYER_SCRIPT, 'Club', COL_MARKET_VALUE, 
        'Archetype', 'Cluster', 'PC1', 'PC2'
    ]
    output_cols.extend(selected_metrics)
    output_cols = [col for col in output_cols if col in df_final.columns]
    output_df = df_final[output_cols].copy()
    
    output_df = output_df.sort_values(by=['Archetype', COL_MARKET_VALUE], ascending=[True, False])
    
    output_df.to_csv(results_path, index=False)
    
    print(f"✓ Saved final results to {results_path}")
    print("\n" + "="*60)
    print("CLUSTER SUMMARY")
    print("="*60)
    print(output_df['Archetype'].value_counts())
    print("="*60)


def run_winger_analysis():
    """
    Main function to run the full data science workflow for WINGERS.
    """
    
    # --- Build robust file paths ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # --- !!! IMPORTANT !!! ---
    # --- These filenames are now updated based on your request ---
    lw_base_path = os.path.join(script_dir, 'Left_Wingers.csv')
    rw_base_path = os.path.join(script_dir, 'Right_Wingers.csv')
    
    lw_combine_path = os.path.join(script_dir, 'LW_combine.csv')
    rw_combine_path = os.path.join(script_dir, 'RW-Combine.csv')
    
    # === STEP 1: Data Handling ===
    print("STEP 1: Loading and merging WINGER data...")
    try:
        # Load all base files
        lw_base_raw = pd.read_csv(lw_base_path)
        rw_base_raw = pd.read_csv(rw_base_path)
        
        # Load all combine files
        lw_combine_raw = pd.read_csv(lw_combine_path)
        rw_combine_raw = pd.read_csv(rw_combine_path)
        
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print("---!!! PLEASE READ !!!---")
        print("I tried to use the filenames you provided, but one was not found.")
        print("Please double-check the spellings in your folder match these:")
        print(f"  {os.path.basename(lw_base_path)}, {os.path.basename(rw_base_path)}")
        print(f"  {os.path.basename(lw_combine_path)}, {os.path.basename(rw_combine_path)}")
        print(f"Looking in directory: {script_dir}")
        return

    # --- Concatenate base files ---
    print("Concatenating all base files (Market Value)...")
    df_base_all = pd.concat([lw_base_raw, rw_base_raw], ignore_index=True)
    
    # --- Concatenate combine files ---
    print("Concatenating all combine files (Metrics)...")
    df_combine_all = pd.concat([lw_combine_raw, rw_combine_raw], ignore_index=True)

    # --- Pre-merge diagnostic check ---
    print("\n--- Diagnostic Check ---")
    print(f"Total rows in combined base file: {len(df_base_all)}")
    print(f"Total rows in combined combine file: {len(df_combine_all)}")
    print("--------------------------\n")

    # --- NEW: Pre-merge diagnostic check (Base Files) ---
    print("\n--- Diagnostic Check (Base Files) ---")
    print("Columns found in combined base file (e.g., Left_Wingers.csv):")
    print(list(df_base_all.columns))
    print("------------------------------------------\n")

    # --- Handle Market Value file ---
    try:
        df_mid = df_base_all[[COL_PLAYER_NAME, 'Club', COL_MARKET_VALUE_RAW]]
        df_mid = df_mid.rename(columns={COL_MARKET_VALUE_RAW: COL_MARKET_VALUE})
        df_mid = df_mid.drop_duplicates(subset=[COL_PLAYER_NAME, 'Club'])
    except KeyError as e:
        print(f"ERROR: Could not find required columns in one of the base files (LW/RW). Mismatch on: {e}")
        print("Expected: ['{}', 'Club', '{}']".format(COL_PLAYER_NAME, COL_MARKET_VALUE_RAW))
        print("Please compare this to the 'Diagnostic Check (Base Files)' output above and let me know the correct names.")
        return
        
    # --- NEW: Pre-pivot diagnostic check (Combine Files) ---
    print("\n--- Diagnostic Check (Combine Files) ---")
    print("Columns found in combined metrics file (e.g., LW_combine.csv):")
    print(list(df_combine_all.columns))
    print("------------------------------------------\n")
        
    # --- Handle "long" format Combine files ---
    try:
        print("Pivoting combined metrics from long to wide format...")
        df_combine_all_dedup = df_combine_all.drop_duplicates(subset=[COL_PLAYER_NAME, 'Club', 'Metric'])
        
        df_com_wide = df_combine_all_dedup.pivot_table(
            index=[COL_PLAYER_NAME, 'Club'], 
            columns='Metric', 
            values='Value', 
            aggfunc='first'
        ).reset_index()
    except KeyError as e:
        print(f"ERROR: Could not find required columns in one of the combine files (LW/RW). Mismatch on: {e}")
        print("Expected: ['{}', 'Club', 'Metric', 'Value']".format(COL_PLAYER_NAME))
        print("Please compare this to the 'Diagnostic Check (Combine Files)' output above and let me know the correct names.")
        return

    # --- FIX: Merge on Name ONLY, then clean up Club ---
    print(f"Merging {len(df_mid)} unique players with {len(df_com_wide)} unique players...")
    df_merged = pd.merge(
        df_mid, 
        df_com_wide, 
        on=[COL_PLAYER_NAME],
        how='outer',
        suffixes=('_base', '_combine') # Will create Club_base and Club_combine
    )
    
    # --- FIX: Smartly combine the Club_base and Club_combine columns ---
    df_merged['Club'] = df_merged['Club_base'].fillna(df_merged['Club_combine'])
    df_merged = df_merged.drop(columns=['Club_base', 'Club_combine'])
    
    df_merged = df_merged.rename(columns={COL_PLAYER_NAME: COL_PLAYER_SCRIPT})
    
    print(f"Loaded and merged data. Total unique players found: {df_merged.shape[0]}.")

    # === STEP 2: Select Metrics ===
    print("\nSTEP 2: Selecting relevant metrics for clustering...")
    # --- NEW: Winger metrics from image ---
    all_metrics = [
        "Goals", "Assists", "NPG", "XG", "XA", 
        "Progressive passes", "Progressive carries",
        "Passes completed", "Passes attempted", "Key passes", 
        "Take-ons", "Touches in final third", "Crosses", "Ball Recoveries",
        "Through balls", "Switches", "Shot creating Actions", 
        "Goal Creating Actions", "Tackles", "Dribblers tackles",
        "Interceptions", "Touches", "Aerials Won", "Passes Received",
        "Shots"
    ]
    
    selected_metrics = [col for col in all_metrics if col in df_merged.columns]
    
    # --- NEW: Calculate Pass Completion % ---
    if "Passes completed" in df_merged.columns and "Passes attempted" in df_merged.columns:
        # Avoid division by zero
        df_merged['Pass Completion %'] = (
            df_merged['Passes completed'] / (df_merged['Passes attempted'] + 1e-6)
        ) * 100
        selected_metrics.append('Pass Completion %')
        print("  ✓ Calculated 'Pass Completion %' metric.")
    
    # --- NEW: Radar metrics based on image ---
    radar_metrics = [
        METRIC_PROG_CARRIES, METRIC_TAKE_ONS, METRIC_CROSSES, # Dribbler
        METRIC_KEY_PASSES, METRIC_PROG_PASSES, METRIC_XA,    # Creator
        METRIC_GOALS, METRIC_XG, METRIC_SHOTS                # Scorer
    ]
    missing_radar_metrics = [m for m in radar_metrics if m not in df_merged.columns]

    print(f"✓ Found {len(selected_metrics)} total metrics.")
    if missing_radar_metrics:
        print(f"Warning: Missing key metrics for labeling/radar: {missing_radar_metrics}")
        radar_metrics = [m for m in radar_metrics if m in df_merged.columns]

    if not selected_metrics:
        print("CRITICAL ERROR: No metrics found to cluster. Check your 'Metric' names in the Combine CSVs.")
        return
        
    X = df_merged[selected_metrics].copy()

    # === STEP 3: Preprocessing ===
    print("\nSTEP 3: Preprocessing data...")
    
    # 1. Impute missing values
    print("  Imputing missing values with column mean...")
    imputer = SimpleImputer(strategy='mean')
    imputer_mv = SimpleImputer(strategy='mean') # Imputer for market value
    
    # --- FIX: Impute Market Value separately ---
    df_merged[COL_MARKET_VALUE] = imputer_mv.fit_transform(df_merged[[COL_MARKET_VALUE]])
    
    X_imputed = imputer.fit_transform(X)
    X = pd.DataFrame(X_imputed, columns=X.columns)

    # 2. Skip outlier removal
    X_no_outliers = X
    df_no_outliers = df_merged.reset_index(drop=True)

    # 3. Normalize
    print("  Normalizing data with StandardScaler...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_no_outliers)
    X_scaled_df = pd.DataFrame(X_scaled, columns=X_no_outliers.columns)
    
    # === STEP 4: Dimensionality Reduction (PCA) ===
    print("\nSTEP 4: Applying PCA...")
    pca = PCA(n_components=2, random_state=42)
    X_pca = pca.fit_transform(X_scaled)
    
    df_final = df_no_outliers.copy()
    df_final['PC1'] = X_pca[:, 0]
    df_final['PC2'] = X_pca[:, 1]
    
    for col in selected_metrics:
        df_final[col] = X_no_outliers[col]
        
    print(f"  PC1 explains {pca.explained_variance_ratio_[0]*100:.1f}% of variance.")
    print(f"  PC2 explains {pca.explained_variance_ratio_[1]*100:.1f}% of variance.")

    # === STEP 5: K-Means Clustering ===
    print("\nSTEP 5: Running K-Means Clustering (k=3)...")
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df_final['Cluster'] = kmeans.fit_predict(X_scaled)
    
    # --- NEW: Assign descriptive names based on winger image ---
    print("  Assigning cluster archetypes based on Winger definitions...")
    
    centers_scaled = kmeans.cluster_centers_
    centers_df_scaled = pd.DataFrame(centers_scaled, columns=X_no_outliers.columns)
    
    cluster_map = {}
    
    # Check if we have enough metrics for the new logic
    key_scoring_metrics = [METRIC_PROG_CARRIES, METRIC_KEY_PASSES, METRIC_GOALS]
    
    if all(m in centers_df_scaled.columns for m in key_scoring_metrics):
        scores = []
        for i in range(3):
            center = centers_df_scaled.iloc[i] # Use the SCALED center
            
            # Score for Explosive Dribbler (High Dribbling, Low Passing)
            score_dribbler = (
                center.get(METRIC_PROG_CARRIES, 0) +
                center.get(METRIC_TAKE_ONS, 0) +
                center.get(METRIC_TOUCHES_FINAL_THIRD, 0) -
                center.get('Pass Completion %', 0) # Penalize for high pass %
            )
            # Score for Inverted Creator (High Passing/Creating, Low Take-ons)
            score_creator = (
                center.get(METRIC_KEY_PASSES, 0) +
                center.get(METRIC_PROG_PASSES, 0) +
                center.get(METRIC_XA, 0) -
                center.get(METRIC_TAKE_ONS, 0) # Penalize for high take-ons
            )
            # Score for Goal-Scoring Inside Forward (High Scoring, Low Crossing/Tackles)
            score_scorer = (
                center.get(METRIC_GOALS, 0) +
                center.get(METRIC_XG, 0) +
                center.get(METRIC_SHOTS, 0) -
                center.get(METRIC_CROSSES, 0) - # Penalize for high crosses
                center.get(METRIC_TACKLES, 0)
            )
            
            scores.append({
                'cluster': i,
                'score_dribbler': score_dribbler,
                'score_creator': score_creator,
                'score_scorer': score_scorer
            })
        
        # Find the best cluster for each archetype
        dribbler_cluster = sorted(scores, key=lambda x: x['score_dribbler'], reverse=True)[0]['cluster']
        creator_cluster = sorted(scores, key=lambda x: x['score_creator'], reverse=True)[0]['cluster']
        scorer_cluster = sorted(scores, key=lambda x: x['score_scorer'], reverse=True)[0]['cluster']
        
        # Simple assignment first:
        cluster_map[dribbler_cluster] = ARCHETYPE_DRIBBLER
        cluster_map[creator_cluster] = ARCHETYPE_CREATOR
        cluster_map[scorer_cluster] = ARCHETYPE_SCORER
        
        # Find the leftover cluster
        all_clusters = {0, 1, 2}
        assigned_clusters = {dribbler_cluster, creator_cluster, scorer_cluster}
        
        if len(assigned_clusters) < 3:
            unassigned_cluster_list = list(all_clusters - assigned_clusters)
            if unassigned_cluster_list: 
                unassigned_cluster = unassigned_cluster_list[0]
                
                assigned_archetypes = set(cluster_map.values())
                all_archetypes = {ARCHETYPE_DRIBBLER, ARCHETYPE_CREATOR, ARCHETYPE_SCORER}
                unassigned_archetype_list = list(all_archetypes - assigned_archetypes)
                
                if unassigned_archetype_list: 
                    unassigned_archetype = unassigned_archetype_list[0]
                    cluster_map[unassigned_cluster] = unassigned_archetype

        print(f"  ✓ Mapped clusters: {cluster_map}")
    else:
        print(f"  Warning: Missing key metrics for automatic labeling: {key_scoring_metrics}. Using generic labels.")
        cluster_map = {0: 'Cluster 0', 1: 'Cluster 1', 2: 'Cluster 2'}

    df_final['Archetype'] = df_final['Cluster'].map(cluster_map)

    # === STEP 6: Interactive Visualization ===
    print("\nSTEP 6: Generating interactive scatter plot...")
    
    # --- Define output paths ---
    scatter_path = os.path.join(script_dir, 'winger_clusters_scatter.html')
    radar_path = os.path.join(script_dir, 'winger_radar_comparison.html')
    results_path = os.path.join(script_dir, 'winger_clusters_results.csv')
    
    hover_data = [
        COL_PLAYER_SCRIPT, 'Club', COL_MARKET_VALUE,
        'Goals', 'Assists', 'XG', 'XA', 'Take-ons', 'Progressive carries', 'Crosses'
    ]
    hover_data_final = [col for col in hover_data if col in df_final.columns]
    
    fig = px.scatter(
        df_final,
        x='PC1',
        y='PC2',
        color='Archetype',
        hover_name=COL_PLAYER_SCRIPT,
        hover_data=hover_data_final,
        title="Winger Archetypes via K-Means Clustering",
        labels={
            'PC1': f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%) - "Style"',
            'PC2': f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%) - "Performance"'
        },
        color_discrete_map={
            ARCHETYPE_DRIBBLER: '#EF553B',
            ARCHETYPE_CREATOR: '#636EFA',
            ARCHETYPE_SCORER: '#00CC96',
            'Cluster 0': '#EF553B',
            'Cluster 1': '#636EFA',
            'Cluster 2': '#00CC96',
        }
    )
    
    fig.update_layout(legend_title_text='Winger Archetype')
    fig.update_traces(marker={'size': 10, 'opacity': 0.8, 'line': {'width': 1, 'color': 'DarkSlateGrey'}})
    
    fig.write_html(scatter_path)
    print(f"✓ Saved interactive scatter plot to {scatter_path}")
    
    # === STEP 7 & 8: Radar Chart and Save Results ===
    if radar_metrics:
        create_winger_radar_chart(df_final, radar_metrics, script_dir, radar_path)
    else:
        print("\nSTEP 7: Skipping radar chart (missing key metrics).")
        
    save_winger_results(df_final, selected_metrics, script_dir, results_path)
    
    print("\n" + "="*60)
    print("✓✓✓ WINGER ANALYSIS COMPLETE! ✓✓✓")
    print("Generated files:")
    print(f"  1. {os.path.basename(scatter_path)}")
    if radar_metrics:
        print(f"  2. {os.path.basename(radar_path)}")
    print(f"  3. {os.path.basename(results_path)}")
    print("="*60)


if __name__ == "__main__":
    # Run the full analysis
    run_winger_analysis()

