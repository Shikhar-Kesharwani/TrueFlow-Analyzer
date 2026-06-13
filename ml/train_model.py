import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import os

def main():
    csv_path = 'features.csv'
    
    print("=" * 60)
    print(" DPI Engine - Encrypted Traffic Analysis (ML Training)")
    print("=" * 60)
    
    if not os.path.exists(csv_path):
        print(f"Error: Could not find {csv_path}")
        print("Please run the DPI engine with the --export-ml flag first:")
        print("  ./dpi_engine test_dpi.pcap output.pcap --export-ml features.csv")
        return
        
    print(f"Loading dataset: {csv_path}...")
    df = pd.read_csv(csv_path)
    
    print(f"Loaded {len(df)} flow records.")
    
    # Filter out flows with 'Unknown' app type if any
    df = df[df['app_type'] != 'Unknown']
    
    if len(df) < 10:
        print("Warning: Dataset is very small. The model may not perform well.")
        print("Try running the DPI engine on a larger PCAP file.")
        
    print("\nClass distribution:")
    print(df['app_type'].value_counts())
    
    # Prepare features (X) and labels (y)
    print("\nExtracting Aggregated Statistical Features...")
    
    # Separate the sequence columns
    size_cols = [f'size_{i}' for i in range(50)]
    iat_cols = [f'iat_{i}' for i in range(50)]
    
    # Compute aggregate stats
    df['size_mean'] = df[size_cols].mean(axis=1)
    df['size_std'] = df[size_cols].std(axis=1)
    df['size_max'] = df[size_cols].max(axis=1)
    df['size_min'] = df[size_cols].min(axis=1)
    
    df['iat_mean'] = df[iat_cols].mean(axis=1)
    df['iat_std'] = df[iat_cols].std(axis=1)
    df['iat_max'] = df[iat_cols].max(axis=1)
    
    X = df.drop('app_type', axis=1)
    y = df['app_type']
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    print(f"Training set: {len(X_train)} samples")
    print(f"Testing set: {len(X_test)} samples")
    
    # Train the Random Forest Classifier
    print("\nTraining Optimized Random Forest Classifier (n_estimators=200, balanced classes)...")
    clf = RandomForestClassifier(
        n_estimators=200, 
        random_state=42, 
        max_depth=15, 
        class_weight='balanced'
    )
    clf.fit(X_train, y_train)
    
    # Evaluate the model
    print("\nEvaluating model...")
    y_pred = clf.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nModel Accuracy: {accuracy * 100:.2f}%\n")
    
    print("Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))
    
    # Plot Feature Importance
    feature_importances = clf.feature_importances_
    
    # Group features for better visualization
    size_importance = sum(feature_importances[:50])
    iat_importance = sum(feature_importances[50:])
    
    print("Feature Importance Summary:")
    print(f"  Packet Sizes: {size_importance * 100:.2f}%")
    print(f"  Inter-Arrival Times: {iat_importance * 100:.2f}%")
    
    print("\nDone! The ML pipeline is successfully implemented.")
    print("To use this in production, you would export the trained model")
    print("and run inference either in Python or directly in C++ via ONNX.")

if __name__ == "__main__":
    main()
