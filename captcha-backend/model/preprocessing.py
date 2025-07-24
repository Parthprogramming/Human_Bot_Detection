import pandas as pd
import numpy as np
import json
import scipy.stats
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import entropy

# JSON columns
json_columns = [
    "cursor_movements", "cursor_speeds", "cursor_curvature",
    "cursor_acceleration", "key_press_times", "key_hold_times",
    "click_timestamps", "click_intervals", "keyboard_patterns",
    "human_indicators", "bot_indicators", "mouse_movement_debug",
    "speed_calculation_debug", "post_paste_activity", 
    "scroll_speeds" , "mouseJitter" , "micropause" , "hesitation" , "devicefingerprint","canvas_metrics","unsualscreenresolution",
    "gpu_info","timing_metrics","evasion_signals"
]

# Scalar columns
scalar_columns = [
    "total_time", "scroll_changes", "idle_time", "paste_detected",
    "action_count", "bot_fingerprint_score", "tabkeycount",
    "cursor_entropy", "is_automated_browser",
    "cursorAngleVariance" , "missing_canvas_fingerprint"
]

# JSON parser
def parse_json_column(json_str):
    try:
        if isinstance(json_str, list):
            return [float(x) if isinstance(x, (int, float, str)) and str(x).replace('.', '', 1).isdigit() else x for x in json_str]
        if isinstance(json_str, str):
            # Try to parse as JSON, but if it fails, treat as a simple string or hash
            try:
                parsed = json.loads(json_str)
                if isinstance(parsed, list):
                    return [float(x) if isinstance(x, (int, float, str)) and str(x).replace('.', '', 1).isdigit() else x for x in parsed]
                return parsed
            except Exception:
                # If not JSON, just return the string in a list
                return [json_str]
    except Exception as e:
        print(f"⚠️ JSON parse failed: {e} | Data: {json_str}")
    return []

# Feature extractor
# --- Define the full set of expected columns for robust fallback ---
expected_feature_columns = (
    [f"{col}_{suffix}" for col in json_columns for suffix in ['mean', 'std', 'max', 'min', 'count']] +
    [
        "mouse_speed_mean", "mouse_speed_std", "mouse_accel_mean", "mouse_accel_std", "mouse_angle_entropy", "mouse_total_distance", "mouse_num_pauses",
        "typing_interval_mean", "typing_interval_std", "typing_interval_entropy",
        "scroll_speed_mean", "scroll_speed_std",
        "cursor_micro_movement_count", "cursor_movement_entropy",
        "click_interval_mean", "click_interval_std", "click_interval_entropy"
    ] +
    [
        f"{col}_{k}" for col, keys in [
            ("mouse_movement_debug", ["distance", "dx", "dy", "currentSpeed"]),
            ("speed_calculation_debug", ["rawSpeed", "filteredSpeed", "latestSpeed"]),
            ("post_paste_activity", ["keyPresses", "mouseMoves", "clicks", "timeToFirstAction", "timeToLastAction"])
        ] for k in keys
    ] +
    scalar_columns + ["tabKeyCount", "label", "classification"]
)

