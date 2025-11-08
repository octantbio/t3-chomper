# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

T3 Chomper is a Python tool for parsing and processing data from Pion Sirius T3 instrument XML files. It supports two main workflows:
1. Extracting pKa and logP data from T3 result files (`.t3r` XML format)
2. Generating CSV experiment import files for the T3 instrument from registration and pKa data

## Development Setup

This project uses Poetry for dependency management with Python 3.9+.

```bash
# Install dependencies
poetry install --all-groups

# Run tests
poetry run pytest

# Format code
poetry run black .
```

## CLI Commands

The package provides two CLI entry points:

### `t3_extract` - Extract data from T3 result files

```bash
# Extract pka data from a single file
t3_extract my_data.t3r --protocol pka --output pka_output.csv

# Extract logp data from a directory
t3_extract /path/to/logp_files/ --protocol logp --output logp_output.csv

# Write to stdout instead of file
t3_extract my_data.t3r --protocol pka
```

### `t3_gencsv` - Generate experiment import files

```bash
# Generate CSV files for T3 instrument with specified tray format
t3_gencsv --regi <registration_file> --pka <pka_data_file> --protocol fastuvpska --output <output_dir>

# With sample filtering
t3_gencsv --regi <registration_file> --filter-file <filter_file> --pka <pka_data_file> --protocol phmetric --output <output_dir>

# With custom concentration and volume
t3_gencsv --regi <registration_file> --pka <pka_data_file> --protocol fastuvpska --concentration 20 --volume 10 --output <output_dir>
```

Available tray formats: `fastuvpska`, `phmetric`, `uvmetric`, `logp`

Optional parameters:
- `--concentration`: Sample concentration in mM (default: 10.0)
- `--volume`: Sample volume in µL (default: 5.0)
- `--sample-col`: Custom sample column name (default: "sample")
- `--filter-file`: CSV file to filter samples from registration file

## Code Architecture

### Core Modules

**`parsers.py`** - XML parsing logic for T3 result files
- `BaseT3RParser`: Abstract base class for parsing T3R XML files
- `UVMetricPKaT3RParser`: Parses pKa experiment results from XML
  - Handles two result formats: FastDpasMeanResult and DielectricFit (YasudaShedlovsky)
  - Extracts measured pKa values, standard deviations, ionic strength, and temperature
  - Matches measured results with predicted pKa types (acid/base)
- `LogPT3RParser`: Parses logP experiment results from XML
- Uses `xmltodict` to convert XML to Python dictionaries
- All parsers validate that the input file matches expected assay category

**`formatters.py`** - CSV generation for T3 instrument imports
- `SiriusT3CSVGenerator`: Abstract base class for generating experiment CSV files
- Concrete implementations for different tray formats:
  - `FastUVPSKAGenerator`: 47 samples/tray with one calibration
  - `UVMetricPSKAGenerator`: 24 samples/tray with automatic calibration before each
  - `PHMetricPSKAGenerator`: 24 samples/tray with cleanup after each (requires mg/fw)
  - `LogPGenerator`: 16 samples/tray with 2x cleanup between samples (requires mg/fw)
- `generate_registration_pka_file()`: Merges registration and pKa data, handles filtering, adds concentration_mm and volume_ul columns
- `convert_long_pka_df()`: Converts long-format pKa data (one row per pKa) to short-format (one row per compound with comma-separated pKa string)

**`t3_extractor.py`** - CLI for data extraction
- `FileOrPathExtractor`: Handles parsing single files or directories of `.t3r` files
- Tracks successful/failed parses and outputs results as CSV or to stdout

**`csv_generator.py`** - CLI for experiment file generation
- Orchestrates the workflow: reads registration + pKa files → merges → generates tray CSVs

### Data Models

**pKa Format**: The T3 instrument uses a comma-separated format for multiple pKas:
```
"ACID,2.5,BASE,9.3"  # type1,value1,type2,value2,...
```
Values are sorted in ascending order.

