import numpy as np
import json
import re
import sys
from pathlib import Path
import math

def parse_cameras_txt(path):
    # Returns: {camera_id: (model, width, height, [params])}
    cameras = {}
    with open(path, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("#") or not line:
                continue
            elems = line.split()
            camera_id = int(elems[0])
            model = elems[1]
            width = int(elems[2])
            height = int(elems[3])
            params = list(map(float, elems[4:]))
            cameras[camera_id] = (model, width, height, params)
    return cameras

def parse_images_txt(path):
    # Returns: List of dicts with keys: image_id, qw, qx, qy, qz, tx, ty, tz, camera_id, name
    images = []
    with open(path, "r") as f:
        lines = f.readlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith("#") or not line:
            i += 1
            continue
        elems = line.split()
        if len(elems) < 9:
            i += 1
            continue
        image_id = int(elems[0])
        qw, qx, qy, qz = map(float, elems[1:5])
        tx, ty, tz = map(float, elems[5:8])
        camera_id = int(elems[8])
        name = elems[9]
        images.append({
            "image_id": image_id,
            "qw": qw,
            "qx": qx,
            "qy": qy,
            "qz": qz,
            "tx": tx,
            "ty": ty,
            "tz": tz,
            "camera_id": camera_id,
            "name": name
        })
        i += 2  # images.txt alternates lines (one line for pose, one for pts)
    return images

def qvec2rotmat(qvec):
    # Quaternion (qw, qx, qy, qz) to rotation matrix
    qw, qx, qy, qz = qvec
    R = np.array([
        [1 - 2*qy*qy - 2*qz*qz,     2*qx*qy - 2*qz*qw,     2*qx*qz + 2*qy*qw],
        [2*qx*qy + 2*qz*qw,     1 - 2*qx*qx - 2*qz*qz,     2*qy*qz - 2*qx*qw],
        [2*qx*qz - 2*qy*qw,     2*qy*qz + 2*qx*qw,     1 - 2*qx*qx - 2*qy*qy]
    ])
    return R

def colmap_to_nerfstudio_intrinsics(model, params):
    # For PINHOLE: fx, fy, cx, cy
    # For SIMPLE_PINHOLE: f, cx, cy (fx=fy=f)
    # For SIMPLE_RADIAL: f, cx, cy, k
    # For OPENCV: fx, fy, cx, cy, k1, k2, p1, p2
    # We'll try to get fx, fy, cx, cy always (used by Nerfstudio)
    if model == "PINHOLE":
        fx, fy, cx, cy = params[:4]
    elif model == "SIMPLE_PINHOLE":
        f, cx, cy = params[:3]
        fx, fy = f, f
    elif model == "SIMPLE_RADIAL":
        f, cx, cy, _ = params[:4]
        fx, fy = f, f
    elif model == "OPENCV":
        fx, fy, cx, cy = params[:4]
    else:
        raise RuntimeError(f"Unknown camera model: {model}")
    return fx, fy, cx, cy

def construct_transform_matrix(qvec, tvec):
    # Colmap stores world-to-camera, Nerfstudio wants camera-to-world
    R = qvec2rotmat(qvec)
    t = np.array(tvec).reshape((3, 1))
    w2c = np.eye(4)
    w2c[:3,:3] = R
    w2c[:3, 3] = t.flatten()
    c2w = np.linalg.inv(w2c)
    # return as list of lists for JSON
    return c2w.tolist()

def main(sparse_dir, output_dir):
    # Paths
    cameras_path = Path(sparse_dir+"cameras.txt")
    images_path = Path(sparse_dir+"images.txt")
    transforms_path = Path(output_dir+"transforms.json")

    cameras = parse_cameras_txt(cameras_path)
    images = parse_images_txt(images_path)

    # Use first camera for global intrinsics
    cam0 = cameras[images[0]["camera_id"]]
    model, width, height, params = cam0
    fx, fy, cx, cy = colmap_to_nerfstudio_intrinsics(model, params)

    # Build frames
    frames = []
    for img in images:
        qvec = (img["qw"], img["qx"], img["qy"], img["qz"])
        tvec = (img["tx"], img["ty"], img["tz"])
        c2w = construct_transform_matrix(qvec, tvec)
        frame = {
            "file_path": f"images/{img['name']}",
            "transform_matrix": c2w,
            "colmap_im_id": img["image_id"]
        }
        frames.append(frame)

    ## go here to edit structure of JSON file
    ns_json = {
        "camera_model": "PINHOLE",
        "fl_x": fx,
        "fl_y": fy,
        "cx": cx,
        "cy": cy,
        "w": width,
        "h": height,
        "camera_angle_x": 2*math.atan(.5*width/fx),
  	"camera_angle_y": 2*math.atan(.5*height/fy),
        "frames": frames,
        "ply_file_path": "sparse_pc.ply"
    }

    with open(transforms_path, "w") as f:
        json.dump(ns_json, f, indent=2)

    print(f"Saved Nerfstudio transforms.json ({len(frames)} frames)")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: script.py <path_to_sparse> <output_dir>")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])
