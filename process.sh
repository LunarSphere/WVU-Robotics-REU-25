#!/bin/bash

# we are gonna generate the point cloud with colmap 
# and the transforms with a pythonscript since built in conversions get it wrong

# --- Configuration Variables ---
PROJECT_PATH="/home/wvuguest/Documents/tree_line"
SPARSE_PATH="$PROJECT_PATH/sparse"
MPOSES_PATH="$PROJECT_PATH/m_sparse"        # your known poses (cameras.txt, images.txt, etc.)
DB_PATH="$PROJECT_PATH/database.db"
IMG_PATH="$PROJECT_PATH/images"
GS_OUTPUT_PATH="$PROJECT_PATH/gs_data"

# --- Step 0: Create COLMAP database and move files --- 

touch $DB_PATH
mkdir -p "$MPOSES_PATH/0"  
mkdir -p $SPARSE_PATH
mkdir -p "$SPARSE_PATH/0"
mkdir -p "$PROJECT_PATH/nerfstudio"
mkdir -p "$PROJECT_PATH/nerfstudio/images"
mkdir -p "$PROJECT_PATH/svraster"
mkdir -p "$PROJECT_PATH/svraster/images"


# FIX: Move .txt files into $MPOSES_PATH/0 not $MPOSES_PATH
# cp $PROJECT_PATH/*.txt "$SPARSE_PATH"
rsync -av --progress "$PROJECT_PATH/"*.txt "$SPARSE_PATH/"
cp "$IMG_PATH"/*.jpg "$PROJECT_PATH/nerfstudio/images"
cp "$IMG_PATH"/*.jpg "$PROJECT_PATH/svraster/images"

# --- Step 1: Extract features ---
colmap feature_extractor \
    --database_path $DB_PATH \
    --image_path $IMG_PATH \
    --ImageReader.single_camera 1

# --- Step 2: Match features (exhaustive for small scenes) ---
colmap sequential_matcher \
    --database_path $DB_PATH 
# --- Step 3: Triangulate points using known poses ---
# FIX: Use $MPOSES_PATH/0 as input_path, not $MPOSES_PATH
colmap point_triangulator \
    --database_path $DB_PATH \
    --image_path $IMG_PATH \
    --input_path "$SPARSE_PATH" \
    --output_path "$SPARSE_PATH/0"

#  --- step 4: Convert points3d to sparse_pc.ply format ---
# convert to to txt
colmap model_converter \
--input_path $SPARSE_PATH/0 \
--output_path "$MPOSES_PATH/0" \
--output_type TXT

#convert to ply
colmap model_converter \
--input_path "$MPOSES_PATH/0" \
--output_path "$PROJECT_PATH/sparse_pc.ply" \
--output_type PLY



# --- step 5: Convert images and cameras to transform.json  NERFSTUDIO--- 
python "/home/wvuguest/Desktop/colmap2nerfstudio.py" "$PROJECT_PATH/" "$PROJECT_PATH/nerfstudio/"

# --step 6: convert Images for SVraster
python "/home/wvuguest/Desktop/colmap2svraster.py" "$PROJECT_PATH/" "$PROJECT_PATH/svraster/"






