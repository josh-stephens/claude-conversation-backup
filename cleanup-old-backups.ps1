# Cleanup Old JSONL Backups
# These have been converted to Markdown and are redundant

$backupDir = "C:\Users\josh\Documents\Mine\Claude Code Conversation Backups (Automated)"
$backupFolders = Get-ChildItem "$backupDir\backup_*" -Directory

Write-Host "Found $($backupFolders.Count) old backup folders to clean up" -ForegroundColor Yellow

# Archive important metadata before deletion
$archiveInfo = @()
foreach ($folder in $backupFolders) {
    $info = @{
        Name = $folder.Name
        Date = $folder.LastWriteTime
        Files = (Get-ChildItem $folder -Recurse -File).Count
    }
    $archiveInfo += $info
}

# Save cleanup record
$archiveInfo | ConvertTo-Json | Out-File "$backupDir\cleanup-archive-$(Get-Date -Format 'yyyy-MM-dd').json"

# Confirm before deletion
$totalSize = [math]::Round((Get-ChildItem $backupDir\backup_* -Recurse -File | Measure-Object -Property Length -Sum).Sum/1MB, 2)
Write-Host "These folders contain $totalSize MB of duplicate JSONL files" -ForegroundColor Cyan
Write-Host "Markdown conversions are already complete in the Devices folder" -ForegroundColor Green

$response = Read-Host "Delete all old backup folders? (yes/no)"
if ($response -eq "yes") {
    foreach ($folder in $backupFolders) {
        Write-Host "Removing $($folder.Name)..." -ForegroundColor Gray
        Remove-Item $folder.FullName -Recurse -Force
    }
    Write-Host "Cleanup complete! Freed $totalSize MB" -ForegroundColor Green
} else {
    Write-Host "Cleanup cancelled" -ForegroundColor Yellow
}