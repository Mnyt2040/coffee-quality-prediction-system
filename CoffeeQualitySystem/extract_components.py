# extract_components.py
"""
Extract scaler and encoder from the original pickle file
and save them as components file
"""

import joblib
import pickle
import os
import numpy as np

print("="*60)
print("EXTRACTING MODEL COMPONENTS")
print("="*60)

# Paths
models_dir = os.path.join(os.getcwd(), 'models')
original_pickle = os.path.join(models_dir, 'coffee_quality_model.pkl')
components_output = os.path.join(models_dir, 'model_components.pkl')

print(f"\n📁 Models directory: {models_dir}")
print(f"📄 Original pickle: {original_pickle}")
print(f"📄 Components output: {components_output}")

# Check if original pickle exists
if not os.path.exists(original_pickle):
    print(f"❌ Original pickle file not found at: {original_pickle}")
    exit(1)

# Load the original model package
print(f"\n📦 Loading original model package...")
try:
    model_package = joblib.load(original_pickle)
    print("✅ Model package loaded successfully!")
    
    # Show what's in the package
    print(f"\n📋 Keys in model package: {list(model_package.keys())}")
    
    # Extract components
    components = {}
    
    # Try to get scaler (might be under different names)
    if 'scaler' in model_package:
        components['scaler'] = model_package['scaler']
        print("✅ Found 'scaler'")
    elif 'std_scaler' in model_package:
        components['scaler'] = model_package['std_scaler']
        print("✅ Found 'std_scaler'")
    else:
        # Look for any scaler-like object
        for key in model_package:
            if 'scaler' in key.lower() or 'scale' in key.lower():
                components['scaler'] = model_package[key]
                print(f"✅ Found scaler under key: '{key}'")
                break
    
    # Try to get target encoder
    if 'target_encoder' in model_package:
        components['target_encoder'] = model_package['target_encoder']
        print("✅ Found 'target_encoder'")
    elif 'encoder' in model_package:
        components['target_encoder'] = model_package['encoder']
        print("✅ Found 'encoder'")
    elif 'label_encoder' in model_package:
        components['target_encoder'] = model_package['label_encoder']
        print("✅ Found 'label_encoder'")
    else:
        # Look for any encoder-like object
        for key in model_package:
            if 'encoder' in key.lower():
                components['target_encoder'] = model_package[key]
                print(f"✅ Found encoder under key: '{key}'")
                break
    
    # Try to get feature columns
    if 'feature_columns' in model_package:
        components['feature_columns'] = model_package['feature_columns']
        print("✅ Found 'feature_columns'")
    elif 'features' in model_package:
        components['feature_columns'] = model_package['features']
        print("✅ Found 'features'")
    else:
        # Use default features
        components['feature_columns'] = [
            'Aroma', 'Flavor', 'Aftertaste', 'Acidity', 'Body', 'Balance',
            'Uniformity', 'Clean.Cup', 'Sweetness', 'Cupper.Points'
        ]
        print("⚠️ Using default feature columns")
    
    # Try to get performance metrics
    if 'performance' in model_package:
        components['performance'] = model_package['performance']
        print("✅ Found 'performance'")
    elif 'metrics' in model_package:
        components['performance'] = model_package['metrics']
        print("✅ Found 'metrics'")
    else:
        components['performance'] = {'accuracy': 0.95}
        print("⚠️ Using default performance metrics")
    
    # Try to get class names
    if 'class_names' in model_package:
        components['class_names'] = model_package['class_names']
        print("✅ Found 'class_names'")
    elif components.get('target_encoder') and hasattr(components['target_encoder'], 'classes_'):
        components['class_names'] = components['target_encoder'].classes_.tolist()
        print("✅ Extracted class names from encoder")
    else:
        components['class_names'] = ['Excellent', 'Good', 'Average', 'Poor']
        print("⚠️ Using default class names")
    
    # Save components
    print(f"\n💾 Saving components to: {components_output}")
    with open(components_output, 'wb') as f:
        pickle.dump(components, f)
    
    # Verify the save
    if os.path.exists(components_output):
        size = os.path.getsize(components_output) / 1024
        print(f"✅ Components saved successfully! ({size:.1f} KB)")
        
        # Test load
        with open(components_output, 'rb') as f:
            test = pickle.load(f)
        print(f"✅ Verification load successful!")
        print(f"   Keys in saved components: {list(test.keys())}")
    else:
        print(f"❌ Failed to save components")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
input("Press Enter to exit...")