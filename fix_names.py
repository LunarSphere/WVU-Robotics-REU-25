import os
import re

IMAGES_TXT = "images.txt"
IMAGES_DIR = "images"
PAD_WIDTH = 6  # e.g. IMG_000007.jpg

def get_img_id(img_name):
    m = re.match(r"IMG_(\d+)\.jpg", img_name)
    return int(m.group(1)) if m else None

def pad_img_name(img_id):
    return f"IMG_{img_id:0{PAD_WIDTH}d}.jpg"

# 1. Rename images in folder
for fname in os.listdir(IMAGES_DIR):
    img_id = get_img_id(fname)
    if img_id is not None:
        new_fname = pad_img_name(img_id)
        if fname != new_fname:
            os.rename(os.path.join(IMAGES_DIR, fname), os.path.join(IMAGES_DIR, new_fname))
            print(f"{fname} -> {new_fname}")

# 2. Edit images.txt lines (only last column)
with open(IMAGES_TXT, "r") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    parts = line.strip().split()
    if len(parts) > 0 and not line.strip().startswith("#"):
        img_name = parts[-1]
        img_id = get_img_id(img_name)
        if img_id is not None:
            parts[-1] = pad_img_name(img_id)
            line = " ".join(parts)
    new_lines.append(line + "\n")

with open(IMAGES_TXT, "w") as f:
    f.writelines(new_lines)

print("Image renaming and images.txt update complete.")