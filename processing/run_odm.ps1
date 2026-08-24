# define the project name
$Project = "1944_4001"

# define the log file path with timestamp
$TimeStamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$LogFile = "D:/OpenDroneMap/$Project/${Project}_log_$TimeStamp.log"


#  define the variables
$matcher_type = "bruteforce"
$feature_type = "sift"
$feature_quality = "ultra"
$min_num_features = 90000
$pc_quality = "ultra"
$pc_filter = 1
# $dem_gapfill_steps = 0
$orthophoto_resolution = 10 # in cm
# $dem_resolution = 25 # in cm
$geo_file_path = "/dataset/project/${Project}_geo.txt" # relative path to dataset folder in docker container
$gcp_file_path = "/dataset/project/${Project}_gcp_cords_ODM_CoP.txt" # relative path to dataset folder in docker container


#  add these variables to the log file
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


"Starting OpenDroneMap processing for project: $Project" | Tee-Object -FilePath $LogFile -Append

$Start = Get-Date

docker run -ti --rm `
-v D:/OpenDroneMap/$Project/dataset:/dataset `
--gpus all `
opendronemap/odm:gpu `
--project-path /dataset project `
--geo ${geo_file_path} `
--gcp ${gcp_file_path} `
--matcher-type $matcher_type `
--feature-type $feature_type `
--feature-quality $feature_quality `
--min-num-features $min_num_features `
--ignore-gsd `
--pc-quality $pc_quality `
--pc-filter $pc_filter `
--pc-rectify `
--orthophoto-resolution $orthophoto_resolution `
2>&1 | Tee-Object -FilePath $LogFile -Append

# --dem-gapfill-steps $dem_gapfill_steps `
# --dsm `
# --dtm `
# --dem-resolution $dem_resolution `

$End = Get-Date
$Duration = $End - $Start

"Processing time: $($Duration.ToString())" | Tee-Object -FilePath $LogFile -Append

Write-Host "Log saved to: $LogFile"


#  -------------- write QA file for the project

$qa_file_path = "D:/OpenDroneMap/$Project/${Project}_QA_$TimeStamp.txt"

if (Test-Path $qa_file_path) {
    Write-Host "File exists"
    "The stats of the runs are:" | Out-File $qa_file_path
}

$stats_json_path = "D:/OpenDroneMap/$Project/dataset/project/opensfm/stats/stats.json"
$gcp_json_path = "D:/OpenDroneMap/$Project/dataset/project/opensfm/stats/ground_control_points.json"

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
