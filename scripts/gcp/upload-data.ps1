param(
    [Parameter(Mandatory=$true)][string]$GcpProjectId,
    [Parameter(Mandatory=$true)][string]$GcpRegion,
    [Parameter(Mandatory=$true)][string]$GcpStagingBucket,
    [Parameter(Mandatory=$true)][string]$ManifestPath
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path -LiteralPath $ManifestPath)) {
    throw "Manifest path does not exist: $ManifestPath"
}

Write-Host "Authenticating and configuring GCP Project: $GcpProjectId ($GcpRegion)..."
gcloud config set project $GcpProjectId

Write-Host "Ensuring BigQuery dataset uninews exists..."
bq --location=$GcpRegion mk --dataset "${GcpProjectId}:uninews" 2>$null

Write-Host "Ensuring GCS staging bucket exists: gs://$GcpStagingBucket..."
gcloud storage buckets create "gs://$GcpStagingBucket" --location=$GcpRegion --uniform-bucket-level-access 2>$null

Write-Host "Uploading batch using analytics module..."
python -m analytics upload --manifest $ManifestPath --project $GcpProjectId --dataset uninews --bucket $GcpStagingBucket --location $GcpRegion

Write-Host "Batch upload completed successfully."
