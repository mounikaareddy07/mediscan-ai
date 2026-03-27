"""
=================================================================
  MediScan AI — Complete Model Training Notebook for Kaggle
=================================================================

INSTRUCTIONS:
1. Create a NEW Kaggle Notebook (https://www.kaggle.com/code)
2. Enable GPU: Settings → Accelerator → GPU T4 x2
3. Add these 5 datasets via "Add Data" button on the right:
   - paultimothymooney/chest-xray-pneumonia
   - masoudnickparvar/brain-tumor-mri-dataset
   - kmader/skin-cancer-mnist-ham10000
   - paultimothymooney/kermany2018
   - bmadushanirodrigo/fracture-multi-region-x-ray-data
4. Copy ALL the code below into a single cell and run it
5. After training, download the output ZIP from the Output tab

Total training time: ~25-40 minutes on GPU T4
=================================================================
"""

import os
import json
import shutil
import random
import zipfile
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout, BatchNormalization
from tensorflow.keras.models import Model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam

print(f"TensorFlow version: {tf.__version__}")
print(f"GPU available: {tf.config.list_physical_devices('GPU')}")

# ─── Configuration ───────────────────────────────────────────────────
IMG_SIZE = 150
BATCH_SIZE = 32
OUTPUT_DIR = '/kaggle/working/mediscan_models'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Kaggle input paths
KAGGLE_INPUT = '/kaggle/input'


def build_model(num_classes, input_shape=(IMG_SIZE, IMG_SIZE, 3)):
    """Build a MobileNetV2 transfer learning model."""
    base_model = MobileNetV2(
        weights='imagenet',
        include_top=False,
        input_shape=input_shape
    )
    # Freeze base layers
    base_model.trainable = False

    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    x = BatchNormalization()(x)
    x = Dense(128, activation='relu')(x)
    x = Dropout(0.3)(x)
    x = BatchNormalization()(x)
    x = Dense(64, activation='relu')(x)
    x = Dropout(0.2)(x)
    predictions = Dense(num_classes, activation='softmax')(x)

    model = Model(inputs=base_model.input, outputs=predictions)
    return model


def train_and_save(model_name, train_dir, val_dir, classes, epochs=10):
    """Train a model and save as both .keras and .tflite"""
    print(f"\n{'='*60}")
    print(f"  TRAINING: {model_name}")
    print(f"  Classes: {classes}")
    print(f"  Epochs: {epochs}")
    print(f"{'='*60}\n")

    num_classes = len(classes)
    model = build_model(num_classes)

    # Data generators
    train_datagen = ImageDataGenerator(
        rescale=1./255,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.15,
        zoom_range=0.15,
        horizontal_flip=True,
        fill_mode='nearest'
    )
    val_datagen = ImageDataGenerator(rescale=1./255)

    train_gen = train_datagen.flow_from_directory(
        train_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=classes,
        shuffle=True
    )
    val_gen = val_datagen.flow_from_directory(
        val_dir,
        target_size=(IMG_SIZE, IMG_SIZE),
        batch_size=BATCH_SIZE,
        class_mode='categorical',
        classes=classes,
        shuffle=False
    )

    # Compile
    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )

    # Callbacks
    callbacks = [
        EarlyStopping(monitor='val_accuracy', patience=3, restore_best_weights=True),
        ReduceLROnPlateau(monitor='val_loss', patience=2, factor=0.5, min_lr=1e-6),
    ]

    # Train
    history = model.fit(
        train_gen,
        epochs=epochs,
        validation_data=val_gen,
        callbacks=callbacks,
        verbose=1
    )

    best_acc = max(history.history.get('val_accuracy', [0]))
    print(f"\n  ✅ Best Validation Accuracy: {best_acc*100:.1f}%")

    # Save .keras model
    keras_path = os.path.join(OUTPUT_DIR, f'{model_name}.keras')
    model.save(keras_path)
    print(f"  📦 Saved: {keras_path}")

    # Convert to TFLite
    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    converter.optimizations = [tf.lite.Optimize.DEFAULT]
    tflite_model = converter.convert()

    tflite_path = os.path.join(OUTPUT_DIR, f'{model_name}.tflite')
    with open(tflite_path, 'wb') as f:
        f.write(tflite_model)
    tflite_size = os.path.getsize(tflite_path) / (1024 * 1024)
    print(f"  📦 Saved TFLite: {tflite_path} ({tflite_size:.1f} MB)")

    # Save class mapping
    class_map = {str(i): cls for i, cls in enumerate(classes)}
    json_path = os.path.join(OUTPUT_DIR, f'{model_name}_classes.json')
    with open(json_path, 'w') as f:
        json.dump(class_map, f, indent=2)
    print(f"  📦 Saved classes: {json_path}")

    return best_acc


