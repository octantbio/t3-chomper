# CreateExperimentFolders.ps1

Add-Type -AssemblyName Microsoft.VisualBasic

# Show input dialog box
$ExperimentID = [Microsoft.VisualBasic.Interaction]::InputBox(
    "Enter the Experiment ID (ST3-<id>):", 
    "Create Experiment Folder", 
    ""
)

# Check if user cancelled or entered nothing
if ([string]::IsNullOrWhiteSpace($ExperimentID)) {
    [System.Windows.Forms.MessageBox]::Show(
        "No Experiment ID provided. Operation cancelled.",
        "Cancelled",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}

# Define the base directory
$baseDirectory = "C:\New PION Data"

# Create the full path for the experiment folder
$experimentPath = Join-Path -Path $baseDirectory -ChildPath $ExperimentID

# Check if the experiment folder already exists
if (Test-Path -Path $experimentPath) {
    Add-Type -AssemblyName System.Windows.Forms
    $result = [System.Windows.Forms.MessageBox]::Show(
        "Folder '$experimentPath' already exists!`n`nDo you want to continue and create subfolders?",
        "Folder Exists",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    
    if ($result -eq [System.Windows.Forms.DialogResult]::No) {
        [System.Windows.Forms.MessageBox]::Show(
            "Operation cancelled.",
            "Cancelled",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Information
        )
        exit
    }
} else {
    # Create the experiment folder
    New-Item -Path $experimentPath -ItemType Directory -Force | Out-Null
    Write-Host "Created experiment folder: $experimentPath" -ForegroundColor Green
}

# Define the subfolder names
$subfolders = @("Unprocessed", "QC Fail", "For logP", "For UV-metric pKa", "For pH-metric pKa","Input files")

# Create each subfolder
foreach ($folder in $subfolders) {
    $subfolderPath = Join-Path -Path $experimentPath -ChildPath $folder
    
    if (-not (Test-Path -Path $subfolderPath)) {
        New-Item -Path $subfolderPath -ItemType Directory -Force | Out-Null
        Write-Host "Created subfolder: $folder" -ForegroundColor Cyan
    } else {
        Write-Host "Subfolder already exists: $folder" -ForegroundColor Yellow
    }
}

# Show success message
Add-Type -AssemblyName System.Windows.Forms
[System.Windows.Forms.MessageBox]::Show(
    "Folder structure created successfully!`n`nLocation: $experimentPath",
    "Success",
    [System.Windows.Forms.MessageBoxButtons]::OK,
    [System.Windows.Forms.MessageBoxIcon]::Information
)

explorer.exe $experimentPath
