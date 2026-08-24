# define the project name
$Project = "1944_4001"

# define the log file path with timestamp
$LogFile = "D:/OpenDroneMap/$Project/${Project}_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"


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
