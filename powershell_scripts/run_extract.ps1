# RunT3GenCSV.ps1

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$pionTopFolder = "C:\New PION Data"

$folderBrowser = New-Object System.Windows.Forms.FolderBrowserDialog
$folderBrowser.Description = "Select the data location"
$folderBrowser.RootFolder = [System.Environment+SpecialFolder]::MyComputer
$folderBrowser.SelectedPath = $pionTopFolder  # Starting location

if ($folderBrowser.ShowDialog() -eq [System.Windows.Forms.DialogResult]::OK) {
    $selectedFolder = $folderBrowser.SelectedPath
} else {
    [System.Windows.Forms.MessageBox]::Show(
        "No folder selected. Operation cancelled.",
        "Cancelled",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}

# Create form for protocol selection
$form = New-Object System.Windows.Forms.Form
$form.Text = "Select Protocol"
$form.Size = New-Object System.Drawing.Size(350, 200)
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = "FixedDialog"
$form.MaximizeBox = $false
$form.TopMost = $true

# Create label
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
$comboBox.Items.AddRange(@("pka", "logp"))
$comboBox.SelectedIndex = 0  # Default to first option
$form.Controls.Add($comboBox)

# Create OK button
$okButton = New-Object System.Windows.Forms.Button
$okButton.Location = New-Object System.Drawing.Point(160, 110)
$okButton.Size = New-Object System.Drawing.Size(75, 30)
$okButton.Text = "OK"
$okButton.DialogResult = [System.Windows.Forms.DialogResult]::OK
$form.AcceptButton = $okButton
$form.Controls.Add($okButton)

# Create Cancel button
$cancelButton = New-Object System.Windows.Forms.Button
$cancelButton.Location = New-Object System.Drawing.Point(245, 110)
$cancelButton.Size = New-Object System.Drawing.Size(75, 30)
$cancelButton.Text = "Cancel"
$cancelButton.DialogResult = [System.Windows.Forms.DialogResult]::Cancel
$form.CancelButton = $cancelButton
$form.Controls.Add($cancelButton)

# Show form and get result
$formResult = $form.ShowDialog()

if ($formResult -eq [System.Windows.Forms.DialogResult]::OK) {
    $protocol = $comboBox.SelectedItem
} else {
    [System.Windows.Forms.MessageBox]::Show(
        "No protocol selected. Operation cancelled.",
        "Cancelled",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}
$outputFile = $protocol + "_output.csv"
$outputPath = Join-Path -Path $selectedFolder -ChildPath $outputFile

# Prepare the command
$scriptName = "t3_extract.exe"
$arguments = "--protocol $protocol --output `"$outputPath`" `"$selectedFolder`""

$fullCommand = $scriptName + " " + $arguments

# Create log filename with timestamp
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "log_$timestamp.txt"
$logPath = Join-Path -Path $selectedFolder -ChildPath $logFile

# Write initial log entry
$logContent = @"
========================================
T3 GenCSV Execution Log
========================================
Timestamp: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Command: $fullCommand

Parameters:
  Working Folder: $selectedFolder
  --protocol: $protocol
  --output: $selectedFolder
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
    
    # Use StringBuilder to collect output asynchronously
    $stdout = New-Object System.Text.StringBuilder
    $stderr = New-Object System.Text.StringBuilder
    
    # Register async event handlers
    $outputHandler = {
        if (-not [String]::IsNullOrEmpty($EventArgs.Data)) {
            $Event.MessageData.AppendLine($EventArgs.Data)
        }
    }
    
    $outputEvent = Register-ObjectEvent -InputObject $process `
        -EventName OutputDataReceived `
        -MessageData $stdout `
        -Action $outputHandler
    
    $errorEvent = Register-ObjectEvent -InputObject $process `
        -EventName ErrorDataReceived `
        -MessageData $stderr `
        -Action $outputHandler
    
    $process.Start() | Out-Null
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()
    
    # Wait for process to exit
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    
    # Clean up events
    Unregister-Event -SourceIdentifier $outputEvent.Name
    Unregister-Event -SourceIdentifier $errorEvent.Name
    
    # Get the collected output
    $stdoutText = $stdout.ToString()
    $stderrText = $stderr.ToString()
    
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

