# date: 01-06-2026
# author: MohantyB
# topic: historic aerial image processing
# description:


import os
import cv2
from PIL import Image

# sub_dir = "1944 4001"
sub_dir = "1951_5129"
# in_prt_dir = r"D:\datasets\wales_gov\penarth_head_to_cold_knap"
in_prt_dir = r"D:\datasets\image_preprocessing\histogram_equalisation\penarth_head_to_cold_knap"
out_prt_dir = r"D:\datasets\image_preprocessing\add_padding\penarth_head_to_cold_knap"

in_dir = os.path.join(in_prt_dir, sub_dir)
out_dir = os.path.join(out_prt_dir, sub_dir)

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

image_list = [os.path.join(in_dir, f) for f in os.listdir(in_dir)
              if f.lower().endswith(('.tif', '.tiff'))]

if len(image_list) == 0:
    print(f"No TIFF images found in {in_dir}. Exiting.")
    exit()

# find max size
max_width = 0
max_height = 0

for image_path in image_list:
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is not None:
        h, w = image.shape[:2]
        max_width = max(max_width, w)
        max_height = max(max_height, h)

print(f'Max width: {max_width}, Max height: {max_height}')


for image_path in image_list:
    # ✅ Read DPI using PIL
    pil_img = Image.open(image_path)
    dpi = pil_img.info.get("dpi", (320, 320))  # fallback if missing
    image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    if image is None:
        continue
    h, w = image.shape[:2]
    pad_w = max_width - w
    pad_h = max_height - h
    print(f'Processing {image_path}: ({w}x{h}), pad ({pad_w},{pad_h})')
#
    if pad_w > 0 or pad_h > 0:
        if len(image.shape) == 2:
            padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w,
                                        cv2.BORDER_CONSTANT, value=0)
#
        elif len(image.shape) == 3 and image.shape[2] == 3:
            padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w,
                                        cv2.BORDER_CONSTANT, value=[0, 0, 0])
            padded = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)  # ✅ fix color
#
        elif len(image.shape) == 3 and image.shape[2] == 4:
            padded = cv2.copyMakeBorder(image, 0, pad_h, 0, pad_w,
                                        cv2.BORDER_CONSTANT, value=[0, 0, 0, 0])
            padded = cv2.cvtColor(padded, cv2.COLOR_BGRA2RGBA)
#
        else:
            print(f'Unsupported: {image_path}')
            continue
#
    else:
        padded = image
        if len(padded.shape) == 3 and padded.shape[2] == 3:
            padded = cv2.cvtColor(padded, cv2.COLOR_BGR2RGB)
        elif len(padded.shape) == 3 and padded.shape[2] == 4:
            padded = cv2.cvtColor(padded, cv2.COLOR_BGRA2RGBA)
#
    # ✅ Convert to PIL and save WITH DPI
    out_name = os.path.basename(image_path).replace('.tif', '_padded.tif')
    out_path = os.path.join(out_dir, out_name)
#
    Image.fromarray(padded).save(
        out_path,
        dpi=dpi,
        compression="none"   # ✅ no data loss
    )
#
    print(f'Saved → {out_path} with DPI {dpi}')