def count_images(directory):
    """Count images in a directory tree."""
    count = 0
    if os.path.exists(directory):
        for root, dirs, files in os.walk(directory):
            count += len([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
    return count


# ═══════════════════════════════════════════════════════════════════════
# MODEL 1: CHEST X-RAY (Normal vs Pneumonia)
# Dataset: paultimothymooney/chest-xray-pneumonia
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "█" * 60)
print("  MODEL 1/5: CHEST X-RAY")
print("█" * 60)

chest_base = os.path.join(KAGGLE_INPUT, 'chest-xray-pneumonia', 'chest_xray')
# Some versions have nested structure
if not os.path.exists(os.path.join(chest_base, 'train')):
    chest_base = os.path.join(KAGGLE_INPUT, 'chest-xray-pneumonia', 'chest_xray', 'chest_xray')

chest_train = os.path.join(chest_base, 'train')
chest_val = os.path.join(chest_base, 'val')
chest_test = os.path.join(chest_base, 'test')

# Use test as validation if val is too small
if count_images(chest_val) < 50:
    chest_val = chest_test

chest_classes = ['NORMAL', 'PNEUMONIA']
print(f"  Train images: {count_images(chest_train)}")
print(f"  Val images: {count_images(chest_val)}")

results = {}

if count_images(chest_train) >= 10:
    acc = train_and_save('chest_xray_model', chest_train, chest_val, chest_classes, epochs=8)
    results['chest_xray'] = acc
else:
    print("  ❌ Dataset not found! Make sure to add 'paultimothymooney/chest-xray-pneumonia'")


# ═══════════════════════════════════════════════════════════════════════
# MODEL 2: BRAIN TUMOR MRI (4 classes)
# Dataset: masoudnickparvar/brain-tumor-mri-dataset
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "█" * 60)
print("  MODEL 2/5: BRAIN TUMOR MRI")
print("█" * 60)

brain_base = os.path.join(KAGGLE_INPUT, 'brain-tumor-mri-dataset')

# Find training and testing directories
brain_train = None
brain_val = None
for item in os.listdir(brain_base):
    item_lower = item.lower()
    item_path = os.path.join(brain_base, item)
    if os.path.isdir(item_path):
        if 'train' in item_lower:
            brain_train = item_path
        elif 'test' in item_lower:
            brain_val = item_path

brain_classes = ['glioma', 'meningioma', 'notumor', 'pituitary']

if brain_train:
    # Check actual folder names and match to our classes
    actual_folders = sorted(os.listdir(brain_train))
    print(f"  Found folders: {actual_folders}")
    
    # Map folder names to lowercase
    folder_map = {}
    for folder in actual_folders:
        folder_lower = folder.lower().replace(' ', '').replace('_', '')
        for cls in brain_classes:
            if cls in folder_lower or folder_lower in cls:
                folder_map[folder] = cls
    
    # If folder names don't match exactly, use actual folder names
    if len(folder_map) < len(brain_classes):
        brain_classes = sorted([f for f in actual_folders if os.path.isdir(os.path.join(brain_train, f))])
    
    print(f"  Train images: {count_images(brain_train)}")
    print(f"  Val images: {count_images(brain_val)}")
    
    if count_images(brain_train) >= 10:
        acc = train_and_save('brain_tumor_model', brain_train, brain_val, brain_classes, epochs=10)
        results['brain_tumor'] = acc
    else:
        print("  ❌ Not enough images")
else:
    print("  ❌ Dataset not found! Make sure to add 'masoudnickparvar/brain-tumor-mri-dataset'")


# ═══════════════════════════════════════════════════════════════════════
# MODEL 3: SKIN LESION (Benign vs Malignant)
# Dataset: kmader/skin-cancer-mnist-ham10000
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "█" * 60)
print("  MODEL 3/5: SKIN LESION")
print("█" * 60)

skin_base = os.path.join(KAGGLE_INPUT, 'skin-cancer-mnist-ham10000')
skin_prepared = os.path.join('/kaggle/working', 'skin_prepared')

# Read metadata CSV
metadata_file = None
for f in os.listdir(skin_base):
    if f.endswith('.csv') and 'metadata' in f.lower():
        metadata_file = os.path.join(skin_base, f)
        break

# Also check for HAM10000_metadata.csv
if not metadata_file:
    for f in os.listdir(skin_base):
        if f.endswith('.csv'):
            metadata_file = os.path.join(skin_base, f)
            break

