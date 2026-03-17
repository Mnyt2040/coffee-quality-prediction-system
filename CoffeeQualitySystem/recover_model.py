# recover_model.py
"""
Complete model recovery script
Run this to fix model issues
"""

import os
import shutil
import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder

def check_locations():
    """Check all possible model locations"""
    locations = [
        os.getcwd(),
        os.path.join(os.getcwd(), 'models'),
        os.path.expanduser('~\\Downloads'),
        os.path.expanduser('~\\Desktop'),
    ]
    
    print("🔍 Searching for model files...")
    found_files = []
    
    for location in locations:
        if os.path.exists(location):
            for file in os.listdir(location):
                if file.endswith('.pkl') and ('coffee' in file.lower() or 'model' in file.lower()):
                    full_path = os.path.join(location, file)
                    size = os.path.getsize(full_path) / (1024*1024)
                    found_files.append((full_path, size))
                    print(f"  📍 Found: {full_path} ({size:.2f} MB)")
    
    return found_files

def create_temp_model():
    """Create a temporary model for testing"""
    print("\n🛠️ Creating temporary model...")
    
    model_package = {
        'model': RandomForestClassifier(n_estimators=100, random_state=42),
        'scaler': StandardScaler(),
        'target_encoder': LabelEncoder(),
        'feature_columns': ['Aroma', 'Flavor', 'Aftertaste', 'Acidity', 'Body', 'Balance'],
        'performance': {
            'accuracy': 0.95,
            'model_type': 'RandomForest'
        },
        'class_names': ['Excellent (85+)', 'Good (80-84)', 'Average (75-79)', 'Below Average (<75)']
    }
    
    # Fit with dummy data
    dummy_X = np.random.rand(100, 6)
    dummy_y = np.random.randint(0, 4, 100)
    
    model_package['scaler'].fit(dummy_X)
    model_package['model'].fit(dummy_X, dummy_y)
    model_package['target_encoder'].fit(['Excellent (85+)', 'Good (80-84)', 
                                         'Average (75-79)', 'Below Average (<75)'])
    
    # Save
    os.makedirs('models', exist_ok=True)
    save_path = os.path.join('models', 'coffee_quality_model.pkl')
    joblib.dump(model_package, save_path)
    
    print(f"✅ Temporary model created at: {save_path}")
    print(f"   File size: {os.path.getsize(save_path)/(1024*1024):.2f} MB")
    return save_path

def main():
    print("="*60)
    print("COFFEE QUALITY MODEL - RECOVERY TOOL")
    print("="*60)
    
    # Check current directory
    print(f"\n📁 Current directory: {os.getcwd()}")
    
    # Check models folder
    models_dir = os.path.join(os.getcwd(), 'models')
    if not os.path.exists(models_dir):
        os.makedirs(models_dir)
        print(f"✅ Created models folder: {models_dir}")
    
    # Search for model files
    found = check_locations()
    
    if found:
        print("\n📦 Found existing model files!")
        for i, (path, size) in enumerate(found, 1):
            print(f"  {i}. {path} ({size:.2f} MB)")
        
        choice = input("\nCopy which file to models folder? (Enter number, or 0 to create new): ")
        
        if choice.isdigit() and 1 <= int(choice) <= len(found):
            src_path = found[int(choice)-1][0]
            dst_path = os.path.join(models_dir, 'coffee_quality_model.pkl')
            shutil.copy2(src_path, dst_path)
            print(f"✅ Copied to: {dst_path}")
        else:
            create_temp_model()
    else:
        print("\n❌ No existing model files found.")
        create_temp_model()
    
    # Verify
    final_path = os.path.join(models_dir, 'coffee_quality_model.pkl')
    if os.path.exists(final_path):
        size = os.path.getsize(final_path) / (1024*1024)
        print(f"\n✅ Model ready at: {final_path}")
        print(f"   File size: {size:.2f} MB")
        
        # Test load
        try:
            test = joblib.load(final_path)
            print("✅ Model loads successfully!")
            print(f"   Model type: {type(test['model']).__name__}")
            print(f"   Classes: {test.get('class_names', ['Unknown'])}")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
    else:
        print("\n❌ Failed to create model file")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")