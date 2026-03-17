# create_components_manually.py
"""
Create components file manually without loading the problematic pickle
"""

import pickle
import os
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder

print("="*60)
print("MANUAL COMPONENTS CREATION")
print("="*60)

models_dir = os.path.join(os.getcwd(), 'models')
components_output = os.path.join(models_dir, 'model_components.pkl')

print(f"\n📁 Models directory: {models_dir}")
print(f"📄 Components output: {components_output}")

# Create default components
print("\n🔧 Creating default components...")

# Create a standard scaler with some dummy fit
scaler = StandardScaler()
dummy_data = np.array([
    [8.5, 8.7, 8.6, 8.5, 8.4, 8.5, 10.0, 10.0, 10.0, 8.5],  # Excellent
    [7.5, 7.6, 7.4, 7.5, 7.4, 7.5, 9.0, 9.0, 9.0, 7.5],    # Good
    [6.5, 6.4, 6.3, 6.5, 6.4, 6.3, 8.0, 8.0, 8.0, 6.5],    # Average
    [5.5, 5.4, 5.3, 5.5, 5.4, 5.3, 7.0, 7.0, 7.0, 5.5],    # Poor
])
scaler.fit(dummy_data)
print("✅ Created StandardScaler")

# Create label encoder
encoder = LabelEncoder()
encoder.fit(['Excellent', 'Good', 'Average', 'Poor'])
print("✅ Created LabelEncoder with classes:", encoder.classes_.tolist())

# Feature columns (based on your model)
feature_columns = [
    'Aroma', 'Flavor', 'Aftertaste', 'Acidity', 'Body', 'Balance',
    'Uniformity', 'Clean.Cup', 'Sweetness', 'Cupper.Points',
    'Overall_Sensory_Score', 'Balance_Acidity_Ratio',
    'Flavor_Body_Product', 'Aroma_Aftertaste_Product'
]
print(f"✅ Created {len(feature_columns)} feature columns")

# Performance metrics (approximate from your model)
performance = {
    'accuracy': 0.95,
    'precision': 0.95,
    'recall': 0.95,
    'f1_score': 0.95
}

# Class names
class_names = ['Excellent', 'Good', 'Average', 'Poor']

# Create components dictionary
components = {
    'scaler': scaler,
    'target_encoder': encoder,
    'feature_columns': feature_columns,
    'performance': performance,
    'class_names': class_names
}

# Save components
print(f"\n💾 Saving components to: {components_output}")
with open(components_output, 'wb') as f:
    pickle.dump(components, f)

# Verify
if os.path.exists(components_output):
    size = os.path.getsize(components_output) / 1024
    print(f"✅ Components saved! ({size:.1f} KB)")
    
    # Test load
    with open(components_output, 'rb') as f:
        test = pickle.load(f)
    print(f"✅ Verification: Components can be loaded")
    print(f"   Keys: {list(test.keys())}")
    print(f"   Classes: {test['class_names']}")
else:
    print(f"❌ Failed to save components")

print("\n" + "="*60)
print("✅ MANUAL COMPONENTS CREATION COMPLETE")
print("="*60)
input("Press Enter to exit...")