if metadata_file:
    print(f"  Found metadata: {os.path.basename(metadata_file)}")
    df = pd.read_csv(metadata_file)
    print(f"  Total samples: {len(df)}")
    
    # Classify as benign or malignant
    malignant_types = ['mel', 'bcc', 'akiec']
    benign_types = ['nv', 'bkl', 'df', 'vasc']
    
    df['label'] = df['dx'].apply(lambda x: 'malignant' if x in malignant_types else 'benign')
    print(f"  Benign: {(df['label'] == 'benign').sum()}, Malignant: {(df['label'] == 'malignant').sum()}")
    
    # Find image directories
    img_dirs = []
    for f in os.listdir(skin_base):
        fp = os.path.join(skin_base, f)
        if os.path.isdir(fp):
            img_dirs.append(fp)
    
    # Build image path lookup
    img_paths = {}
    for img_dir in img_dirs:
        for img_file in os.listdir(img_dir):
            if img_file.lower().endswith(('.jpg', '.png', '.jpeg')):
                img_id = os.path.splitext(img_file)[0]
                img_paths[img_id] = os.path.join(img_dir, img_file)
    
    # Create train/val structure
    for split in ['train', 'val']:
        for cls in ['benign', 'malignant']:
            os.makedirs(os.path.join(skin_prepared, split, cls), exist_ok=True)
    
    # Split data 80/20
    df_shuffled = df.sample(frac=1, random_state=42).reset_index(drop=True)
    split_idx = int(len(df_shuffled) * 0.8)
    
    copied = 0
    for idx, row in df_shuffled.iterrows():
        img_id = row['image_id']
        label = row['label']
        split = 'train' if idx < split_idx else 'val'
        
        if img_id in img_paths:
            src = img_paths[img_id]
            dst = os.path.join(skin_prepared, split, label, os.path.basename(src))
            if not os.path.exists(dst):
                shutil.copy2(src, dst)
                copied += 1
    
    print(f"  Copied {copied} images")
    print(f"  Train images: {count_images(os.path.join(skin_prepared, 'train'))}")
    print(f"  Val images: {count_images(os.path.join(skin_prepared, 'val'))}")
    
    skin_classes = ['benign', 'malignant']
    if count_images(os.path.join(skin_prepared, 'train')) >= 10:
        acc = train_and_save('skin_lesion_model', 
                           os.path.join(skin_prepared, 'train'),
                           os.path.join(skin_prepared, 'val'),
                           skin_classes, epochs=8)
        results['skin_lesion'] = acc
else:
    print("  ❌ Metadata CSV not found! Make sure to add 'kmader/skin-cancer-mnist-ham10000'")


# ═══════════════════════════════════════════════════════════════════════
# MODEL 4: RETINAL OCT (4 classes)
# Dataset: paultimothymooney/kermany2018
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "█" * 60)
print("  MODEL 4/5: RETINAL OCT")
print("█" * 60)

retinal_base = os.path.join(KAGGLE_INPUT, 'kermany2018')

# Navigate to find train/test dirs (dataset has nested structure)
retinal_train = None
retinal_val = None

def find_split_dirs(base_path):
    """Recursively find train and test directories."""
    train_dir = None
    test_dir = None
    for root, dirs, files in os.walk(base_path):
        for d in dirs:
            d_lower = d.lower()
            full = os.path.join(root, d)
            if d_lower == 'train' and train_dir is None:
                train_dir = full
            elif d_lower == 'test' and test_dir is None:
                test_dir = full
            elif d_lower == 'val' and test_dir is None:
                test_dir = full
        if train_dir and test_dir:
            break
    return train_dir, test_dir

if os.path.exists(retinal_base):
    retinal_train, retinal_val = find_split_dirs(retinal_base)
    
    if retinal_train:
        retinal_classes = sorted([d for d in os.listdir(retinal_train) 
                                  if os.path.isdir(os.path.join(retinal_train, d))])
        print(f"  Found classes: {retinal_classes}")
        print(f"  Train images: {count_images(retinal_train)}")
        print(f"  Val images: {count_images(retinal_val)}")
        
        if count_images(retinal_train) >= 10:
            acc = train_and_save('retinal_model', retinal_train, retinal_val,
                               retinal_classes, epochs=8)
            results['retinal'] = acc
    else:
        print("  ❌ Train directory not found in dataset")
else:
    print("  ❌ Dataset not found! Make sure to add 'paultimothymooney/kermany2018'")


# ═══════════════════════════════════════════════════════════════════════
# MODEL 5: BONE FRACTURE X-RAY (Fractured vs Normal)
# Dataset: bmadushanirodrigo/fracture-multi-region-x-ray-data
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "█" * 60)
print("  MODEL 5/5: BONE FRACTURE X-RAY")
print("█" * 60)

bone_base = os.path.join(KAGGLE_INPUT, 'fracture-multi-region-x-ray-data')

