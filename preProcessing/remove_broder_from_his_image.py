# date: 02-03-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to remove the border from the input image


# to do: the in_dir might have sub dirs


import os
import cv2
import numpy as np
from skimage.measure import label
import matplotlib.pyplot as plt

#  find the script path and set it as working directory
git_dir = r"C:\Users\c25045127\OneDrive - Cardiff University\data_analysis"

# sub_dir = "1942 4220"
sub_dir = "1944 4001"
in_prt_dir = r"D:\datasets\wales_gov\penarth_head_to_cold_knap"
out_prt_dir = r"D:\datasets\image_preprocessing\remove_border\penarth_head_to_cold_knap"

in_dir = os.path.join(in_prt_dir, sub_dir)
out_dir = os.path.join(out_prt_dir, sub_dir)

if not os.path.exists(out_dir):
    os.makedirs(out_dir)

image_list = [f for f in os.listdir(in_dir) if f.endswith('.tif') or f.endswith('.tiff')]

def make_binary_mask(image, type):
    # take threshold as the 2th percentile of the template pixel values to ensure we capture the relevant features while minimizing noise
    if type == "fiducial":
        threshold = np.percentile(image, 5)
    else:
        threshold = np.percentile(image, 2)  # Default threshold for other types
    # threshold = np.median(image) * 0.7
    _, binary_mask = cv2.threshold(image, threshold, 255, cv2.THRESH_BINARY)
    return binary_mask

template_path_top = r"structureFromMotion\sample_data\fiducial_template_top.tif"
template_path_bottom = r"structureFromMotion\sample_data\fiducial_template_bottom.tif"
template_path_left = r"structureFromMotion\sample_data\fiducial_template_left.tif"
template_path_right = r"structureFromMotion\sample_data\fiducial_template_right.tif"
template_top = cv2.imread(os.path.join(git_dir, template_path_top), cv2.IMREAD_GRAYSCALE)
template_bottom = cv2.imread(os.path.join(git_dir, template_path_bottom), cv2.IMREAD_GRAYSCALE)
template_left = cv2.imread(os.path.join(git_dir, template_path_left), cv2.IMREAD_GRAYSCALE)
template_right = cv2.imread(os.path.join(git_dir, template_path_right), cv2.IMREAD_GRAYSCALE)

if template_top is None or template_bottom is None or template_left is None or template_right is None:
    raise ValueError("template not loaded properly")

# rotate template in 4 orientations
template_top = make_binary_mask(cv2.equalizeHist(template_top), "fiducial")
template_bottom = make_binary_mask(cv2.equalizeHist(template_bottom), "fiducial")
template_left = make_binary_mask(cv2.equalizeHist(template_left), "fiducial")
template_right = make_binary_mask(cv2.equalizeHist(template_right), "fiducial")


# plot the templates
plt.figure(figsize=(10, 8))
plt.subplot(2, 2, 1)
plt.imshow(template_top, cmap='gray')
plt.title('Template Top')
plt.subplot(2, 2, 2)
plt.imshow(template_bottom, cmap='gray')
plt.title('Template Bottom')
plt.subplot(2, 2, 3)
plt.imshow(template_left, cmap='gray')
plt.title('Template Left')
plt.subplot(2, 2, 4)
plt.imshow(template_right, cmap='gray')
plt.title('Template Right')
plt.tight_layout()
plt.show()


for image_name in image_list:
    print(f"Processing {image_name}...")
    image_path = os.path.join(in_dir, image_name)
    out_img_path = os.path.join(out_dir, image_name).replace('.', '_br.')
    check_img_path = os.path.join(out_dir, image_name).replace('.', '_br_check.')
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Image not loaded properly")
    # binarise the image
    img = make_binary_mask(img, "image")
    h_img, w_img = img.shape
    # test_img = cv2.GaussianBlur(img, (5,5), 0)
    img_eq = cv2.equalizeHist(img)
    all_points = []
    for template in [template_top, template_bottom, template_left, template_right]:
        h_temp, w_temp = template.shape
        # Template matching
        res = cv2.matchTemplate(img_eq, template, cv2.TM_CCOEFF_NORMED)
        loc = np.where(res >= 0.55)
        points = [(int(x + w_temp/2), int(y + h_temp/2)) for (x, y) in zip(loc[1], loc[0])]
        if len(points) > 0:
            all_points.append(points)
        #  make unique points from all modes
    unique_points = set()
    for points_list in all_points:
        for pt in points_list:
            unique_points.add(pt)
    corrected_points = list(unique_points)
    if not corrected_points:
        print(f"No fiducial matches found for {image_name}, skipping.")
        continue
    pts = np.array(corrected_points, dtype=int).reshape(-1, 2)
    if pts.shape[0] < 4:
        print(f"Only {pts.shape[0]} fiducial match(es) found for {image_name}, skipping.")
        continue
    print("Y range:", np.min(pts[:,1]), np.max(pts[:,1]))
    print("X range:", np.min(pts[:,0]), np.max(pts[:,0]))
    # --- Identify 4 fiducials ---
    top = pts[np.argmin(pts[:, 1])]
    bottom = pts[np.argmax(pts[:, 1])]
    left = pts[np.argmin(pts[:, 0])]
    right = pts[np.argmax(pts[:, 0])]
    # Adaptive margin from template size (NOT hardcoded)
    w_temp_avg = np.min([template_top.shape[1], template_bottom.shape[1], template_left.shape[1], template_right.shape[1]])
    h_temp_avg = np.min([template_top.shape[0], template_bottom.shape[0], template_left.shape[0], template_right.shape[0]])
    margin_x = w_temp_avg // 2
    margin_y = h_temp_avg // 2
    # Crop bounds
    xmin = max(0, int(left[0] + margin_x))
    xmax = min(w_img, int(right[0] - margin_x))
    ymin = max(0, int(top[1] + margin_y))
    ymax = min(h_img, int(bottom[1] - margin_y))
    if xmin >= xmax or ymin >= ymax:
        print(f"Invalid crop bounds for {image_name}: x=({xmin}, {xmax}), y=({ymin}, {ymax}), skipping.")
        continue
    # for check create a image with detected points and crop area
    check_img = img.copy()
    check_img[ymin:ymax, xmin:xmax] = 255
    cv2.imwrite(check_img_path, check_img)
    # save the cropped image
    # read the original image as color to save the cropped image in color
    img_color = cv2.imread(image_path)
    img_color_cropped = img_color[ymin:ymax, xmin:xmax]
    cv2.imwrite(out_img_path, img_color_cropped)
    print(f"Cropped image saved to {out_img_path}")


