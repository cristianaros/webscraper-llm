param(
    [Parameter(Mandatory=$true)][string]$ProjectId,
    [Parameter(Mandatory=$true)][string]$Region,
    [Parameter(Mandatory=$true)][string]$ImageDigest,
    [Parameter(Mandatory=$true)][string]$SqlInstanceConnectionName,
    [Parameter(Mandatory=$true)][string]$MediaBucket,
    [Parameter(Mandatory=$true)][string]$WebServiceAccount,
    [Parameter(Mandatory=$true)][string]$DatabaseSecretVersion,
    [Parameter(Mandatory=$true)][string]$AdminSecretVersion,
    [Parameter(Mandatory=$true)][string]$CollectorSecretVersion
)

$ErrorActionPreference = 'Stop'

Write-Host "Deploying UniNews Web to Cloud Run..."
gcloud run deploy uninews-web --project=$ProjectId --region=$Region `
    --image=$ImageDigest --port=8080 --max-instances=1 --concurrency=20 --timeout=60 `
    --service-account=$WebServiceAccount --add-cloudsql-instances=$SqlInstanceConnectionName `
    --set-secrets="DATABASE_URL=$DatabaseSecretVersion,ADMIN_TOKEN=$AdminSecretVersion,COLLECTOR_TOKEN=$CollectorSecretVersion" `
    --set-env-vars="APP_ENV=production,MEDIA_BACKEND=gcs,GCS_MEDIA_BUCKET=$MediaBucket,RAG_ENABLED=false" `
    --allow-unauthenticated

Write-Host "Deployment completed."
