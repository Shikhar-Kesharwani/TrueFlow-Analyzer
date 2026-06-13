import pandas as pd
import numpy as np
import os
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import warnings
warnings.filterwarnings('ignore')

CSV_FILE = "real_features.csv"
MODEL_FILE = "real_rf_model.joblib"

def main():
    print("========================================")
    print("    REAL-WORLD ML MODEL TRAINER")
    print("========================================")
    
    if not os.path.exists(CSV_FILE):
        print(f"Error: {CSV_FILE} not found. Please run parse_pcap_dataset.py first.")
        return

    print("1. Loading Real Dataset...")
    df = pd.read_csv(CSV_FILE)
    
    # Feature Engineering
    print("2. Generating Statistical Features...")
    size_cols = [f'size_{i}' for i in range(50)]
    iat_cols = [f'iat_{i}' for i in range(50)]
    
    df['size_mean'] = df[size_cols].mean(axis=1)
    df['size_std'] = df[size_cols].std(axis=1)
    df['size_max'] = df[size_cols].max(axis=1)
    df['size_min'] = df[size_cols].min(axis=1)
    
    df['iat_mean'] = df[iat_cols].mean(axis=1)
    df['iat_std'] = df[iat_cols].std(axis=1)
    df['iat_max'] = df[iat_cols].max(axis=1)
    
    X = df.drop('app_type', axis=1)
    y = df['app_type']
    
    print(f"Dataset Shape: {X.shape[0]} flows, {X.shape[1]} features")
    
    # Split for validation
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("3. Training Random Forest Algorithm...")
    clf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=20, n_jobs=-1, class_weight='balanced')
    clf.fit(X_train, y_train)
    
    print("\\n========================================")
    print("       MODEL ACCURACY REPORT")
    print("========================================")
    y_pred = clf.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"Overall Real-World Accuracy: {acc * 100:.2f}%\\n")
    print(classification_report(y_test, y_pred))
    print("========================================\\n")
    
    print("4. Saving Production Model...")
    joblib.dump(clf, MODEL_FILE)
    print(f"[SUCCESS] Model saved as {MODEL_FILE}")
    print("The Dashboard Engine will now automatically use this real-world model!")

if __name__ == "__main__":
    main()
