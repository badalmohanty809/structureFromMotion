# date: 02-03-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to remove the border from the input image

# =========================== NOT WORKING AS EXPECTED
# =========================== TODO: NEED ENTIRELY DIFFERENT LOGIC

# notes:
# 1. The idea here is to remove the border from the images.
#       I am thinking to detect the brider as a strip of black or almost
#       black line in horizontal and vertical direction.

# 2. There might be text on the image broder. So have to keep that in
#       mind while detecting the black strip.

# 3. for now, assuming the image has only one band

# 4. Why its not working as expected?
#       The logic is working for some images but not for all.
        # case 0: the code is working fine
        # case 1: The threshold of 70 is too less for some images and
        #         was removing part of the image after final step.
        #         So may be need to icrease it to 90 or > 95
        # case 2: The input image is not perfectly aligned and the
        #         broder is not perfectly horizontal or vertical.
        #         so, it is not removing broder with current logic.


#  examples of different cases:
# case 0:
# D:\datasets\wales_gov\penarth_head_to_cold_knap\1951 5129\71-79\76.tiff
# case 1:
# D:\datasets\wales_gov\penarth_head_to_cold_knap\1951 5129\71-79\77.tiff
# case 2:
# D:\datasets\wales_gov\penarth_head_to_cold_knap\1951 5129\81-121\94.tiff

import cv2
import numpy as np

# threshold for percentage of pixels with value 0 in a row or column to
# be considered as border
percentage_threshold = 70


def create_binary_image(input_image: np.ndarray) -> np.ndarray:
    '''
    function to create a binary image where pixels with value greater
    than the threshold are set to 255 and others are set to 0

    image: input image as numpy array
    threshold: threshold value to create the binary image
    return: binary image as numpy array
    '''
    #  find counts for each pixel value
    print("Finding the most repeated pixel value in the image...")
    DN_value, DN_counts = np.unique(input_image, return_counts=True)
    #  get the max value among the top 5 most repeated pixel values
    value_most_rep = max(DN_value[np.argsort(DN_counts)[-5:]])
    print(f"\tThe most repeated pixel value is {value_most_rep}"
          f" with count {DN_counts[np.argsort(DN_counts)[-1]]}")
    # create a binary image where pixels with value greater than the
    #   most repeated value are set to 255 and others are set to 0
    print(f"\tCreating a binary image using the most repeated pixel "
          f"value as threshold...")
    thresh_binary_image = np.where(input_image > value_most_rep, 255,
                                   0).astype(np.uint8)
    print("\tBinary image created.")
    return thresh_binary_image


def calculate_percentage_zero(thresh_binary_image: np.ndarray) -> tuple:
    '''
    function to calculate the percentage of pixels with value 0 in
    each row and column of the binary image

    thresh_binary_image: binary image as numpy array
    return: tuple of two lists, one for border rows and another for
            border columns
    '''
    # find broder rows
    print("Calculating percentage of pixels with value 0 in each row "
          f"and column...")
    border_rows = []
    rows_per_zero = []
    for row in range(thresh_binary_image.shape[0]):
        count_zero = np.sum(thresh_binary_image[row,:] == 0)
        percentage_zero = (count_zero / thresh_binary_image.shape[1]) * 100
        if percentage_zero > 0:
            border_rows.append(row)
            rows_per_zero.append(percentage_zero)
    # find broder columns
    border_cols = []
    cols_per_zero = []
    for col in range(thresh_binary_image.shape[1]):
        count_zero = np.sum(thresh_binary_image[:,col] == 0)
        percentage_zero = (count_zero / thresh_binary_image.shape[0]) * 100
        if percentage_zero > 0:
            border_cols.append(col)
            cols_per_zero.append(percentage_zero)
    # return the border rows and columns along with their percentage
    # of pixels with value 0
    print("\tPercentage of pixels with value 0 calculated for each row "
          "and column.")
    return border_rows, rows_per_zero, border_cols, cols_per_zero


