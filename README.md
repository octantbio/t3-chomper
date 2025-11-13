# T3 chomper

Parse data from [Pion Sirius T3 instrument](https://www.pion-inc.com/solutions/products/siriust3) XML files

# WARNING HIGHLY WIP 

# Instructions

## Installation
First clone and install the repo

```bash
git clone git@github.com:OpenADMET/t3-chomper.git
cd t3-chomper
pip install -e . 
```

Or download and install a whl file from a [release](https://github.com/octantbio/t3-chomper/releases)

```bash
pip install t3_chomper-0.1.5-py3-none-any.whl 
```

## Parsing data files

One can then parse file(s) from the T3 instrument using the CLI. 
One can parse from one file or a directory of t3r result files.
The user must specify whether you are parsing pka data or logp data with the --protocol argument.
Parsed results will be written to a csv file.

```bash
# Extract pka data from a file named my_data.t3r to pka_output.csv
t3_extract my_data.t3r --protocol pka --output pka_output.csv

# Extract logp data from a directory /home/data/logp_files to logp_output.csv
t3_extract /home/data/logp_files/ --protocol logp --output logp_output.csv

# Extract pka data from a file and write to stdout
t3_extract my_data.t3r --protocol pka 
```

## Generating experiment imports

One can also generate CSV import files for creating experiments. 
For this, one needs a **registration file** with sample information and a **pKa data file** with estimated pKas.
There are several defined experimental tray layouts which can be listed by viewing the help dialog:

```bash
t3_gencsv --help
```

The **registration file** should have the following columns (column names are case-insensitive):

| Column  | Description                                   |
|---------|-----------------------------------------------|
| sample  | compound/sample ID (must match pKa data file) |
| well    | well in plate                                 |
| mw      | molecular weight                              |
| fw      | formula weight                                |
| mg      | mass in mg                                    |

The **pKa data file** can be in one of two formats: 

### Short pKa data file format:

The short format includes one row for each compound and one column for all pKas per compound. 
It uses the same comma-separated format that the T3 instrument uses.

| Column           | Description                                                                         |
|------------------|-------------------------------------------------------------------------------------|
| sample           | compound/sample ID (must match registration file)                                   |
| reformatted_pkas | comma-separated list of pKas and types in ascending order: e.g. "ACID,2.5,BASE,9.3" |

### Long pKa data file format:

The long format includes one row for each pKa. 
Compounds with multiple pKas will appear in multiple rows.

| Column    | Description                                       |
|-----------|---------------------------------------------------|
| sample    | compound/sample ID (must match registration file) |
| pka_value | value of pka                                      |
| pka_type  | type of pka ("acid" or "base")                    |


### Filtering/Limiting Entries

One can limit the entries that are used in the experiment by filtering samples in the regi file 
by including a filter file with the `--filter-file` argument. The filter file just needs one column
**sample** that matches samples in the regi file. Only samples found in the filter file will progress
to subsequent steps for generating experiment files.

### Available experiment layouts

| TrayFormat | Description                                           |
|------------|-------------------------------------------------------|
| fastuvpska | 47 samples per tray, with one calibration             |
| phmetric   | 24 samples per tray, with 1x cleanup step after each  |
| uvmetric   | 24 samples per tray, calibration before each sample   |
| logp       | 16 samples per tray, with 2x cleanup steps after each |


Files for each tray will be generated in the output directory provided with the --output argument.

### Examples 

```bash
# Generate csv experiment import files with fastuvpska format
t3_gencsv --regi <registration file> --pka <pKa data file> --protocol fastuvpska --output <new_pka_experiment_dir>

# Generate csv experiment import files with logp format (solvent is required)
t3_gencsv --regi <registration file> --pka <pKa data file> --protocol logp --logp-solvent octanol --output <new_logp_experiment_dir>

# Generate csv experiment import files with phmetric tray format and only include samples listed in the filter file
t3_gencsv --regi <registration file> --filter-file <filter_file> --pka <pKa data file> --protocol phmetric --output <new_logp_experiment_dir>

# Generate csv with custom concentration (20 mM) and volume (10 µL)
t3_gencsv --regi <registration file> --pka <pKa data file> --protocol fastuvpska --concentration 20 --volume 10 --output <output_dir>

# Generate logP experiment with toluene solvent
t3_gencsv --regi <registration file> --pka <pKa data file> --protocol logp --logp-solvent toluene --output <output_dir>

```

### Optional Parameters

- `--concentration FLOAT`: Sample concentration in mM (default: 10.0)
- `--volume FLOAT`: Sample volume in µL (default: 5.0)
- `--logp-solvent [octanol|toluene|cyclohexane|chloroform]`: Solvent for logP protocol (**required when --protocol is logp**)
- `--sample-col TEXT`: Name of sample/ID column for joining files (default: "sample")
- `--filter-file FILE`: CSV file with sample names to include (filters the registration file)

**Notes:**
- `--concentration` and `--volume` are not used for logP protocol
- `--logp-solvent` is required when `--protocol` is `logp` - the command will fail with a validation error if not provided

```

## PowerShell Scripts for Windows Users

The `powershell_scripts/` folder contains Windows PowerShell scripts that provide GUI wrappers and utilities for working with T3 instrument data. These scripts are designed to simplify common workflows on Windows systems.

### Available Scripts

#### `create_experiment_folder.ps1`
Creates a standardized experiment folder structure for organizing T3 data.

**What it does:**
- Prompts for an Experiment ID (format: ST3-<id>)
- Creates a base experiment folder at `C:\New PION Data\<Experiment ID>`
- Creates standard subfolders:
  - `Unprocessed` - Raw, unprocessed T3R files
  - `QC Fail` - Files that failed quality control
  - `For logP` - Files prepared for logP analysis
  - `For UV-metric pKa` - Files for UV-metric pKa experiments
  - `For pH-metric pKa` - Files for pH-metric pKa experiments
  - `Input files` - Registration and pKa data files

**Usage:**
```powershell
.\powershell_scripts\create_experiment_folder.ps1
```

#### `parse_t3r_filenames.ps1`
Parses T3R filenames following a standard naming convention and exports metadata to CSV.

**What it does:**
- Opens folder browser to select a directory containing `.t3r` files
- Parses filenames matching pattern: `DATE_SAMPLE_ID_ASSAY_NAME.t3r`
- Extracts three fields: date, sample_id, assay_name
- Exports parsed data to `parsed_files_<timestamp>.csv`
- Reports skipped files that don't match the expected pattern

**Usage:**
```powershell
.\powershell_scripts\parse_t3r_filenames.ps1
```

#### `run_extract.ps1`
GUI wrapper for the `t3_extract` command-line tool.

**What it does:**
- Opens folder browser to select data location
- Presents dropdown to choose protocol (pka or logp)
- Executes `t3_extract.exe` with selected parameters
- Captures stdout, stderr, and exit code to timestamped log file
- Shows success/error dialog with option to view log

**Equivalent command line:**
```bash
t3_extract --protocol <selected_protocol> --output <protocol>_output.csv "<selected_folder>"
```

**Usage:**
```powershell
.\powershell_scripts\run_extract.ps1
```

#### `run_gencsv.ps1`
GUI wrapper for the `t3_gencsv` command-line tool.

**What it does:**
- Opens file browser to select registration CSV file (`--regi`)
- Opens file browser to select pKa data CSV file (`--pka`)
- Optionally prompts for filter file to limit samples (`--filter-file`)
- Presents dialog to choose protocol (fastuvpska, phmetric, uvmetric, logp)
- For non-logP protocols, allows customization of:
  - Concentration (mM) - default: 10
  - Volume (µL) - default: 5
  - These fields are disabled for logP protocol
- For logP protocol, allows selection of solvent:
  - Choices: <none>, octanol, toluene, cyclohexane, chloroform
  - Validation: Solvent selection is required for logP protocol
  - Dialog prevents closing until valid solvent is selected or user cancels
  - This field is disabled for non-logP protocols
- Automatically sets output folder to `<regi_folder>/<protocol>`
- Executes `t3_gencsv.exe` with selected parameters
- Captures output and creates timestamped log file
- Shows success/error dialog with option to view log

**Equivalent command line:**
```bash
# Non-logP protocol
t3_gencsv --regi "<selected_regi>" --pka "<selected_pka>" --protocol fastuvpska --concentration 10 --volume 5 --output "<regi_folder>/<protocol>"

# logP protocol with solvent
t3_gencsv --regi "<selected_regi>" --pka "<selected_pka>" --protocol logp --logp-solvent toluene --output "<regi_folder>/<protocol>"

# With filter file
t3_gencsv --regi "<selected_regi>" --pka "<selected_pka>" --filter-file "<selected_filter>" --protocol <selected_protocol> --concentration <value> --volume <value> --output "<regi_folder>/<protocol>"
```

**Usage:**
```powershell
.\powershell_scripts\run_gencsv.ps1
```

### Notes for Windows Users

- All scripts assume the default data location is `C:\New PION Data`
- Scripts use Windows Forms for GUI dialogs (file browsers, message boxes, dropdown menus)
- Log files are created with timestamps for tracking execution history
- The scripts expect `.exe` versions of the CLI tools (`t3_extract.exe`, `t3_gencsv.exe`) to be available in the system PATH

## CSV File Column Requirements and Validation

This section documents the exact column requirements for CSV input files used by `t3_gencsv`. The validation logic is implemented in `t3_chomper/formatters.py`.

### Registration File Column Requirements

All registration files require these **base columns** (case-insensitive):

- `sample` - Unique compound/sample identifier (used for joining with pKa file)
- `well` - Well position in the plate
- `mw` - Molecular weight

**Note:** You can customize the sample column name using `--sample-col` parameter (default: "sample")

**Protocol-specific additional requirements:**

| Protocol     | Additional Required Columns | Notes                                    |
|--------------|----------------------------|------------------------------------------|
| `fastuvpska` | None                       | Only base columns required               |
| `uvmetric`   | None                       | Only base columns required               |
| `phmetric`   | `fw`, `mg`                 | Formula weight and mass (solid samples)  |
| `logp`       | `fw`, `mg`                 | Formula weight and mass (solid samples)  |

**Validation behavior:**
- Column names are automatically converted to lowercase for matching
- Missing required columns will cause the program to exit with an error message
- The error message will specify which column is missing and in which file (see formatters.py:94-96, 208-211)

### pKa Data File Column Requirements

The pKa data file **always requires**:
- `sample` - Compound/sample identifier (must match registration file, or use `--sample-col` to specify a different column name)

The pKa file can be provided in **two formats**, which are automatically detected:

#### Format 1: Short Format (Preferred)
- `sample` - Sample identifier
- `reformatted_pkas` - Comma-separated string in the format: `"TYPE1,value1,TYPE2,value2,..."` where TYPE is either ACID or BASE
- Example: `"ACID,2.86,BASE,9.64"`

#### Format 2: Long Format (Automatically Converted)
If the `reformatted_pkas` column is **not present**, the code attempts to convert from long format.

Required columns for long format:
- `sample` - Sample identifier (or custom name via `--sample-col`)
- `pka_value` - Numeric pKa value
- `pka_type` - Type of pKa, either "acid" or "base" (case-insensitive)

**Conversion behavior:**
- Long format will be automatically converted to short format (see formatters.py:119-123)
- Multiple pKa values for the same compound should appear on separate rows
- Converted values are sorted by ascending pKa value
- Types are converted to uppercase in the output string
- The conversion is done by `convert_long_pka_df()` function (formatters.py:13-51)

**Validation behavior:**
- Missing required columns in long format conversion will raise a ValueError (formatters.py:35-38)
- Rows with missing pKa data after merging with registration file are dropped with a warning (formatters.py:131-138)
- The warning includes the sample IDs that were dropped

### Filter File Column Requirements (Optional)

If using the `--filter-file` option to limit which samples are processed:

**Required column:**
- `sample` - Sample identifiers to include (or custom name via `--sample-col`)

**Validation behavior:**
- Only samples present in the filter file will be processed from the registration file (formatters.py:106)
- If no matches are found between the filter file and registration file, the program exits with an error (formatters.py:108-111)
- A log message reports how many rows remain after filtering (formatters.py:112)

### General Validation Notes

1. **Case insensitivity**: All column name matching is case-insensitive. Files are read and column names are immediately converted to lowercase (formatters.py:76, 100, 115, 206)

2. **Column name customization**: The sample ID column name defaults to "sample" but can be changed via `--sample-col` parameter

3. **Merging logic**: The registration and pKa files are joined using a left join on the sample column, meaning:
   - All rows from the registration file are kept
   - Rows without matching pKa data receive null values
   - Null pKa rows are then dropped with a warning

4. **Automatically added columns**: The following columns are automatically added to the merged dataframe:
   - `concentration_mm` - Sample concentration in mM (from `--concentration` parameter, default: 10.0)
   - `volume_ul` - Sample volume in µL (from `--volume` parameter, default: 5.0)
   - These columns will have the same value for all records

5. **Error messages**: The code provides informative error messages that specify:
   - Which column is missing
   - Which file has the problem
   - For filter files: whether no matches were found

6. **Default column names**: When using `convert_long_pka_df()` programmatically, the default parameter names are:
   - `id_col="sample"`
   - `pka_col="pka_value"`
   - `pka_type_col="pka_type"`
   - `reformatted_pka_col="reformatted_pkas"`

### Code References

- Registration file validation: `formatters.py:87-96`
- pKa file validation: `formatters.py:114-123`
- Filter file validation: `formatters.py:99-112`
- Protocol-specific requirements: `formatters.py:192-218, 337-341, 372-376`
- Long-to-short format conversion: `formatters.py:13-51`