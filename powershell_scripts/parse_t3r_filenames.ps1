# ParseT3RFiles.ps1

Add-Type -AssemblyName System.Windows.Forms

# Function to browse for a folder
function Get-FolderPath {
    param(
        [string]$Description = "Select a folder",
        [string]$InitialDirectory = "C:\New PION Data"
    )
    
    $folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
    $folderBrowser.Description = $Description
    $folderBrowser.SelectedPath = $InitialDirectory
    $folderBrowser.ShowNewFolderButton = $false
    
    if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $folderBrowser.SelectedPath
    } else {
        return $null
    }
}

# Function to show MessageBox on top
function Show-TopMessageBox {
    param(
        [string]$Message,
        [string]$Title,
        [System.Windows.Forms.MessageBoxButtons]$Buttons = [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]$Icon = [System.Windows.Forms.MessageBoxIcon]::Information
    )
    
    # Create a hidden form to act as owner and ensure TopMost
    $form = New-Object System.Windows.Forms.Form
    $form.TopMost = $true
    $form.StartPosition = 'Manual'
    $form.Location = New-Object System.Drawing.Point(-2000, -2000)
    $form.Size = New-Object System.Drawing.Size(1, 1)
    $form.ShowInTaskbar = $false
    $form.Show()
    
    $result = [System.Windows.Forms.MessageBox]::Show($form, $Message, $Title, $Buttons, $Icon)
    
    $form.Close()
    $form.Dispose()
    
    return $result
}

# Get folder from user
$selectedFolder = Get-FolderPath -Description "Select folder containing .t3r files" -InitialDirectory "C:\New PION Data"

if ([string]::IsNullOrEmpty($selectedFolder)) {
    Show-TopMessageBox -Message "No folder selected. Operation cancelled." -Title "Cancelled" -Icon Warning
    exit
}

# Find all .t3r files
$t3rFiles = Get-ChildItem -Path $selectedFolder -Filter "*.t3r" -File

if ($t3rFiles.Count -eq 0) {
    Show-TopMessageBox -Message "No .t3r files found in the selected folder." -Title "No Files Found" -Icon Warning
    exit
}

# Create array to hold parsed data
$parsedData = @()
$skippedFiles = @()

# Parse each filename
foreach ($file in $t3rFiles) {
    # Get filename without extension
    $baseName = $file.BaseName
    
    # Split by underscore (limit to 3 parts in case assay name has underscores)
    $parts = $baseName -split '_', 3
    
    if ($parts.Count -eq 3) {
        $parsedData += [PSCustomObject]@{
            date = $parts[0]
            sample_id = $parts[1]
            assay_name = $parts[2]
        }
    } else {
        # Track files that don't match the pattern
        $skippedFiles += $file.Name
        Write-Warning "File does not match pattern: $($file.Name)"
    }
}

# Check if we have any parsed data
if ($parsedData.Count -eq 0) {
    Show-TopMessageBox -Message "No files matched the expected naming pattern (DATE_SAMPLE_ID_ASSAY_NAME)." -Title "No Valid Files" -Icon Warning
    exit
}

# Create output CSV filename
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$csvFileName = "parsed_files_$timestamp.csv"
$csvPath = Join-Path -Path $selectedFolder -ChildPath $csvFileName

try {
    # Export to CSV
    $parsedData | Export-Csv -Path $csvPath -NoTypeInformation
    
    # Build success message
    $successMessage = "Successfully processed $($parsedData.Count) file(s).`n`nCSV saved to:`n$csvPath"
    
    if ($skippedFiles.Count -gt 0) {
        $successMessage += "`n`nSkipped $($skippedFiles.Count) file(s) that didn't match the pattern."
    }
    
    # Show success message
    Show-TopMessageBox -Message $successMessage -Title "Success" -Icon Information
    
} catch {
    Show-TopMessageBox -Message "Error creating CSV file:`n`n$($_.Exception.Message)" -Title "Error" -Icon Error
}