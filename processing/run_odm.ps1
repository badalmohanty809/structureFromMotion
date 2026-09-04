# date: 22-08-2026
# author: MohantyB
# topic: historic aerial image processing
# description: script to tun the ODM via docker

# define the project name
$Project = "9100_1991_Geonex_set_4"


Write-Host "Starting ODM processing for project: $Project"


#  ------------------------------------ creat folders and copy files for current run
#  get the current run name based on the existing runs in the dataset folder
$ExistingRuns = Get-ChildItem "D:/OpenDroneMap/$Project/dataset" -Directory -Filter "run_*"

if ($ExistingRuns.Count -eq 0) {
    $RunNumber = 1
} else {
    $RunNumber = (($ExistingRuns.Name |
        ForEach-Object { $_ -replace 'run_','' } |
        Measure-Object -Maximum).Maximum) + 1
}

$RunName = "run_$RunNumber"

Write-Host "Current run is: $RunName"
$RunFolder = "D:/OpenDroneMap/$Project/dataset/$RunName"
$output_copy_folder = "D:/OpenDroneMap/$Project/dataset/$RunName/outputs"

# Create run folder
New-Item -ItemType Directory -Force -Path $RunFolder | Out-Null

# copy images to run folder
robocopy "D:\OpenDroneMap\$Project\dataset\images" "$RunFolder\images"

# copy txt files to run folder
Copy-Item "D:\OpenDroneMap\$Project\dataset\${Project}_geo.txt" "$RunFolder\${Project}_geo.txt"
Copy-Item "D:\OpenDroneMap\$Project\dataset\${Project}_gcp_cords_ODM.txt" "$RunFolder\${Project}_gcp_cords_ODM.txt"

# ------------------------------------ running the ODM processing for the current run
# define the log file path with timestamp
$TimeStamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogFile = "D:/OpenDroneMap/$Project/${Project}_${RunName}_log_$TimeStamp.log"

#  define the variables
$matcher_type = "flann" # flann or bruteforce (better than FLANN but takes way more time)
$feature_type = "sift" # dspsift or sift
$feature_quality = "ultra" # ultra | high | medium | low | lowest
$min_num_features = 90000
$pc_quality = "ultra" # ultra | high | medium | low | lowest
$pc_filter = 0 # no cleaning of cloud points - as doing later in pdal
# $dem_gapfill_steps = 0
$orthophoto_resolution = 100 # in cm, too fine resolution take up too much RAM space and time, so keep it at 100cm for now
# $dem_resolution = 25 # in cm
$geo_file_path = "/dataset/${RunName}/${Project}_geo.txt" # relative path to dataset folder in docker container
$gcp_file_path = "/dataset/${RunName}/${Project}_gcp_cords_ODM.txt" # relative path to dataset folder in docker container

#  add these variables to the log file
"Run Name: $RunName" | Out-File -Append $LogFile
"Matcher Type: $matcher_type" | Out-File -Append $LogFile
"Feature Type: $feature_type" | Out-File -Append $LogFile
"Feature Quality: $feature_quality" | Out-File -Append $LogFile
"Minimum Number of Features: $min_num_features" | Out-File -Append $LogFile
"Point Cloud Quality: $pc_quality" | Out-File -Append $LogFile
"Point Cloud Filter: $pc_filter" | Out-File -Append $LogFile
# "DEM Gap Fill Steps: $dem_gapfill_steps" | Out-File -Append $LogFile
"Orthophoto Resolution: $orthophoto_resolution" | Out-File -Append $LogFile
# "DEM Resolution: $dem_resolution" | Out-File -Append $LogFile
"Geo File Path: $geo_file_path" | Out-File -Append $LogFile
"GCP File Path: $gcp_file_path" | Out-File -Append $LogFile

if (-not (Test-Path "$RunFolder\images")) {
    # write it to log file and exit the script
    "Images junction was not created successfully." | Out-File -Append $LogFile
    exit 1
}

"Starting OpenDroneMap processing for project: $Project and run: $RunName" | Tee-Object -FilePath $LogFile -Append

$Start = Get-Date

docker run -ti --rm `
-v D:/OpenDroneMap/$Project/dataset:/dataset `
--gpus all `
opendronemap/odm:gpu `
--project-path /dataset $RunName `
--gcp ${gcp_file_path} `
--geo ${geo_file_path} `
--matcher-type $matcher_type `
--feature-type $feature_type `
--feature-quality $feature_quality `
--min-num-features $min_num_features `
--ignore-gsd `
--pc-quality $pc_quality `
--pc-filter $pc_filter `
--orthophoto-resolution $orthophoto_resolution `
--use-3dmesh `
2>&1 | Tee-Object -FilePath $LogFile -Append

# --dem-gapfill-steps $dem_gapfill_steps `
# --dsm `
# --dtm `
# --dem-resolution $dem_resolution `
# --rerun-from openmvs `
# --dem-resolution 50 `

$End = Get-Date
$Duration = $End - $Start