def extract_features(row):
    try:
        features = {}

        for col in json_columns:
            raw = row.get(col, None)
            values = parse_json_column(raw)
            
            cursor_movements = row.get("cursor_movements", [])
            if isinstance(cursor_movements, str):
                try:
                    cursor_movements = eval(cursor_movements)
                except Exception:
                    cursor_movements = []
                    
            if cursor_movements and isinstance(cursor_movements, list) and len(cursor_movements) > 2:
                xs = [pt["x"] for pt in cursor_movements if "x" in pt]
                ys = [pt["y"] for pt in cursor_movements if "y" in pt]
                ts = [pt["timestamp"] for pt in cursor_movements if "timestamp" in pt]
                # Speed
                speeds = [np.hypot(xs[i+1]-xs[i], ys[i+1]-ys[i])/(ts[i+1]-ts[i]+1e-6) for i in range(len(xs)-1)]
                features["mouse_speed_mean"] = np.mean(speeds)
                features["mouse_speed_std"] = np.std(speeds)
                # Acceleration
                accels = [speeds[i+1]-speeds[i] for i in range(len(speeds)-1)]
                features["mouse_accel_mean"] = np.mean(accels)
                features["mouse_accel_std"] = np.std(accels)
                # Path entropy (angle changes)
                angles = [np.arctan2(ys[i+1]-ys[i], xs[i+1]-xs[i]) for i in range(len(xs)-1)]
                angle_diffs = [angles[i+1]-angles[i] for i in range(len(angles)-1)]
                if angle_diffs:
                    hist, _ = np.histogram(angle_diffs, bins=8, density=True)
                    features["mouse_angle_entropy"] = entropy(hist+1e-6)
                else:
                    features["mouse_angle_entropy"] = np.nan
                # Total distance
                features["mouse_total_distance"] = np.sum([np.hypot(xs[i+1]-xs[i], ys[i+1]-ys[i]) for i in range(len(xs)-1)])
                # Number of stops (pauses > 300ms)
                pauses = [ts[i+1]-ts[i] for i in range(len(ts)-1)]
                features["mouse_num_pauses"] = np.sum(np.array(pauses) > 300)
            else:
                features["mouse_speed_mean"] = np.nan
                features["mouse_speed_std"] = np.nan
                features["mouse_accel_mean"] = np.nan
                features["mouse_accel_std"] = np.nan
                features["mouse_angle_entropy"] = np.nan
                features["mouse_total_distance"] = np.nan
                features["mouse_num_pauses"] = np.nan
                
            key_press_times = row.get("key_press_times", [])
            if isinstance(key_press_times, str):
                try:
                    key_press_times = eval(key_press_times)
                except Exception:
                    key_press_times = []
            if key_press_times and len(key_press_times) > 2:
                intervals = [key_press_times[i+1]-key_press_times[i] for i in range(len(key_press_times)-1)]
                features["typing_interval_mean"] = np.mean(intervals)
                features["typing_interval_std"] = np.std(intervals)
                features["typing_interval_entropy"] = entropy(np.histogram(intervals, bins=8, density=True)[0]+1e-6)
            else:
                features["typing_interval_mean"] = np.nan
                features["typing_interval_std"] = np.nan
                features["typing_interval_entropy"] = np.nan
                
            scroll_speeds = row.get("scroll_speeds", [])
            if isinstance(scroll_speeds, str):
                try:
                    scroll_speeds = eval(scroll_speeds)
                except Exception:
                    scroll_speeds = []
            if scroll_speeds and len(scroll_speeds) > 0:
                features["scroll_speed_mean"] = np.mean(scroll_speeds)
                features["scroll_speed_std"] = np.std(scroll_speeds)
            else:
                features["scroll_speed_mean"] = np.nan
                features["scroll_speed_std"] = np.nan


            if isinstance(cursor_movements, list) and len(cursor_movements) > 1 and isinstance(cursor_movements[0], dict):
                coords = [(v['x'], v['y']) for v in cursor_movements if 'x' in v and 'y' in v]
                dx = np.diff([pt[0] for pt in coords])
                dy = np.diff([pt[1] for pt in coords])
                dist = np.sqrt(dx**2 + dy**2)
                micro_moves = np.sum(dist < 2)  # Count of very small moves
                features["cursor_micro_movement_count"] = micro_moves

                # Entropy of movement distances
                if len(dist) > 1:
                    hist, _ = np.histogram(dist, bins=10)
                    features["cursor_movement_entropy"] = scipy.stats.entropy(hist + 1)  # +1 to avoid log(0)
                else:
                    features["cursor_movement_entropy"] = 0
            else:
                features["cursor_micro_movement_count"] = 0
                features["cursor_movement_entropy"] = 0

            # Entropy of click intervals
            click_timestamps = row.get("click_timestamps", [])
            if isinstance(click_timestamps, str):
                try:
                    click_timestamps = eval(click_timestamps)
                except Exception:
                    click_timestamps = []
            if click_timestamps and len(click_timestamps) > 2:
                click_intervals = [click_timestamps[i+1]-click_timestamps[i] for i in range(len(click_timestamps)-1)]
                features["click_interval_mean"] = np.mean(click_intervals)
                features["click_interval_std"] = np.std(click_intervals)
                features["click_interval_entropy"] = entropy(np.histogram(click_intervals, bins=8, density=True)[0]+1e-6)
            else:
                features["click_interval_mean"] = np.nan
                features["click_interval_std"] = np.nan
                features["click_interval_entropy"] = np.nan


            if isinstance(values, list) and len(values) > 0:
                if isinstance(values[0], dict) and 'x' in values[0]:  # movement paths
                    coords = [(v['x'], v['y']) for v in values if 'x' in v and 'y' in v]
                    dx = np.diff([pt[0] for pt in coords])
                    dy = np.diff([pt[1] for pt in coords])
                    dist = np.sqrt(dx**2 + dy**2)
                    features[f"{col}_mean_distance"] = np.mean(dist) if len(dist) else 0
                    features[f"{col}_total_distance"] = np.sum(dist) if len(dist) else 0
                    features[f"{col}_count"] = len(coords)
                else:
                    numeric_values = []
                    for x in values:
                        try:
                            numeric_values.append(float(x))
                        except (ValueError, TypeError):
                            continue
                    arr = np.array(numeric_values, dtype=np.float64)
                    features[f"{col}_mean"] = np.mean(arr) if len(arr) else 0
                    features[f"{col}_std"] = np.std(arr) if len(arr) else 0
                    features[f"{col}_max"] = np.max(arr) if len(arr) else 0
                    features[f"{col}_min"] = np.min(arr) if len(arr) else 0
                    features[f"{col}_count"] = len(arr)
            else:
                for suffix in ['_mean', '_std', '_max', '_min', '_count']:
                    features[f"{col}{suffix}"] = 0

        # Ensure all expected stats are present even if skipped earlier
        for col in json_columns:
            for suffix in ['_mean', '_std', '_max', '_min', '_count']:
                key = f"{col}{suffix}"
                if key not in features:
                    features[key] = 0

        # Debug fields
        for col, keys in [
            ("mouse_movement_debug", ["distance", "dx", "dy", "currentSpeed"]),
            ("speed_calculation_debug", ["rawSpeed", "filteredSpeed", "latestSpeed"]),
            ("post_paste_activity", ["keyPresses", "mouseMoves", "clicks", "timeToFirstAction", "timeToLastAction"])
        ]:
            parsed = row.get(col, {})
            if isinstance(parsed, str):
                try:
                    parsed = json.loads(parsed)
                except:
                    parsed = {}
            for k in keys:
                features[f"{col}_{k}"] = parsed.get(k, 0) or 0

        # Scalar fields
        for col in scalar_columns:
            features[col] = row.get(col, 0)

        # Fallbacks
        features["tabKeyCount"] = row.get("tabKeyCount", 0)

        # Derived label
        classification = str(row.get("classification", "")).strip().lower()
        features["label"] = 1 if classification == "human" else 0
        features["classification"] = classification.capitalize()

        return pd.DataFrame([features])
    except Exception as e:
        print(f"Error in extract_features: {e} | Row: {row}")
        # Return a DataFrame with all expected columns set to NaN/defaults
        fallback = {col: np.nan for col in expected_feature_columns}
        fallback["label"] = np.nan
        fallback["classification"] = ""
        return pd.DataFrame([fallback])

