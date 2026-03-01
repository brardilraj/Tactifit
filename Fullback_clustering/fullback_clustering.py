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
ARCHETYPE_DEFENSIVE = "Defensive Fullback"
ARCHETYPE_INVERTED = "Inverted / Hybrid Fullback"
ARCHETYPE_WINGBACK = "Attacking Wingback"
# --- This is what the script will call the archetypes ---
CLUSTER_NAME_DEFENSIVE = "Cluster 0: Defensive Fullback"
CLUSTER_NAME_INVERTED = "Cluster 1: Inverted / Hybrid Fullback"
CLUSTER_NAME_WINGBACK = "Cluster 2: Attacking Wingback"


COL_MARKET_VALUE = "Market Value (M)" # The name our script will use
# --- !!! CHECK THIS NAME !!! ---
COL_MARKET_VALUE_RAW = "Market Value (€M)" # The name from the CSV 
# --- !!! CHECK THIS NAME !!! ---
COL_PLAYER_NAME = "Name" # The name from the base CSV (e.g., Left backs.csv)
# --- !!! CHECK THIS NAME !!! ---
COL_COMBINE_PLAYER_NAME = "Player Name" # The name from the combine CSV (e.g., LB-Combine.csv)
COL_PLAYER_SCRIPT = "Player" # The name our script will use internally

# --- NEW: Key metrics from the FB table ---
METRIC_TACKLES_WON = "Tackles Won"
METRIC_CHALLENGES_WON = "Challenges Won"
METRIC_INTERCEPTIONS = "Interceptions"
METRIC_BLOCKS = "Blocks"
METRIC_PROG_CARRIES = "Progressive carries"
METRIC_CROSSES = "Crosses"
METRIC_KEY_PASSES = "Key passes"
METRIC_PASS_COMP = "Passes completed"
METRIC_PASS_ATT = "Passes attempted"
METRIC_PROG_PASSES = "Progressive passes"
METRIC_TOUCHES_MID = "Touches (Middle Third)"
METRIC_AERIALS_WON = "Aerials Won"
METRIC_AERIALS_LOST = "Aerials lost"
METRIC_SCA = "Shot creating Actions"
METRIC_XA = "XA"
METRIC_DEF_ACTIONS = "Defensive Actions"

# --- Calculated Metric Names ---
CALC_PASS_COMP_PERC = "Pass Completion %"
CALC_AERIAL_WON_PERC = "Aerials Won %"


def create_fb_radar_chart(df_final, radar_metrics, script_dir, radar_path):
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
        CLUSTER_NAME_DEFENSIVE: '#EF553B', # Plotly Red
        CLUSTER_NAME_INVERTED: '#636EFA', # Plotly Blue
        CLUSTER_NAME_WINGBACK: '#00CC96', # Plotly Green
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
        title='Fullback Archetype Comparison - Average Metrics (Normalized to 95th Percentile)',
        font={'size': 12}
    )
    
    fig.write_html(radar_path)
    print(f"✓ Saved radar chart to {radar_path}")

def save_fb_results(df_final, selected_metrics, script_dir, results_path):
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