**Registration File Requirements**:
- Required columns (case-insensitive): `sample`, `well`, `mw`
- For pH-metric/logP protocols: also need `fw`, `mg`

**pKa Data File Formats**:
1. Short format: `sample`, `reformatted_pkas` (comma-separated string)
2. Long format: `sample`, `pka_value`, `pka_type` (one row per pKa, automatically converted)

### Key Implementation Details

- The parsers handle two different XML result structures for pKa data: FastDpasMeanResult (newer) and DielectricFit (YasudaShedlovsky method)
- Parser looks for measured pKa values first in FastDpasMeanResult tree, falls back to DielectricFit if not found
- The measured pKa results don't contain type information (acid/base), so it must be matched from predicted pKa values by assuming same ordering
- LogP parsing takes the maximum value when multiple logP values are present (see TODO comment in parsers.py:324)
- Column name matching is case-insensitive throughout
- Filter files allow subsetting a large registration file to only process specific samples

## Testing

Tests use pytest fixtures from `test/fixtures.py` that point to example data files in `test/data/`.

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest test/test_parsers.py
```

## Project Structure

```
t3_chomper/
  ├── parsers.py         # XML parsing classes
  ├── formatters.py      # CSV generation classes
  ├── t3_extractor.py    # Extract CLI
  ├── csv_generator.py   # Generate CSV CLI
  └── logger.py          # Logging utilities
test/
  ├── test_parsers.py
  ├── test_formatters.py
  ├── test_extractor.py
  ├── fixtures.py
  └── data/              # Test XML files
powershell_scripts/
  ├── create_experiment_folder.ps1   # Create standard folder structure
  ├── parse_t3r_filenames.ps1        # Parse T3R filename metadata
  ├── run_extract.ps1                # GUI wrapper for t3_extract
  └── run_gencsv.ps1                 # GUI wrapper for t3_gencsv
```

## PowerShell Script Development Best Practices

This project includes PowerShell scripts in `powershell_scripts/` for Windows users. When creating or modifying PowerShell scripts for this project, follow these conventions:

### GUI and User Interaction

**Use Windows Forms for GUI components:**
```powershell
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
```

**Standard dialog patterns:**
- **FolderBrowserDialog** - For directory selection
  - Set `SelectedPath` to default location (`C:\New PION Data`)
  - Set `TopMost = $true` for dialogs to appear on top
- **OpenFileDialog** - For file selection
  - Use appropriate filters (e.g., `"CSV files (*.csv)|*.csv"`)
  - Set `InitialDirectory` for better UX
- **MessageBox** - For notifications and confirmations
  - Use appropriate icons: Information, Warning, Error, Question
  - For TopMost message boxes, create a hidden form as owner (see `parse_t3r_filenames.ps1:24-48`)

**ComboBox for dropdown selections:**
```powershell
$comboBox = New-Object System.Windows.Forms.ComboBox
$comboBox.DropDownStyle = [System.Windows.Forms.ComboBoxStyle]::DropDownList
$comboBox.Items.AddRange(@("option1", "option2", "option3"))
$comboBox.SelectedIndex = 0  # Set default
```

### Process Execution and Logging

**Always capture and log command execution:**
```powershell
# Create timestamped log file
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logFile = "log_$timestamp.txt"
$logPath = Join-Path -Path $outputFolder -ChildPath $logFile

# Log command details before execution
$logContent = @"
========================================
Execution Log
========================================
Timestamp: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Command: $fullCommand
Parameters:
  --param1: $value1
  --param2: $value2
========================================
"@
Add-Content -Path $logPath -Value $logContent
```

**Process execution pattern:**
```powershell
# Create process with redirected output
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

# Capture output
$stdout = $process.StandardOutput.ReadToEnd()
$stderr = $process.StandardError.ReadToEnd()
$process.WaitForExit()
$exitCode = $process.ExitCode