if os.path.exists(bone_base):
    # Find the structure
    print(f"  Contents: {os.listdir(bone_base)}")
    
    bone_train = None
    bone_val = None
    
    # Look for train/val/test directories
    for root, dirs, files in os.walk(bone_base):
        for d in dirs:
            d_lower = d.lower()
            full = os.path.join(root, d)
            if d_lower == 'train' and bone_train is None:
                bone_train = full
            elif d_lower in ('val', 'test') and bone_val is None:
                bone_val = full
        if bone_train and bone_val:
            break
    
    if bone_train:
        bone_classes = sorted([d for d in os.listdir(bone_train)
                              if os.path.isdir(os.path.join(bone_train, d))])
        print(f"  Found classes: {bone_classes}")
        print(f"  Train images: {count_images(bone_train)}")
        print(f"  Val images: {count_images(bone_val)}")
        
        if count_images(bone_train) >= 10:
            acc = train_and_save('bone_fracture_model', bone_train, bone_val,
                               bone_classes, epochs=8)
            results['bone_fracture'] = acc
    else:
        # Try alternative structure - sometimes flat with class folders
        print("  Looking for alternative structure...")
        all_dirs = []
        for item in os.listdir(bone_base):
            item_path = os.path.join(bone_base, item)
            if os.path.isdir(item_path):
                all_dirs.append(item)
                print(f"    Found: {item}/ ({count_images(item_path)} images)")
        
        if len(all_dirs) >= 2:
            # Create train/val split manually
            bone_prepared = os.path.join('/kaggle/working', 'bone_prepared')
            bone_classes = sorted(all_dirs)
            
            for split in ['train', 'val']:
                for cls in bone_classes:
                    os.makedirs(os.path.join(bone_prepared, split, cls), exist_ok=True)
            
            for cls in bone_classes:
                cls_path = os.path.join(bone_base, cls)
                images = [f for f in os.listdir(cls_path) 
                         if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
                random.shuffle(images)
                split_idx = int(len(images) * 0.8)
                
                for img in images[:split_idx]:
                    shutil.copy2(os.path.join(cls_path, img),
                               os.path.join(bone_prepared, 'train', cls, img))
                for img in images[split_idx:]:
                    shutil.copy2(os.path.join(cls_path, img),
                               os.path.join(bone_prepared, 'val', cls, img))
            
            if count_images(os.path.join(bone_prepared, 'train')) >= 10:
                acc = train_and_save('bone_fracture_model',
                                   os.path.join(bone_prepared, 'train'),
                                   os.path.join(bone_prepared, 'val'),
                                   bone_classes, epochs=8)
                results['bone_fracture'] = acc
else:
    print("  ❌ Dataset not found! Make sure to add 'bmadushanirodrigo/fracture-multi-region-x-ray-data'")


# ═══════════════════════════════════════════════════════════════════════
# PACKAGE ALL MODELS INTO ZIP
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "█" * 60)
print("  PACKAGING MODELS")
print("█" * 60)

# Create summary
summary = {
    'training_results': {},
    'models': [],
    'img_size': IMG_SIZE,
    'architecture': 'MobileNetV2 Transfer Learning'
}

for name, acc in results.items():
    summary['training_results'][name] = f"{acc*100:.1f}%"
    summary['models'].append(name)

with open(os.path.join(OUTPUT_DIR, 'training_summary.json'), 'w') as f:
    json.dump(summary, f, indent=2)

# Create ZIP
zip_path = '/kaggle/working/mediscan_models.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for root, dirs, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.endswith(('.tflite', '.json')):
                filepath = os.path.join(root, file)
                arcname = file  # Flat structure in ZIP
                zipf.write(filepath, arcname)
                print(f"  📦 Added: {file} ({os.path.getsize(filepath)/1024:.0f} KB)")

print(f"\n  ✅ ZIP created: {zip_path}")
print(f"  📥 Download from the 'Output' tab on the right →")

# ═══════════════════════════════════════════════════════════════════════
# FINAL SUMMARY
# ═══════════════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("  🎉 TRAINING COMPLETE — SUMMARY")
print("=" * 60)

for name, acc in results.items():
    status = "✅" if acc > 0.7 else "⚠️"
    print(f"  {status} {name:25s}: {acc*100:.1f}% accuracy")

if not results:
    print("  ❌ No models were trained! Check dataset availability above.")
else:
    print(f"\n  Total models trained: {len(results)}/5")
    print(f"\n  📥 NEXT STEPS:")
    print(f"  1. Click 'Output' tab on the right side panel")
    print(f"  2. Download 'mediscan_models.zip'")
    print(f"  3. Extract the .tflite and _classes.json files")
    print(f"  4. Place them in: backend/models/")
    print(f"  5. Restart your Flask server")

print("=" * 60)
