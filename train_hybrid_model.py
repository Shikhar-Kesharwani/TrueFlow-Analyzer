import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
from sklearn.utils import resample
import joblib
import warnings
warnings.filterwarnings('ignore')

OLD_CSV     = "real_features.csv"
MODERN_CSV  = "modern_features.csv"
MODEL_PATH  = "real_rf_model.joblib"

def load_and_balance():
    print("=" * 55)
    print("   HYBRID MODEL TRAINER (2016 + Modern SNI Data)")
    print("=" * 55)

    # ── Load 2016 data ──
    print("\n[1/4] Loading 2016 academic dataset...")
    df_old = pd.read_csv(OLD_CSV)
    print(f"      Rows: {len(df_old):,}  |  Labels: {df_old['app_type'].nunique()}")

    # ── Load modern SNI-labeled data ──
    print("\n[2/4] Loading modern SNI-labeled data...")
    if not os.path.exists(MODERN_CSV):
        print(f"      [!] {MODERN_CSV} not found — training on 2016 data only.")
        return df_old

    df_modern = pd.read_csv(MODERN_CSV)
    
    # NEW FIX: Remove 'idle-like' chunks from the YouTube flow
    # A video stream has periods of silence/keep-alives. If we train the model on these
    # silent chunks, it will think normal background traffic is YouTube.
    # We enforce a minimum average packet size to only train on HEAVY streaming data.
    size_cols = [c for c in df_modern.columns if 'size' in c]
    df_modern['abs_mean_size'] = df_modern[size_cols].abs().mean(axis=1)
    original_len = len(df_modern)
    df_modern = df_modern[df_modern['abs_mean_size'] > 800].copy()
    df_modern.drop(columns=['abs_mean_size'], inplace=True)
    print(f"      Rows: {original_len:,} (Filtered to {len(df_modern):,} heavy streaming chunks)")
    print(f"      Labels: {df_modern['app_type'].nunique()}")
    print(f"      Apps: {sorted(df_modern['app_type'].unique())}")

    # ── Balance: oversample modern data so it's not drowned out ──
    print("\n[3/4] Balancing dataset (oversampling modern data)...")
    modern_classes = df_modern['app_type'].unique()
    old_class_size = max(df_old['app_type'].value_counts())

    boosted_parts = [df_old]
    for cls in modern_classes:
        cls_rows = df_modern[df_modern['app_type'] == cls]
        # Only oversample if we have very few rows. With 34k rows, no boost needed!
        if len(cls_rows) < 5000:
            target_size = min(old_class_size, 5000)
            oversampled = resample(cls_rows, replace=True, n_samples=int(target_size), random_state=42)
            boosted_parts.append(oversampled)
            print(f"      {cls:20s}: {len(cls_rows):,} → {int(target_size):,} flows (Boosted)")
        else:
            boosted_parts.append(cls_rows)
            print(f"      {cls:20s}: {len(cls_rows):,} flows (Sufficient, no boost needed)")

    df_combined = pd.concat(boosted_parts, ignore_index=True)
    print(f"\n      Final dataset size: {len(df_combined):,} flows")
    return df_combined

def train(df):
    print("\n[4/4] Training Random Forest...")

    feature_cols = [c for c in df.columns if c != 'app_type']
    X = np.array(df[feature_cols].fillna(0), dtype=float)
    y = np.array(df['app_type'], dtype=str)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        n_jobs=-1,
        random_state=42,
        class_weight='balanced'   # extra protection against imbalance
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    print("\n" + "=" * 55)
    print("   ACCURACY REPORT")
    print("=" * 55)
    print(f"   Overall Accuracy: {acc*100:.2f}%\n")
    print(classification_report(y_test, y_pred))

    joblib.dump(clf, MODEL_PATH)
    print(f"\n[SUCCESS] Model saved -> {MODEL_PATH}")
    print("   Restart the live engine to use the new model!")

if __name__ == "__main__":
    df = load_and_balance()
    train(df)
