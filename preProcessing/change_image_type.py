# date: 16-02-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to chnage the file type of the images from tif to
#              PGM or PPM so that it can be used in VisualSFM software.
#              The VisualSFM needs file in JPEG or PPM or PGM format,
#              not using JPEG as it was comppersing the file
#              PGM: Portable GrayMap
#              PPM: Portable PixMap
#              PNM: Portable AnyMap (include both PGM and PPM)


import os

from osgeo import gdal
from PIL import Image
from pillow_heif import register_heif_opener


# Disable auxiliary metadata files
gdal.SetConfigOption("GDAL_PAM_ENABLED", "NO")
# Register HEIF opener with Pillow
register_heif_opener()

# #  define the sub-folder name which can change
# sub_folder_name = '1951 5129'
# # define the input his image paths
# his_img_path = 'D:\\datasets\\wales_gov\\penarth_head_to_cold_knap\\'
# # define the output his image paths
# his_img_out_path = 'D:\\datasets\\wales_gov\\penarth_head_to_cold_knap_jpeg\\'

#  define the sub-folder name which can change
sub_folder_name = 'my_iphone_camera_1'
# define the input his image paths
his_img_path = 'D:\\datasets\\sample_for_sfm\\'
# define the output his image paths
his_img_out_path = his_img_path


def change_from_tif(his_file: str, output_path: str) -> None:
    '''
    function to change the file type from tif to pnm (pgm or ppm)

    Args:
        his_file (str): the input his image file path
        output_path (str): the output path to save the changed file
        Returns: None
    '''
    # opening the dataset with gdal
    dataset = gdal.Open(his_file)
    #  checking if dataset exist or not
    if dataset is None:
        print(f'failed to open {his_file}')
        return
    # detect number of bands
    bands = dataset.RasterCount
    if bands == 1:
        ext = ".pgm"
    elif bands == 3:
        ext = ".ppm"
    else:
        print(f"Unsupported band count: {bands} in {his_file}")
        return
    # define the output pnm file name
    output_pnm = output_path + his_file.split('\\')[-1].split('.')[0] + ext
    # get the jepg driver
    driver = gdal.GetDriverByName('PNM')
    # change the file type
    out_ds = driver.CreateCopy(output_pnm, dataset)
    # save the file by closing it
    out_ds = None
    print(f'changed {his_file} to {output_pnm}')


def convert_heic_to_pnm(his_file: str, output_path: str) -> None:
    """
    Convert a HEIC file to PNM format
    Args:
        his_file (str): the input HEIC file path
        output_path (str): the output path to save the changed file
        Returns: None
    """
    # Open and convert
    img = Image.open(his_file)
    # define the output pnm file name
    output_pnm = output_path + his_file.split('\\')[-1].split('.')[0] + '.ppm'
    img.save(output_pnm, 'PPM')  # PPM is a PNM format variant
    print(f"Converted {his_file} to {output_pnm}")


#  create a list of all the files in the folder including sub-folder
his_file_list = []
for path, subdirs, files in os.walk(his_img_path + sub_folder_name):
    for name in files:
        his_file_list.append(os.path.join(path, name))

print(f'total {len(his_file_list)} files found in the folder')

# exit if there is no file in the folder
if len(his_file_list) == 0:
    exit()


#  looping over all the files to change the file type
for his_file in his_file_list:
    print(his_file)
    # define the output_path
    output_path = his_file.replace(his_file.split('\\')[-1], '').replace(
                    his_img_path + sub_folder_name, his_img_out_path +
                    sub_folder_name)
    # create the output path along with sub_paths if not exists
    if not os.path.exists(output_path):
        print(f'creating the {output_path}')
        os.makedirs(output_path)
    input_file_type = his_file.split('.')[-1].lower()
    if input_file_type == 'tif' or input_file_type == 'tiff':
        print("file type is tif, changing to pnm")
        change_from_tif(his_file, output_path)
    elif input_file_type == 'heic':
        print("file type is heic, changing to pnm")
        convert_heic_to_pnm(his_file, output_path)
    else:
        print(f"Unsupported file type: {input_file_type} in {his_file}")