def find_cropped_image(blank_image: np.ndarray) -> tuple:
    '''
    function to find the cropped image by finding the largest connected
    component in the blank image and cropping the original image using
    the coordinates of that component

    blank_image: binary image with borders as 0 and non-borders as 255
    return: tuple of coordinates (x, y, w, h) for the cropped region
    '''
    # find connected components
    print("Finding the largest connected component in the blank image")
    _, _, stats, _ = cv2.connectedComponentsWithStats(blank_image)
    # ignore label 0 (background)
    # pick component with max area
    largest = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
    x, y, w, h, area = stats[largest]
    crop = blank_image[y:y+h, x:x+w]
    print(f"\tLargest connected component found with area {area} and "
          f"coordinates (x={x}, y={y}, w={w}, h={h}).")
    return crop, x, y, w, h


# path for the text file which contains the list of input image paths
input_image_txt = ('C:\\Users\\c25045127\\OneDrive - Cardiff University\\'
                   'data_analysis\\image_list.txt')

# define the out path
out_dir = ('D:\\datasets\\image_preprocessing\\remove_border\\'
           'penarth_head_to_cold_knap\\1951_5129\\')


# read the input image paths from the text file and make a list
input_image_list = open(input_image_txt, 'r').read().splitlines()


# input_image_path = input_image_list[2] # logic working for this image

for input_image_path in input_image_list:
    print(f"Processing image: {input_image_path}")
    input_image_name = input_image_path.split('\\')[-1].split('.')[0]
    # read the image using OpenCV
    input_image = cv2.imread(input_image_path, cv2.IMREAD_UNCHANGED)
    # check if the image is read properly
    assert input_image is not None, "file could not be read"
    #
    # create a binary image where pixels with value greater than the most
    #   repeated value are set to 255 and others are set to
    thresh_binary_image = create_binary_image(input_image)
    # save the binary image
    binary_out_path = f"{out_dir}{input_image_name}_binary.png"
    cv2.imwrite(binary_out_path, thresh_binary_image)
    print(f"\tBinary image saved at: {binary_out_path}")
    #
    #  make a image with value 255 and the same shape as the input image
    blank_image = np.ones_like(input_image) * 255
    #
    border_rows, rows_per_zero, border_cols, cols_per_zero = calculate_percentage_zero(thresh_binary_image)
    #
    # for rows whose percentage is gt percentage_threshold,
    # set it as 0 in empty image
    print(f"adding row border to blank image")
    for row, perc in zip(border_rows, rows_per_zero):
        if perc > percentage_threshold:
            blank_image[row,:] = 0
    #
    print(f"row border added to blank image")
    #
    # for cols whose percentage is gt percentage_threshold,
    # set it as 0 in empty image
    print(f"adding column border to blank image")
    for col, perc in zip(border_cols, cols_per_zero):
        if perc > percentage_threshold:
            blank_image[:,col] = 0
    #
    print(f"column border added to blank image")
    #
    # save the blank image
    print(f"Saving the mask image with detected borders...")
    mask_out_path = f"{out_dir}{input_image_name}_mask.png"
    cv2.imwrite(mask_out_path, blank_image)
    print(f"\tMask image saved at: {mask_out_path}")
    #
    # crop the original image using the same coordinates
    print(f"Finding cropped image...")
    _, x, y, w, h = find_cropped_image(blank_image)
    cropped_image = input_image[y:y+h, x:x+w]
    #
    # save the cropped image
    cropped_out_path = f"{out_dir}{input_image_name}_cropped.png"
    cv2.imwrite(cropped_out_path, cropped_image)
    print(f"\tCropped image saved at: {cropped_out_path}")



#  in this, the 5th value gave the best broder.
#  so may be taking the max(to_5_val) will work better

# #  find counts for each pixel value
# DN_value, DN_counts = np.unique(input_image, return_counts=True)
# #  get the index of top 5 counts
# top_5_indices = np.argsort(DN_counts)[-5:]
# top_5_values = DN_value[top_5_indices]
# # DN_counts[top_5_indices]


# # for each top_5 value, creat a binary image and save it
# for val in top_5_values:
#     binary_image = np.where(input_image > val, 255, 0).astype(np.uint8)
#     index = top_5_values.tolist().index(val)
#     out_path = f"{out_dir}binary_{val}_{index}.png"
#     cv2.imwrite(out_path, binary_image)