# --- Feature Audit Utility ---
def audit_features(df, label_col='label'):
    """Prints audit info for feature quality and suggests columns to drop."""
    features_numeric = df.select_dtypes(include=["number", "bool"])
    print("\n--- Feature Audit ---")
    nan_percent = df.isna().mean() * 100
    print("NaN percentage per feature (top 20):")
    print(nan_percent.sort_values(ascending=False).head(20))
    unique_counts = df.nunique()
    print("\nUnique value count per feature (top 20):")
    print(unique_counts.sort_values().head(20))
    # Only calculate variance on numeric columns
    variances = features_numeric.var()
    print("\nVariance per feature (top 20):")
    print(variances.sort_values().head(20))
    drop_nan = nan_percent[nan_percent > 80].index.tolist()
    drop_const = unique_counts[unique_counts <= 1].index.tolist()
    print(f"\nSuggested features to drop (NaN > 80%): {drop_nan}")
    print(f"Suggested features to drop (constant): {drop_const}")
    features_cleaned = df.drop(columns=list(set(drop_nan + drop_const)))
    print(f"\nShape after dropping: {features_cleaned.shape}")

    # if label_col in df.columns:
    #     label = df[label_col]
    #     top_vars = variances.sort_values(ascending=False).index
    #     for col in top_vars:
    #         plt.figure(figsize=(6,3))
    #         try:
    #             sns.histplot(data=df, x=col, hue=label_col, bins=30, kde=True, element="step", stat="density")
    #             plt.title(f"Distribution of {col} by label")
    #             plt.tight_layout()
    #             plt.show()
    #         except Exception as e:
    #             print(f"Could not plot {col}: {e}")
    # return features_cleaned

