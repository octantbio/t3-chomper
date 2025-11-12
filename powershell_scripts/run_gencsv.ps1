# RunT3GenCSV.ps1

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$pionTopFolder = "C:\New PION Data"

# Function to browse for a CSV file
function Get-CSVFileName {
    param([string]$Title)
    
    $openFileDialog = New-Object System.Windows.Forms.OpenFileDialog
    $openFileDialog.Title = $Title
    $openFileDialog.Filter = "CSV files (*.csv)|*.csv"
    $openFileDialog.InitialDirectory = $pionTopFolder
	$openFileDialog.TopMost = $true
    
    if ($openFileDialog.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
        return $openFileDialog.FileName
    } else {
        return $null
    }
}

# Get --regi file
$regiFile = Get-CSVFileName -Title "Select CSV file for --regi"
if ([string]::IsNullOrEmpty($regiFile)) {
    [System.Windows.Forms.MessageBox]::Show(
        "No file selected for --regi. Operation cancelled.",
        "Cancelled",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}

# Get --pka file
$pkaFile = Get-CSVFileName -Title "Select CSV file for --pka"
if ([string]::IsNullOrEmpty($pkaFile)) {
    [System.Windows.Forms.MessageBox]::Show(
        "No file selected for --pka. Operation cancelled.",
        "Cancelled",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}

# Get --filter-file (optional)
$filterPrompt = [System.Windows.Forms.MessageBox]::Show(
    "Would you like to select a filter file to limit samples?`n`n(This is optional - click No to skip)",
    "Filter File",
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question
)

$filterFile = $null
if ($filterPrompt -eq [System.Windows.Forms.DialogResult]::Yes) {
    $filterFile = Get-CSVFileName -Title "Select CSV file for --filter-file (optional)"
    # Note: if user clicks Cancel on the file dialog, filterFile will be null, which is fine
}

# Create form for protocol selection
$form = New-Object System.Windows.Forms.Form
$form.Text = "Select Protocol and Parameters"
$form.Size = New-Object System.Drawing.Size(350, 280)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.TopMost = $true

# Create protocol label
$label = New-Object System.Windows.Forms.Label
$label.Location = New-Object System.Drawing.Point(10, 20)
$label.Size = New-Object System.Drawing.Size(320, 20)
$label.Text = "Select protocol:"
$form.Controls.Add($label)

# Create dropdown/combobox
$comboBox = New-Object System.Windows.Forms.ComboBox
$comboBox.Location = New-Object System.Drawing.Point(10, 50)
$comboBox.Size = New-Object System.Drawing.Size(310, 20)
$comboBox.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
$comboBox.Items.AddRange(@("fastuvpska", "phmetric", "uvmetric", "logp"))
$comboBox.SelectedIndex = 0  # Default to first option
$form.Controls.Add($comboBox)

# Create concentration label
$concentrationLabel = New-Object System.Windows.Forms.Label
$concentrationLabel.Location = New-Object System.Drawing.Point(10, 90)
$concentrationLabel.Size = New-Object System.Drawing.Size(150, 20)
$concentrationLabel.Text = "Concentration (mM):"
$form.Controls.Add($concentrationLabel)

# Create concentration textbox
$concentrationTextBox = New-Object System.Windows.Forms.TextBox
$concentrationTextBox.Location = New-Object System.Drawing.Point(160, 90)
$concentrationTextBox.Size = New-Object System.Drawing.Size(160, 20)
$concentrationTextBox.Text = "10"
$form.Controls.Add($concentrationTextBox)

# Create volume label
$volumeLabel = New-Object System.Windows.Forms.Label
$volumeLabel.Location = New-Object System.Drawing.Point(10, 120)
$volumeLabel.Size = New-Object System.Drawing.Size(150, 20)
$volumeLabel.Text = "Volume (µL):"
$form.Controls.Add($volumeLabel)

# Create volume textbox
$volumeTextBox = New-Object System.Windows.Forms.TextBox
$volumeTextBox.Location = New-Object System.Drawing.Point(160, 120)
$volumeTextBox.Size = New-Object System.Drawing.Size(160, 20)
$volumeTextBox.Text = "5"
$form.Controls.Add($volumeTextBox)

# Add event handler to disable concentration/volume for logP protocol
$comboBox.Add_SelectedIndexChanged({
    $selectedProtocol = $comboBox.SelectedItem
    if ($selectedProtocol -eq "logp") {
        $concentrationTextBox.Enabled = $false
        $volumeTextBox.Enabled = $false
        $concentrationLabel.Enabled = $false
        $volumeLabel.Enabled = $false
    } else {
        $concentrationTextBox.Enabled = $true
        $volumeTextBox.Enabled = $true
        $concentrationLabel.Enabled = $true
        $volumeLabel.Enabled = $true
    }
})

# Create OK button
$okButton = New-Object System.Windows.Forms.Button
$okButton.Location = New-Object System.Drawing.Point(160, 190)
$okButton.Size = New-Object System.Drawing.Size(75, 30)
$okButton.Text = "OK"
$okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.AcceptButton = $okButton
$form.Controls.Add($okButton)

# Create Cancel button
$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Location = New-Object System.Drawing.Point(245, 190)
$cancelButton.Size = New-Object System.Drawing.Size(75, 30)
$cancelButton.Text = "Cancel"
$cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.CancelButton = $cancelButton
$form.Controls.Add($cancelButton)

# Show form and get result
$formResult = $form.ShowDialog()

if ($formResult -eq [System.Windows.Forms.DialogResult]::OK) {
    $protocol = $comboBox.SelectedItem
    $concentration = $concentrationTextBox.Text
    $volume = $volumeTextBox.Text
} else {
    [System.Windows.Forms.MessageBox]::Show(
        "No protocol selected. Operation cancelled.",
        "Cancelled",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}

# Validate concentration and volume are numeric (if protocol is not logp)
if ($protocol -ne "logp") {
    try {
        $concentrationValue = [float]$concentration
        $volumeValue = [float]$volume
    } catch {
        [System.Windows.Forms.MessageBox]::Show(
            "Concentration and Volume must be valid numbers.",
            "Invalid Input",
            [System.Windows.Forms.MessageBoxButtons]::OK,
            [System.Windows.Forms.MessageBoxIcon]::Error
        )
        exit
    }
}


# Get --output folder name
$outputFolderPath = Split-Path $regiFile -Parent

$outputFolder = Join-Path -Path $outputFolderPath -ChildPath $protocol


# Prepare the command
$scriptName = "t3_gencsv.exe"
$arguments = "--regi `"$regiFile`" --pka `"$pkaFile`" --output `"$outputFolder`" --protocol $protocol"

# Add optional filter file if provided
if (-not [string]::IsNullOrEmpty($filterFile)) {
    $arguments += " --filter-file `"$filterFile`""
}

# Add concentration and volume for non-logP protocols
if ($protocol -ne "logp") {
    $arguments += " --concentration $concentration --volume $volume"
}

$fullCommand = "$scriptName $arguments"

# Create log filename with timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "log_$timestamp.txt"
$logPath = Join-Path -Path $outputFolderPath -ChildPath $logFile

# Write initial log entry
$filterFileLog = if ([string]::IsNullOrEmpty($filterFile)) { "None" } else { $filterFile }
$concentrationLog = if ($protocol -ne "logp") { $concentration } else { "N/A (logP protocol)" }
$volumeLog = if ($protocol -ne "logp") { $volume } else { "N/A (logP protocol)" }

$logContent = @"
========================================
T3 GenCSV Execution Log
========================================
Timestamp: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Command: $fullCommand

Parameters:
  --regi: $regiFile
  --pka: $pkaFile
  --filter-file: $filterFileLog
  --protocol: $protocol
  --concentration: $concentrationLog mM
  --volume: $volumeLog µL
  --output: $outputFolder (Regi folder + protocol)
========================================

"@

Add-Content -Path $logPath -Value $logContent

# Execute the script and capture output
try {
    Write-Host "Executing: $fullCommand" -ForegroundColor Cyan
    
    # Run the process and capture output
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $scriptName
    $processInfo.Arguments = $arguments
    $processInfo.UseShellExecute = $false
    $processInfo.RedirectStandardOutput = $true
    $processInfo.RedirectStandardError = $true
    $processInfo.CreateNoWindow = $true
    
    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $processInfo
    $process.Start() | Out-Null
    
    # Read output
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    
    # Prepare log output
    $outputLog = @"
STANDARD OUTPUT:
$stdout

STANDARD ERROR:
$stderr

EXIT CODE: $exitCode
========================================
"@
    
    # Write to log file
    Add-Content -Path $logPath -Value $outputLog
    
    # Determine success or failure
    if ($exitCode -eq 0) {
        $message = "Script executed successfully!`n`nExit Code: $exitCode`nOutput Folder: $outputFolder`n`nLog saved to: $logPath"
        $icon = [System.Windows.Forms.MessageBoxIcon]::Information
        $title = "Success"
        $color = "Green"
    } else {
        $message = "Script execution failed!`n`nExit Code: $exitCode`n`nLog saved to: $logPath`n`nError: $stderr"
        $icon = [System.Windows.Forms.MessageBoxIcon]::Error
        $title = "Error"
        $color = "Red"
    }
    
    # Display result
    Write-Host "`nExecution completed with exit code: $exitCode" -ForegroundColor $color
    Write-Host "Log file: $logPath" -ForegroundColor Yellow
    
    # Show message box
    $result = [System.Windows.Forms.MessageBox]::Show(
        $message,
        $title,
        [System.Windows.Forms.MessageBoxButtons]::OK,
        $icon
    )
    
    # Ask if user wants to view the log
    $viewLog = [System.Windows.Forms.MessageBox]::Show(
        "Would you like to open the log file?",
        "View Log",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Question
    )
    
    if ($viewLog -eq [System.Windows.Forms.DialogResult]::Yes) {
        notepad.exe $logPath
    }
    
} catch {
    $errorMessage = $_.Exception.Message
    $errorLog = @"
EXECUTION ERROR:
$errorMessage
========================================
"@
    Add-Content -Path $logPath -Value $errorLog
    
    [System.Windows.Forms.MessageBox]::Show(
        "An error occurred while executing the script:`n`n$errorMessage`n`nLog saved to: $logPath",
        "Error",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
}