# Log results
$outputLog = @"
STANDARD OUTPUT:
$stdout

STANDARD ERROR:
$stderr

EXIT CODE: $exitCode
========================================
"@
Add-Content -Path $logPath -Value $outputLog
```

### Error Handling and User Feedback

**Always check for user cancellation:**
```powershell
if ([string]::IsNullOrEmpty($selectedFolder)) {
    [System.Windows.Forms.MessageBox]::Show(
        "No folder selected. Operation cancelled.",
        "Cancelled",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )
    exit
}
```

**Use try-catch with detailed error logging:**
```powershell
try {
    # Operation code
} catch {
    $errorMessage = $_.Exception.Message
    $errorLog = @"
EXECUTION ERROR:
$errorMessage
========================================
"@
    Add-Content -Path $logPath -Value $errorLog

    [System.Windows.Forms.MessageBox]::Show(
        "An error occurred: `n`n$errorMessage`n`nLog saved to: $logPath",
        "Error",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    )
}
```

**Provide option to view log files:**
```powershell
$viewLog = [System.Windows.Forms.MessageBox]::Show(
    "Would you like to open the log file?",
    "View Log",
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question
)

if ($viewLog -eq [System.Windows.Forms.DialogResult]::Yes) {
    notepad.exe $logPath
}
```

### File and Path Handling

**Standard path construction:**
```powershell
# Default base directory
$pionTopFolder = "C:\New PION Data"

# Join paths safely
$outputPath = Join-Path -Path $selectedFolder -ChildPath $outputFile

# Get parent directory
$parentPath = Split-Path $filePath -Parent

# Get filename without extension
$baseName = $file.BaseName
```

**Check for existing paths:**
```powershell
if (Test-Path -Path $experimentPath) {
    # Prompt user for confirmation
    $result = [System.Windows.Forms.MessageBox]::Show(
        "Folder '$experimentPath' already exists!`n`nDo you want to continue?",
        "Folder Exists",
        [System.Windows.Forms.MessageBoxButtons]::YesNo,
        [System.Windows.Forms.MessageBoxIcon]::Warning
    )

    if ($result -eq [System.Windows.Forms.DialogResult]::No) {
        exit
    }
}
```

### Data Processing

**Array building pattern:**
```powershell
$parsedData = @()
$skippedFiles = @()

foreach ($file in $files) {
    if ($file -match $pattern) {
        $parsedData += [PSCustomObject]@{
            field1 = $value1
            field2 = $value2
        }
    } else {
        $skippedFiles += $file.Name
        Write-Warning "Skipped: $($file.Name)"
    }
}
```

**CSV export:**
```powershell
$parsedData | Export-Csv -Path $csvPath -NoTypeInformation
```

### Naming Conventions

- **Script names**: Use descriptive names with underscores (e.g., `run_gencsv.ps1`, `create_experiment_folder.ps1`)
- **Variables**: Use camelCase for local variables (`$selectedFolder`, `$exitCode`)
- **Constants**: Use PascalCase for user-facing constants (`$ExperimentID`)
- **Functions**: Use Verb-Noun pattern (`Get-FolderPath`, `Show-TopMessageBox`)

### Command Arguments

**Quote paths with spaces:**
```powershell
$arguments = "--regi `"$regiFile`" --pka `"$pkaFile`" --output `"$outputFolder`""
```

**Build full command string for logging:**
```powershell
$fullCommand = "$scriptName $arguments"
```

### Project-Specific Conventions

- Default data location: `C:\New PION Data`
- Log files use timestamp format: `log_yyyyMMdd_HHmmss.txt`
- Output files use timestamp format: `parsed_files_yyyyMMdd_HHmmss.csv`
- CLI tools are expected as `.exe` files: `t3_extract.exe`, `t3_gencsv.exe`
- All forms should have `TopMost = $true` for visibility
- Always provide both console output (Write-Host) and GUI feedback (MessageBox)