# Main
if __name__ == "__main__":
    print("\n🚀 Loading and processing...")
    df = pd.read_csv("user-behavior.csv")

    print("\n🔍 Sample raw values:")
    for col in json_columns:
        if col in df.columns:
            print(f"{col}: {type(df[col].iloc[0])} => {df[col].iloc[0]}")
    processed_rows = df.apply(extract_features, axis=1)
    processed_rows_list = []
    for i, r in enumerate(processed_rows.tolist()):
        if not isinstance(r, pd.DataFrame):
            print(f"Row {i} is not a DataFrame! Type: {type(r)}, Value: {r}")
        else:
            processed_rows_list.append(r)
    if processed_rows_list:
        processed_df = pd.concat(processed_rows_list, ignore_index=True)
        # Always reindex to the full set of expected columns
        processed_df = processed_df.reindex(columns=sorted(expected_feature_columns))
        # Merge in all original columns from user_behavior.csv that are not already present
        for col in df.columns:
            if col not in processed_df.columns:
                processed_df[col] = df[col]
    else:
        print("No valid DataFrames in processed_rows!")
        processed_df = pd.DataFrame(columns=sorted(expected_feature_columns))
    if processed_df.empty:
        print("Processed DataFrame is empty after feature extraction. Exiting.")
        exit(1)
    # Remove columns with all NaN or constant values (but keep all original columns)
    nunique = processed_df.nunique(dropna=False)
    constant_cols = nunique[nunique <= 1].index.tolist()
    nan_cols = processed_df.columns[processed_df.isna().all()].tolist()
    drop_cols = list(set(constant_cols + nan_cols))
    if drop_cols:
        print(f"\n🧹 Dropping constant/NaN columns: {drop_cols}")
        processed_df = processed_df.drop(columns=drop_cols)
    else:
        print("\n✅ No constant or all-NaN columns to drop.")
    # --- Feature Audit Call ---
    audit_features(processed_df)
    # Explicitly drop high-NaN and uninformative features based on audit/visualization
    drop_explicit = [
        # High-NaN features (already present)
        'click_interval_entropy', 'click_interval_mean', 'click_interval_std',
        # Features with nearly no bars, very small/overlapped bars, or highly overlapping distributions
        # 'mouse_accel_std', 'mouse_speed_std', 'mouse_accel_mean', 'mouse_speed_mean', 'total_time',
        # 'key_hold_times_max', 'key_press_times_max', 'typing_interval_std', 'key_press_times_std',
        # 'key_hold_times_std', 'keyboard_patterns_std', 'key_press_times_mean', 'key_hold_times_mean',
        # 'key_hold_times_min', 'post_paste_activity_timeToLastAction', 'post_paste_activity_timeToFirstAction',
        # 'cursor_acceleration_min', 'click_intervals_max', 'click_intervals_mean', 'click_intervals_min',
        # 'click_timestamps_std', 'click_intervals_std', 'scroll_speeds_max', 'micropause_std',
        # 'hesitation_max', 'hesitation_std', 'scroll_speeds_min', 'key_press_times_min', 'micropause_max',
        # 'micropause_mean', 'post_paste_activity_mouseMoves', 'cursor_entropy', 'tabkeycount',
        # 'mouse_total_distance', 'typing_interval_mean', 'mouseJitter_max', 'mouseJitter_mean',
        # 'mouseJitter_std', 'mouseJitter_min', 'post_paste_activity_keyPresses', 'post_paste_activity_clicks'
    ]
    processed_df = processed_df.drop(columns=[c for c in drop_explicit if c in processed_df.columns])
    print(f"\n🚫 Explicitly dropped columns: {drop_explicit}")
    print("\n📊 Processed shape after cleaning:", processed_df.shape)
    processed_df.to_csv("processed_user_behavior_final.csv", index=False)
    print("✅ Preprocessing complete. Saved to 'processed_user_behavior_final.csv'")




