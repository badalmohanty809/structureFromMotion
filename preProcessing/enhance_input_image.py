# date: 02-03-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to enhance the input image by

import os, sys
import numpy as np
import cv2
from skimage import exposure
from PIL import Image
import matplotlib.pyplot as plt

# set the OpenCV log level to error to suppress warnings
# cv2.utils.logging.setLogLevel(cv2.utils.logging.LOG_LEVEL_ERROR)


def generate_histogram(image: np.ndarray, out_path: str, type: str) -> None:
    '''
    function to generate histogram and cdf of the input image and save
    the plot

    image: input image as numpy array
    out_path: path to save the histogram plot
    return: None
    '''
    # For color images, convert to grayscale for histogram
    if len(image.shape) == 3:
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Determine bit depth from dtype (e.g., uint8 -> 8 bits)
    bit_depth = image.dtype.itemsize * 8
    # Number of possible intensity levels
    num_bins = 2 ** bit_depth
    # Histogram range is [0, max_value + 1]
    hist_range = [0, num_bins]
    # Calculate histogram with num_bins bins over range [0, num_bins]
    hist,_ = np.histogram(image.flatten(), bins = num_bins, range = hist_range)
    # Compute cumulative sum of histogram values
    # (Cumulative Distribution Function)
    cdf = hist.cumsum()
    # Normalize CDF to match histogram maximum for visualization
    cdf_normalized = cdf * float(hist.max()) / cdf.max()
    # clear the current figure
    plt.clf()
    # Plot the normalized CDF as a blue line
    plt.plot(cdf_normalized, color = 'b')
    # Plot histogram with num_bins bins as red bars
    plt.hist(image.flatten(), bins = num_bins, range = hist_range,
             color = 'r')
    # Set x-axis limits to [0, num_bins]
    plt.xlim([0,num_bins])
    # add axis names
    plt.xlabel('Pixel Intensity')
    plt.ylabel('Frequency')
    # add title
    plt.title(f'Histogram and CDF of the {type} Image')
    # Add legend identifying CDF and histogram lines
    plt.legend(('cdf','histogram'), loc = 'upper left')
    # Save the plot to the specified output path
    plt.savefig(out_path)
    # Display the plot
    # plt.show()

def save_image(image: np.ndarray, out_path: str, type: str) -> None:
    '''
    function to save the input image as tif file

    image: input image as numpy array
    out_path: path to save the image
    return: None
    '''
    # save the image using OpenCV
    cv2.imwrite(out_path, image)
    print(f"\t{type} image saved at: {out_path}")

def img_linear_stretch(img_gray_clahe: np.ndarray) -> np.ndarray:
    '''
    function to rescale the pixel values of the input image using linear
    stretching based on the 1st and 99th percentiles to avoid influence
    of outliers

    img_gray_clahe: input image as numpy array
    return: rescaled image as numpy array
    '''
    min_val = np.uint8(np.floor(np.percentile(img_gray_clahe, 1)))
    max_val = np.uint8(np.ceil(np.percentile(img_gray_clahe, 99)))
    img_rescale = exposure.rescale_intensity(img_gray_clahe, in_range=(min_val, max_val))
    return img_rescale

def clahe_equalize_image(img: np.ndarray, clipLimit=2.0,
                         tileGridSize=(8,8)) -> np.ndarray:
    '''
    Contrast Limited Adaptive Histogram Equalization
    Works for both grayscale and color images

    img_gray: input image (despite name, can be color or grayscale)
    return: enhanced image with same number of bands as input
    '''
    # Check if image is color or grayscale
    clahe = cv2.createCLAHE(clipLimit=clipLimit, tileGridSize=tileGridSize)
#
    if len(img.shape) == 3:
        # Color image - convert to LAB, apply CLAHE to L channel
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        # apply CLAHE to L channel
        l_clahe = clahe.apply(l)
        # rescale L channel using percentiles to avoid influence of
        # outliers
        l_rescale = img_linear_stretch(l_clahe)
        # Merge back and convert to BGR
        lab_rescale = cv2.merge([l_rescale, a, b])
        img_rescale = cv2.cvtColor(lab_rescale, cv2.COLOR_LAB2BGR)
    else:
        # Grayscale image
        img_gray_clahe = clahe.apply(img)
        # rescale using percentiles to avoid influence of outliers
        img_rescale = img_linear_stretch(img_gray_clahe)
#
    return img_rescale

def save_image_with_dpi(input_path: str, image: np.ndarray, out_path: str, type: str):
    '''
    Save image preserving DPI from input image
    '''
    # read original DPI
    with Image.open(input_path) as img_in:
        dpi = img_in.info.get('dpi', (300, 300))  # fallback if missing
    # convert OpenCV (BGR) to PIL (RGB)
    if len(image.shape) == 3:
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    else:
        image_rgb = image
    pil_img = Image.fromarray(image_rgb)
    # save with original DPI
    pil_img.save(out_path, dpi=dpi)
    print(f"\t{type} Image saved with preserved DPI at: {out_path}")


br_file_path = sys.argv[1]
hist_eq_file_path=sys.argv[2]

print(f"Processing image: {br_file_path}")

# read the image using OpenCV
image = cv2.imread(br_file_path, cv2.IMREAD_UNCHANGED)

# check if the image is read properly
assert image is not None, "file could not be read"

# check if the image is grayscale or color
# if the image is not greyscale the the codes to enhance the
# image will have to change as the below functions work with
# grey scale images only
if len(image.shape) == 2:  # Grayscale image
    print("The image is grayscale.")
elif len(image.shape) == 3:  # Color image
    print("The image is color.")
elif len(image.shape) == 4:  # Multichannel image (e.g., RGBA)
    print("The image is multichannel (e.g., RGBA).")
    image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

# check the original image
# org_hist_file_path = hist_eq_file_path.replace('.tif', '_original_histogram.png').replace('.tiff', '_original_histogram.png')
org_hist_file_path = hist_eq_file_path.split('.tif')[0] + '_original_histogram.png'
generate_histogram(image, org_hist_file_path, type='original')

# option 3: apply CLAHE as per HSFM paper
# only if image has no border
clahe_hsfm_image = clahe_equalize_image(image)

# save the clahe hsfm enhanced image
# clahe_hsfm_hist_file_path = hist_eq_file_path.replace('.tif', '_clahe_histogram.png').replace('.tiff', '_clahe_histogram.png')
clahe_hsfm_hist_file_path = hist_eq_file_path.split('.tif')[0] + '_clahe_histogram.png'
generate_histogram(clahe_hsfm_image, clahe_hsfm_hist_file_path, type='clahe_hsfm')

save_image_with_dpi(br_file_path, clahe_hsfm_image, hist_eq_file_path, type='clahe_hsfm')
print(f"\tCLAHE enhanced image saved at: {hist_eq_file_path}")