"Processing time: $($Duration.ToString())" | Tee-Object -FilePath $LogFile -Append

Write-Host "Log saved to: $LogFile"


# ------------------------------------ write QA file for the project

$qa_file_path = "D:/OpenDroneMap/$Project/${Project}_${RunName}_QA_$TimeStamp.txt"

Write-Host "creating QA file"

"The stats of the runs are:" | Out-File $qa_file_path

$stats_json_path = "D:/OpenDroneMap/$Project/dataset/${RunName}/opensfm/stats/stats.json"
$gcp_json_path = "D:/OpenDroneMap/$Project/dataset/${RunName}/opensfm/stats/ground_control_points.json"

if (-Not (Test-Path $stats_json_path))
{
    Write-Host "Stats JSON file not found: $stats_json_path"
    "stats file not found at: $stats_json_path" | Out-File -Append $qa_file_path
}else{
    Write-Host "Stats JSON file found: $stats_json_path"
    "stats file path: $stats_json_path" | Out-File -Append $qa_file_path
    $stats_json = Get-Content $stats_json_path -Raw | ConvertFrom-Json
    $reproj_err_px = $stats_json.reconstruction_statistics.reprojection_error_pixels
    $in_shot_count = $stats_json.reconstruction_statistics.initial_shots_count
    $re_shot_count = $stats_json.reconstruction_statistics.reconstructed_shots_count
    $gcp_err_avg = $stats_json.gcp_errors.average_error
    $gcp_err_x = $stats_json.gcp_errors.error.x
    $gcp_err_y = $stats_json.gcp_errors.error.y
    $gcp_err_z = $stats_json.gcp_errors.error.z
    $gcp_error_ce90 = $stats_json.gcp_errors.ce90
    $gcp_error_le90 = $stats_json.gcp_errors.le90
    "total image present: $in_shot_count" | Out-File -Append $qa_file_path
    "total image reconstructed: $re_shot_count" | Out-File -Append $qa_file_path
    "reprojection error (px): $reproj_err_px" | Out-File -Append $qa_file_path
    "average GCP error (m): $gcp_err_avg" | Out-File -Append $qa_file_path
    "GCP error X (m): $gcp_err_x" | Out-File -Append $qa_file_path
    "GCP error Y (m): $gcp_err_y" | Out-File -Append $qa_file_path
    "GCP error Z (m): $gcp_err_z" | Out-File -Append $qa_file_path
    "GCP error CE90 (m): $gcp_error_ce90" | Out-File -Append $qa_file_path
    "GCP error LE90 (m): $gcp_error_le90" | Out-File -Append $qa_file_path
}

if (-Not (Test-Path $gcp_json_path))
{
    Write-Host "GCP JSON file not found: $gcp_json_path"
    "GCP file not found at: $gcp_json_path" | Out-File -Append $qa_file_path
}else{
    Write-Host "GCP JSON file found: $gcp_json_path"
    "GCP file path: $gcp_json_path" | Out-File -Append $qa_file_path
    $gcp_json = Get-Content $gcp_json_path -Raw | ConvertFrom-Json
    "Individual GCP errors (m):" | Out-File -Append $qa_file_path
    "GCP ID, GCP Error X (m), GCP Error Y (m), GCP Error Z (m)" | Out-File -Append $qa_file_path
    $gcp_json | ForEach-Object {"$($_.id),$($_.error[0]),$($_.error[1]),$($_.error[2])"} | Add-Content $qa_file_path
}

Write-Host "QA file saved to: $qa_file_path"


# ------------------------------------ copy the required outputs to another folder for further processing


$laz_file_in_path = "$RunFolder/odm_georeferencing/odm_georeferenced_model.laz"
$orthophoto_file_in_path = "$RunFolder/odm_orthophoto/odm_orthophoto.tif"

$laz_file_out_path = "$output_copy_folder/${Project}_${RunName}_odm_georeferenced_model.laz"
$orthophoto_file_out_path = "$output_copy_folder/${Project}_${RunName}_odm_orthophoto.tif"


#  chcek if the files exist before copying
if (Test-Path $laz_file_in_path)
{
    if (-Not (Test-Path $output_copy_folder))
    {
        New-Item -ItemType Directory -Path $output_copy_folder
    }
    Copy-Item -Path $laz_file_in_path -Destination $laz_file_out_path
    Write-Host "Copied LAZ file to: $laz_file_out_path"
}else{
    Write-Host "LAZ file not found at: $laz_file_in_path"
}

if (Test-Path $orthophoto_file_in_path)
{
    if (-Not (Test-Path $output_copy_folder))
    {
        New-Item -ItemType Directory -Path $output_copy_folder
    }
    Copy-Item -Path $orthophoto_file_in_path -Destination $orthophoto_file_out_path
    Write-Host "Copied Orthophoto file to: $orthophoto_file_out_path"
}else{
    Write-Host "Orthophoto file not found at: $orthophoto_file_in_path"
}