def run_fb_analysis():
    """
    Main function to run the full data science workflow for FULLBACKS.
    """
    
    # --- Build robust file paths ---
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # --- !!! IMPORTANT !!! ---
    # --- These are the filenames we'll load ---
    base_paths = [
        os.path.join(script_dir, 'Left backs.csv'),
        os.path.join(script_dir, 'Right backs.csv')
    ]
    combine_paths = [
        os.path.join(script_dir, 'LB-Combine.csv'),
        os.path.join(script_dir, 'RB-Combine.csv')
    ]
    
    # === STEP 1: Data Handling ===
    print("STEP 1: Loading and merging FULLBACK data...")
    try:
        # Load all base files
        df_base_all = pd.concat([pd.read_csv(f) for f in base_paths], ignore_index=True)
        print("Concatenating all base files (Market Value)...")
        
        # Load all combine files
        df_combine_all = pd.concat([pd.read_csv(f) for f in combine_paths], ignore_index=True)
        print("Concatenating all combine files (Metrics)...")
        
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        print("---!!! PLEASE READ !!!---")
        print("I tried to load the Fullback files, but one was not found.")
        print("Please double-check the spellings in your folder match your list.")
        print(f"Looking in directory: {script_dir}")
        return

    # --- Pre-merge diagnostic check ---
    print("\n--- Diagnostic Check ---")
    print(f"Total rows in combined base file: {len(df_base_all)}")
    print(f"Total rows in combined combine file: {len(df_combine_all)}")
    print("--------------------------\n")

    # --- NEW: Pre-merge diagnostic check (Base Files) ---
    print("\n--- Diagnostic Check (Base Files) ---")
    print("Columns found in combined base file (e.g., Left backs.csv):")
    print(list(df_base_all.columns))
    print("------------------------------------------\n")

    # --- Handle Market Value file ---
    try:
        df_mid = df_base_all[[COL_PLAYER_NAME, 'Club', COL_MARKET_VALUE_RAW]]
        df_mid = df_mid.rename(columns={COL_MARKET_VALUE_RAW: COL_MARKET_VALUE})
        df_mid = df_mid.drop_duplicates(subset=[COL_PLAYER_NAME, 'Club'])
    except KeyError as e:
        print("ERROR: Could not find required columns in the base file. Mismatch on: {}".format(e))
        print("Expected: ['{}', 'Club', '{}']".format(COL_PLAYER_NAME, COL_MARKET_VALUE_RAW))
        print("Please compare this to the 'Diagnostic Check (Base Files)' output above and let me know the correct names.")
        return
        
    # --- NEW: Pre-pivot diagnostic check (Combine Files) ---
    print("\n--- Diagnostic Check (Combine Files) ---")
    print("Columns found in combined metrics file (e.g., LB-Combine.csv):")
    print(list(df_combine_all.columns))
    print("------------------------------------------\n")
        
    # --- Handle "long" format Combine files ---
    try:
        print("Pivoting combined metrics from long to wide format...")
        df_combine_all_dedup = df_combine_all.drop_duplicates(subset=[COL_COMBINE_PLAYER_NAME, 'Club', 'Metric'])
        
        df_com_wide = df_combine_all_dedup.pivot_table(
            index=[COL_COMBINE_PLAYER_NAME, 'Club'],
            columns='Metric', 
            values='Value', 
            aggfunc='first'
        ).reset_index()
    except KeyError as e:
        print("ERROR: Could not find required columns in the combine file. Mismatch on: {}".format(e))
        print("Expected: ['{}', 'Club', 'Metric', 'Value']".format(COL_COMBINE_PLAYER_NAME))
        print("Please compare this to the 'Diagnostic Check (Combine Files)' output above and let me know the correct names.")
        return

    # --- Merge on Name ONLY, then clean up Club ---
    print(f"Merging {len(df_mid)} unique players with {len(df_com_wide)} unique players...")
    df_merged = pd.merge(
        df_mid, 
        df_com_wide, 
        left_on=[COL_PLAYER_NAME, 'Club'],
        right_on=[COL_COMBINE_PLAYER_NAME, 'Club'],
        how='outer'
    )
    
    # --- Smartly combine the player name columns ---
    df_merged[COL_PLAYER_SCRIPT] = df_merged[COL_PLAYER_NAME].fillna(df_merged[COL_COMBINE_PLAYER_NAME])
    
    # --- Drop the old name columns ---
    df_merged = df_merged.drop(columns=[COL_PLAYER_NAME, COL_COMBINE_PLAYER_NAME])
    
    print(f"Loaded and merged data. Total unique players found: {df_merged.shape[0]}.")

    # === STEP 2: Select Metrics ===
    print("\nSTEP 2: Selecting relevant metrics for clustering...")
    # --- NEW: FB metrics from table ---
    all_metrics = [
        METRIC_TACKLES_WON, METRIC_CHALLENGES_WON, METRIC_INTERCEPTIONS, METRIC_BLOCKS,
        METRIC_PROG_CARRIES, METRIC_CROSSES, METRIC_KEY_PASSES,
        METRIC_PASS_COMP, METRIC_PASS_ATT, METRIC_PROG_PASSES,
        METRIC_TOUCHES_MID, METRIC_AERIALS_WON, METRIC_AERIALS_LOST,
        METRIC_SCA, METRIC_XA, METRIC_DEF_ACTIONS, "Touches"
    ]
    
    selected_metrics = [col for col in all_metrics if col in df_merged.columns]
    
    # --- NEW: Calculate Pass Completion % ---
    if METRIC_PASS_COMP in df_merged.columns and METRIC_PASS_ATT in df_merged.columns:
        df_merged[CALC_PASS_COMP_PERC] = (
            df_merged[METRIC_PASS_COMP] / (df_merged[METRIC_PASS_ATT] + 1e-6)
        ) * 100
        selected_metrics.append(CALC_PASS_COMP_PERC)
        print(f"  ✓ Calculated '{CALC_PASS_COMP_PERC}' metric.")
        
    # --- NEW: Calculate Aerials Won % ---
    if METRIC_AERIALS_WON in df_merged.columns and METRIC_AERIALS_LOST in df_merged.columns:
        df_merged[CALC_AERIAL_WON_PERC] = (
            df_merged[METRIC_AERIALS_WON] / (df_merged[METRIC_AERIALS_WON] + df_merged[METRIC_AERIALS_LOST] + 1e-6)
        ) * 100
        selected_metrics.append(CALC_AERIAL_WON_PERC)
        print(f"  ✓ Calculated '{CALC_AERIAL_WON_PERC}' metric.")

    # --- NEW: Radar metrics based on table ---
    radar_metrics = [
        METRIC_TACKLES_WON, METRIC_INTERCEPTIONS, CALC_PASS_COMP_PERC,
        METRIC_PROG_PASSES, METRIC_PROG_CARRIES, METRIC_CROSSES,
        METRIC_KEY_PASSES, METRIC_XA
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
    
    # --- Impute Market Value separately ---
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
    
    # --- NEW: Assign descriptive names based on FB table ---
    print("  Assigning cluster archetypes based on FB definitions...")
    
    centers_scaled = kmeans.cluster_centers_
    centers_df_scaled = pd.DataFrame(centers_scaled, columns=X_no_outliers.columns)
    
    cluster_map = {}
    
    # Check if we have enough metrics for the new logic
    key_scoring_metrics = [METRIC_TACKLES_WON, METRIC_PROG_PASSES, METRIC_CROSSES]
    
    if all(m in centers_df_scaled.columns for m in key_scoring_metrics):
        scores = []
        
        aerial_metric_name = CALC_AERIAL_WON_PERC if CALC_AERIAL_WON_PERC in centers_df_scaled.columns else METRIC_AERIALS_WON

        for i in range(3):
            center = centers_df_scaled.iloc[i] # Use the SCALED center
            
            # Score for Defensive Fullback (High Def, Low Off)
            score_defensive = (
                center.get(METRIC_TACKLES_WON, 0) +
                center.get(METRIC_CHALLENGES_WON, 0) +
                center.get(METRIC_INTERCEPTIONS, 0) +
                center.get(METRIC_BLOCKS, 0) -
                center.get(METRIC_PROG_CARRIES, 0) -
                center.get(METRIC_CROSSES, 0) -
                center.get(METRIC_KEY_PASSES, 0)
            )
            # Score for Inverted Fullback (High Pass, Low Cross/Aerial)
            score_inverted = (
                center.get(CALC_PASS_COMP_PERC, 0) +
                center.get(METRIC_PROG_PASSES, 0) +
                center.get(METRIC_TOUCHES_MID, 0) -
                center.get(METRIC_CROSSES, 0) -
                center.get(aerial_metric_name, 0) -
                center.get(METRIC_TACKLES_WON, 0)
            )
            # Score for Attacking Wingback (High Attack, Low Def)
            score_wingback = (
                center.get(METRIC_CROSSES, 0) +
                center.get(METRIC_PROG_CARRIES, 0) +
                center.get(METRIC_KEY_PASSES, 0) +
                center.get(METRIC_SCA, 0) +
                center.get(METRIC_XA, 0) -
                center.get(METRIC_DEF_ACTIONS, 0) -
                center.get(aerial_metric_name, 0)
            )
            
            scores.append({
                'cluster': i,
                'score_defensive': score_defensive,
                'score_inverted': score_inverted,
                'score_wingback': score_wingback
            })
        
        # Find the best cluster for each archetype
        defensive_cluster = sorted(scores, key=lambda x: x['score_defensive'], reverse=True)[0]['cluster']
        inverted_cluster = sorted(scores, key=lambda x: x['score_inverted'], reverse=True)[0]['cluster']
        wingback_cluster = sorted(scores, key=lambda x: x['score_wingback'], reverse=True)[0]['cluster']
        
        # Handle potential overlaps with a simple mapping
        cluster_map = {}
        cluster_map[defensive_cluster] = CLUSTER_NAME_DEFENSIVE
        cluster_map[inverted_cluster] = CLUSTER_NAME_INVERTED
        cluster_map[wingback_cluster] = CLUSTER_NAME_WINGBACK
        
        # Find the leftover cluster
        all_clusters = {0, 1, 2}
        assigned_clusters = {defensive_cluster, inverted_cluster, wingback_cluster}
        
        if len(assigned_clusters) < 3:
            unassigned_cluster_list = list(all_clusters - assigned_clusters)
            if unassigned_cluster_list: 
                unassigned_cluster = unassigned_cluster_list[0]
                
                assigned_archetypes = set(cluster_map.values())
                all_archetypes = {CLUSTER_NAME_DEFENSIVE, CLUSTER_NAME_INVERTED, CLUSTER_NAME_WINGBACK}
                unassigned_archetype_list = list(all_archetypes - assigned_archetypes)
                
                if unassigned_archetype_list: 
                    unassigned_archetype = unassigned_archetype_list[0]
                    cluster_map[unassigned_cluster] = unassigned_archetype
        
        # Ensure all clusters are named
        for i in range(3):
            if i not in cluster_map:
                # Fallback for any unassigned
                if CLUSTER_NAME_DEFENSIVE not in cluster_map.values():
                    cluster_map[i] = CLUSTER_NAME_DEFENSIVE
                elif CLUSTER_NAME_INVERTED not in cluster_map.values():
                    cluster_map[i] = CLUSTER_NAME_INVERTED
                else:
                    cluster_map[i] = CLUSTER_NAME_WINGBACK

        print(f"  ✓ Mapped clusters: {cluster_map}")
    else:
        print(f"  Warning: Missing key metrics for automatic labeling: {key_scoring_metrics}. Using generic labels.")
        cluster_map = {0: CLUSTER_NAME_DEFENSIVE, 1: CLUSTER_NAME_INVERTED, 2: CLUSTER_NAME_WINGBACK}

    df_final['Archetype'] = df_final['Cluster'].map(cluster_map)

    # === STEP 6: Interactive Visualization ===
    print("\nSTEP 6: Generating interactive scatter plot...")
    
    # --- Define output paths ---
    scatter_path = os.path.join(script_dir, 'fb_clusters_scatter.html')
    radar_path = os.path.join(script_dir, 'fb_radar_comparison.html')
    results_path = os.path.join(script_dir, 'fb_clusters_results.csv')
    
    hover_data = [
        COL_PLAYER_SCRIPT, 'Club', COL_MARKET_VALUE,
        METRIC_TACKLES_WON, METRIC_PROG_PASSES, METRIC_PROG_CARRIES,
        METRIC_CROSSES, METRIC_KEY_PASSES
    ]
    hover_data_final = [col for col in hover_data if col in df_final.columns]
    
    # --- Add the final player name to the dataframe for hover ---
    df_final[COL_PLAYER_SCRIPT] = df_merged[COL_PLAYER_SCRIPT]
    
    fig = px.scatter(
        df_final,
        x='PC1',
        y='PC2',
        color='Archetype',
        hover_name=COL_PLAYER_SCRIPT,
        hover_data=hover_data_final,
        title="Fullback Archetypes via K-Means Clustering",
        labels={
            'PC1': f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%) - "Attacking Style"',
            'PC2': f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%) - "Defensive/Buildup Style"'
        },
        color_discrete_map={
            CLUSTER_NAME_DEFENSIVE: '#EF553B',
            CLUSTER_NAME_INVERTED: '#636EFA',
            CLUSTER_NAME_WINGBACK: '#00CC96',
        }
    )
    
    fig.update_layout(legend_title_text='FB Archetype')
    fig.update_traces(marker={'size': 10, 'opacity': 0.8, 'line': {'width': 1, 'color': 'DarkSlateGrey'}})
    
    fig.write_html(scatter_path)
    print(f"✓ Saved interactive scatter plot to {scatter_path}")
    
    # === STEP 7 & 8: Radar Chart and Save Results ===
    if radar_metrics:
        create_fb_radar_chart(df_final, radar_metrics, script_dir, radar_path)
    else:
        print("\nSTEP 7: Skipping radar chart (missing key metrics).")
        
    save_fb_results(df_final, selected_metrics, script_dir, results_path)
    
    print("\n" + "="*60)
    print("✓✓✓ FULLBACK ANALYSIS COMPLETE! ✓✓✓")
    print("Generated files:")
    print(f"  1. {os.path.basename(scatter_path)}")
    if radar_metrics:
        print(f"  2. {os.path.basename(radar_path)}")
    print(f"  3. {os.path.basename(results_path)}")
    print("="*60)


if __name__ == "__main__":
    # Run the full analysis
    run_fb_analysis()
