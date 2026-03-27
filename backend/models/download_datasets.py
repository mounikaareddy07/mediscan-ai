"""
MediScan AI - Dataset Downloader
Downloads medical imaging datasets from direct URLs (no Kaggle account needed).
Uses publicly available research datasets.
"""

import os
import sys
import zipfile
import shutil
import random
import urllib.request
import ssl

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, '..', 'datasets')
os.makedirs(DATASET_DIR, exist_ok=True)

# Disable SSL verification for some research servers
ssl._create_default_https_context = ssl._create_unverified_context


def download_file(url, dest_path, desc=""):
    """Download a file with progress."""
    print(f"  Downloading {desc}...")
    print(f"  URL: {url[:80]}...")

    def progress_hook(count, block_size, total_size):
        if total_size > 0:
            percent = min(100, count * block_size * 100 / total_size)
            mb_done = count * block_size / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            sys.stdout.write(f"\r  Progress: {percent:.1f}% ({mb_done:.1f}/{mb_total:.1f} MB)")
            sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, dest_path, reporthook=progress_hook)
        print(f"\n  ✓ Downloaded successfully!")
        return True
    except Exception as e:
        print(f"\n  ✗ Download failed: {e}")
        return False


def create_train_val_split(src_dir, dest_dir, classes, val_ratio=0.2):
    """Split a dataset into train/val sets."""
    for split in ['train', 'val']:
        for cls in classes:
            os.makedirs(os.path.join(dest_dir, split, cls), exist_ok=True)

    for cls in classes:
        cls_dir = os.path.join(src_dir, cls)
        if not os.path.exists(cls_dir):
            # Try case-insensitive search
            for d in os.listdir(src_dir):
                if d.lower() == cls.lower():
                    cls_dir = os.path.join(src_dir, d)
                    break

        if not os.path.exists(cls_dir):
            print(f"  Warning: Class directory '{cls}' not found in {src_dir}")
            continue

        images = [f for f in os.listdir(cls_dir)
                  if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        random.shuffle(images)

        split_idx = int(len(images) * (1 - val_ratio))
        train_imgs = images[:split_idx]
        val_imgs = images[split_idx:]

        for img in train_imgs:
            shutil.copy2(os.path.join(cls_dir, img),
                        os.path.join(dest_dir, 'train', cls, img))
        for img in val_imgs:
            shutil.copy2(os.path.join(cls_dir, img),
                        os.path.join(dest_dir, 'val', cls, img))

        print(f"  {cls}: {len(train_imgs)} train, {len(val_imgs)} val")


def setup_chest_xray():
    """Download chest X-ray dataset (Pneumonia)."""
    print("\n" + "="*60)
    print("  [1/4] Chest X-Ray Dataset (Pneumonia)")
    print("="*60)

    dataset_path = os.path.join(DATASET_DIR, 'chest_xray')
    if os.path.exists(dataset_path) and count_images(dataset_path) > 50:
        print(f"  Already exists with {count_images(dataset_path)} images. Skipping.")
        return True

    # Try Mendeley Data / GitHub mirrors for chest X-ray
    zip_path = os.path.join(DATASET_DIR, 'chest_xray.zip')

    # Paul Mooney chest X-ray dataset mirror
    urls = [
        "https://data.mendeley.com/public-files/datasets/rscbjbr9sj/files/f12eaf6d-6023-432f-acc9-80c9d7393433/file_downloaded",
    ]

    downloaded = False
    for url in urls:
        if download_file(url, zip_path, "Chest X-ray dataset"):
            downloaded = True
            break

    if downloaded and os.path.exists(zip_path):
        print("  Extracting...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(DATASET_DIR)
            os.remove(zip_path)
            # The extracted folder might be nested
            for item in os.listdir(DATASET_DIR):
                item_path = os.path.join(DATASET_DIR, item)
                if os.path.isdir(item_path) and 'chest' in item.lower():
                    if item_path != dataset_path:
                        if os.path.exists(dataset_path):
                            shutil.rmtree(dataset_path)
                        shutil.move(item_path, dataset_path)
            print("  ✓ Chest X-ray dataset ready!")
            return True
        except Exception as e:
            print(f"  ✗ Extraction failed: {e}")

    # Fallback: Create dataset with sample images for demo
    print("\n  Direct download unavailable. Creating sample dataset...")
    return create_sample_dataset('chest_xray', ['NORMAL', 'PNEUMONIA'])


def setup_brain_tumor():
    """Download brain tumor MRI dataset."""
    print("\n" + "="*60)
    print("  [2/4] Brain Tumor MRI Dataset")
    print("="*60)

    dataset_path = os.path.join(DATASET_DIR, 'brain_tumor')
    if os.path.exists(dataset_path) and count_images(dataset_path) > 50:
        print(f"  Already exists with {count_images(dataset_path)} images. Skipping.")
        return True

    zip_path = os.path.join(DATASET_DIR, 'brain_tumor.zip')

    # Brain tumor dataset from Kaggle mirrors/alternatives
    urls = [
        "https://github.com/sartajbhuvaji/brain-tumor-classification-dataset/archive/master.zip",
    ]

    downloaded = False
    for url in urls:
        if download_file(url, zip_path, "Brain Tumor MRI dataset"):
            downloaded = True
            break

    if downloaded and os.path.exists(zip_path):
        print("  Extracting...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(os.path.join(DATASET_DIR, 'brain_raw'))
            os.remove(zip_path)

            # Find Training and Testing folders and reorganize
            raw_base = os.path.join(DATASET_DIR, 'brain_raw')
            _reorganize_brain(raw_base, dataset_path)
            shutil.rmtree(raw_base, ignore_errors=True)
            print("  ✓ Brain tumor dataset ready!")
            return True
        except Exception as e:
            print(f"  ✗ Extraction failed: {e}")

    print("\n  Direct download unavailable. Creating sample dataset...")
    return create_sample_dataset('brain_tumor', ['glioma', 'meningioma', 'notumor', 'pituitary'])


def setup_skin_lesion():
    """Download skin lesion dataset."""
    print("\n" + "="*60)
    print("  [3/4] Skin Lesion Dataset")
    print("="*60)

    dataset_path = os.path.join(DATASET_DIR, 'skin_lesion')
    if os.path.exists(dataset_path) and count_images(dataset_path) > 50:
        print(f"  Already exists with {count_images(dataset_path)} images. Skipping.")
        return True

    # Try ISIC subset or other public skin lesion datasets
    zip_path = os.path.join(DATASET_DIR, 'skin_lesion.zip')

    urls = [
        "https://github.com/hasibzunair/adversarial-lesions/raw/master/data/ISIC2018_subset.zip",
    ]

    downloaded = False
    for url in urls:
        if download_file(url, zip_path, "Skin Lesion dataset"):
            downloaded = True
            break

    if downloaded and os.path.exists(zip_path):
        print("  Extracting...")
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                z.extractall(os.path.join(DATASET_DIR, 'skin_raw'))
            os.remove(zip_path)
            _reorganize_skin(os.path.join(DATASET_DIR, 'skin_raw'), dataset_path)
            shutil.rmtree(os.path.join(DATASET_DIR, 'skin_raw'), ignore_errors=True)
            print("  ✓ Skin lesion dataset ready!")
            return True
        except Exception as e:
            print(f"  ✗ Extraction failed: {e}")

    print("\n  Direct download unavailable. Creating sample dataset...")
    return create_sample_dataset('skin_lesion', ['benign', 'malignant'])


def setup_retinal():
    """Download retinal scan dataset."""
    print("\n" + "="*60)
    print("  [4/4] Retinal Scan Dataset")
    print("="*60)

    dataset_path = os.path.join(DATASET_DIR, 'retinal')
    if os.path.exists(dataset_path) and count_images(dataset_path) > 50:
        print(f"  Already exists with {count_images(dataset_path)} images. Skipping.")
        return True

    # Try OCT retinal dataset or cataract datasets
    print("\n  Using alternative approach for retinal dataset...")
    return create_sample_dataset('retinal', ['normal', 'cataract'])


def _reorganize_brain(raw_base, dest_path):
    """Reorganize extracted brain tumor dataset."""
    classes = ['glioma', 'meningioma', 'notumor', 'pituitary']

    # Find the actual data directory (might be nested)
    training_dir = None
    testing_dir = None

    for root, dirs, files in os.walk(raw_base):
        for d in dirs:
            dl = d.lower()
            if dl in ('training', 'train'):
                training_dir = os.path.join(root, d)
            elif dl in ('testing', 'test'):
                testing_dir = os.path.join(root, d)

    if training_dir:
        for split_name, src_dir in [('train', training_dir), ('val', testing_dir or training_dir)]:
            if not os.path.exists(src_dir):
                continue
            for cls_folder in os.listdir(src_dir):
                cls_path = os.path.join(src_dir, cls_folder)
                if not os.path.isdir(cls_path):
                    continue
                # Normalize class name
                cls_norm = cls_folder.lower().replace(' ', '').replace('_', '')
                target_cls = None
                for c in classes:
                    if c in cls_norm or cls_norm in c:
                        target_cls = c
                        break
                if target_cls is None:
                    if 'no' in cls_norm or 'healthy' in cls_norm or 'normal' in cls_norm:
                        target_cls = 'notumor'
                    else:
                        continue

                os.makedirs(os.path.join(dest_path, split_name, target_cls), exist_ok=True)
                for img in os.listdir(cls_path):
                    if img.lower().endswith(('.jpg', '.jpeg', '.png')):
                        shutil.copy2(
                            os.path.join(cls_path, img),
                            os.path.join(dest_path, split_name, target_cls, img)
                        )


def _reorganize_skin(raw_base, dest_path):
    """Reorganize skin lesion dataset into benign/malignant."""
    for split in ['train', 'val']:
        for cls in ['benign', 'malignant']:
            os.makedirs(os.path.join(dest_path, split, cls), exist_ok=True)

    # Walk through all extracted files
    all_images = {'benign': [], 'malignant': []}
    for root, dirs, files in os.walk(raw_base):
        folder = os.path.basename(root).lower()
        for f in files:
            if f.lower().endswith(('.jpg', '.jpeg', '.png')):
                fpath = os.path.join(root, f)
                if any(x in folder for x in ['mel', 'malig', 'cancer', 'bcc', 'akiec']):
                    all_images['malignant'].append(fpath)
                elif any(x in folder for x in ['benign', 'nev', 'normal', 'bkl', 'df']):
                    all_images['benign'].append(fpath)
                else:
                    # Default: classify by folder position
                    all_images['benign'].append(fpath)

    for cls, images in all_images.items():
        random.shuffle(images)
        split_idx = int(len(images) * 0.8)
        for img in images[:split_idx]:
            shutil.copy2(img, os.path.join(dest_path, 'train', cls, os.path.basename(img)))
        for img in images[split_idx:]:
            shutil.copy2(img, os.path.join(dest_path, 'val', cls, os.path.basename(img)))


def create_sample_dataset(name, classes, num_per_class=200):
    """Create a synthetic sample dataset using generated medical-like images."""
    import numpy as np
    try:
        from PIL import Image
    except ImportError:
        import cv2

    dataset_path = os.path.join(DATASET_DIR, name)
    print(f"  Generating {num_per_class} synthetic images per class...")

    for split in ['train', 'val']:
        for cls in classes:
            cls_dir = os.path.join(dataset_path, split, cls)
            os.makedirs(cls_dir, exist_ok=True)

            n = num_per_class if split == 'train' else int(num_per_class * 0.25)
            for i in range(n):
                # Generate realistic-looking medical images
                img = _generate_medical_image(name, cls, i)
                img_path = os.path.join(cls_dir, f"{cls}_{split}_{i:04d}.png")
                Image.fromarray(img).save(img_path)

            print(f"    {cls} ({split}): {n} images")

    print(f"  ✓ Sample {name} dataset created!")
    return True


def _generate_medical_image(scan_type, cls, seed):
    """Generate a synthetic medical image for training."""
    import numpy as np
    np.random.seed(seed + hash(cls) % 10000)

    size = 150

    if scan_type == 'chest_xray':
        # Chest X-ray: grayscale, lung-like shapes
        img = np.random.normal(128, 30, (size, size)).astype(np.uint8)
        # Add lung-like ellipses
        y, x = np.ogrid[:size, :size]
        left_lung = ((x - size*0.35)**2 / (size*0.15)**2 + (y - size*0.45)**2 / (size*0.25)**2) < 1
        right_lung = ((x - size*0.65)**2 / (size*0.15)**2 + (y - size*0.45)**2 / (size*0.25)**2) < 1
        img[left_lung] = np.clip(img[left_lung] - 40, 0, 255)
        img[right_lung] = np.clip(img[right_lung] - 40, 0, 255)

        if cls == 'PNEUMONIA':
            # Add opacity patches
            for _ in range(np.random.randint(2, 5)):
                cx, cy = np.random.randint(30, 120, 2)
                r = np.random.randint(10, 25)
                mask = ((x - cx)**2 + (y - cy)**2) < r**2
                img[mask] = np.clip(img[mask] + np.random.randint(30, 60), 0, 255)

        img = np.stack([img]*3, axis=-1)

    elif scan_type == 'brain_tumor':
        # Brain MRI: grayscale, circular brain shape
        img = np.random.normal(40, 15, (size, size)).astype(np.uint8)
        y, x = np.ogrid[:size, :size]
        brain = ((x - size//2)**2 + (y - size//2)**2) < (size*0.4)**2
        img[brain] = np.clip(np.random.normal(120, 20, img[brain].shape), 0, 255).astype(np.uint8)

        if cls != 'notumor':
            # Add tumor-like bright spot
            cx = size//2 + np.random.randint(-20, 20)
            cy = size//2 + np.random.randint(-20, 20)
            r = np.random.randint(8, 20)
            tumor = ((x - cx)**2 + (y - cy)**2) < r**2
            intensity = {'glioma': 200, 'meningioma': 180, 'pituitary': 190}.get(cls, 185)
            img[tumor] = np.clip(np.random.normal(intensity, 10, img[tumor].shape), 0, 255).astype(np.uint8)

        img = np.stack([img]*3, axis=-1)

    elif scan_type == 'skin_lesion':
        # Skin image: colorful, lesion-like
        img = np.random.normal(200, 15, (size, size, 3)).astype(np.uint8)
        img[:,:,0] = np.clip(img[:,:,0] + 20, 0, 255)  # Skin tone

        y, x = np.ogrid[:size, :size]
        cx, cy = size//2 + np.random.randint(-10, 10), size//2 + np.random.randint(-10, 10)
        r = np.random.randint(20, 40)
        lesion = ((x - cx)**2 + (y - cy)**2) < r**2

        if cls == 'malignant':
            img[lesion, 0] = np.clip(np.random.normal(80, 20, img[lesion, 0].shape), 0, 255).astype(np.uint8)
            img[lesion, 1] = np.clip(np.random.normal(40, 15, img[lesion, 1].shape), 0, 255).astype(np.uint8)
            img[lesion, 2] = np.clip(np.random.normal(50, 15, img[lesion, 2].shape), 0, 255).astype(np.uint8)
        else:
            img[lesion, 0] = np.clip(np.random.normal(150, 15, img[lesion, 0].shape), 0, 255).astype(np.uint8)
            img[lesion, 1] = np.clip(np.random.normal(120, 10, img[lesion, 1].shape), 0, 255).astype(np.uint8)
            img[lesion, 2] = np.clip(np.random.normal(100, 10, img[lesion, 2].shape), 0, 255).astype(np.uint8)

    elif scan_type == 'retinal':
        # Retinal scan: dark background, circular fundus
        img = np.zeros((size, size, 3), dtype=np.uint8)
        y, x = np.ogrid[:size, :size]
        fundus = ((x - size//2)**2 + (y - size//2)**2) < (size*0.4)**2

        img[fundus, 0] = np.clip(np.random.normal(140, 20, img[fundus, 0].shape), 0, 255).astype(np.uint8)
        img[fundus, 1] = np.clip(np.random.normal(60, 15, img[fundus, 1].shape), 0, 255).astype(np.uint8)
        img[fundus, 2] = np.clip(np.random.normal(30, 10, img[fundus, 2].shape), 0, 255).astype(np.uint8)

        if cls == 'cataract':
            # Add cloudy patches
            for _ in range(3):
                cx = size//2 + np.random.randint(-15, 15)
                cy = size//2 + np.random.randint(-15, 15)
                r = np.random.randint(10, 20)
                cloud = ((x - cx)**2 + (y - cy)**2) < r**2
                img[cloud] = np.clip(img[cloud] + 60, 0, 255)
    else:
        img = np.random.randint(0, 255, (size, size, 3), dtype=np.uint8)

    return img


def count_images(directory):
    """Count total images in a directory tree."""
    count = 0
    if os.path.exists(directory):
        for root, dirs, files in os.walk(directory):
            count += len([f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
    return count


def download_all():
    """Download/prepare all datasets."""
    print("\n" + "="*60)
    print("  MediScan AI - Dataset Setup")
    print("="*60)

    results = {}
    results['chest_xray'] = setup_chest_xray()
    results['brain_tumor'] = setup_brain_tumor()
    results['skin_lesion'] = setup_skin_lesion()
    results['retinal'] = setup_retinal()

    print("\n" + "="*60)
    print("  Dataset Setup Summary")
    print("="*60)
    for name, success in results.items():
        status = "✓ Ready" if success else "✗ Failed"
        count = count_images(os.path.join(DATASET_DIR, name))
        print(f"  {name:20s} : {status} ({count} images)")
    print("="*60)

    return results


if __name__ == '__main__':
    download_all()
