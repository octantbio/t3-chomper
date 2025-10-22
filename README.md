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

The **registration file** should have the following columns:

| Column          | Description                            |
|-----------------|----------------------------------------|
| ID              | compound ID (must match pKa data file) |
| Registry Number | compound name in registry              |
| Batch Name      | Name/number of compound batch          |
| Well            | well in plate                          |
| MW              | molecular weight                       |
| FW              | formula weight                         | 
| mg              | mass in mg                             |



The **pKa data file** can be in one of two formats: 

### Short pKa data file format:

The short format includes one row for each compound and one column for all pKas per compound. 
It uses the same comma-separated format that the T3 instrument uses.

| Column           | Description                                                                         |
|------------------|-------------------------------------------------------------------------------------|
| vendor_id        | compound ID (must match registration file)                                          |
| reformatted_pkas | comma-separated list of pKas and types in ascending order: e.g. "ACID,2.5,BASE,9.3" |

### Long pKa data file format:

The long format includes one row for each pKa. 
Compounds with multiple pKas will appear in multiple rows.

| Column    | Description                                |
|-----------|--------------------------------------------|
| vendor_id | compound ID (must match registration file) |
| pka_value | value of pka                               |
| pka_type  | type of pka ("acid" or "base")             |


### Available experiment layouts

| TrayFormat | Description                                           |
|------------|-------------------------------------------------------|
| fastuvpska | 47 samples per tray, with one calibration             |
| phmetric   | 24 samples per tray, with 1x cleanup step after each  |
| uvmetric   | 24 samples per tray, calibration before each sample   |
| logp       | 16 samples per tray, with 2x cleanup steps after each |


Files for each tray will be generated in the output directory provided with the --output argument.

```bash
# Generate csv experiment import files with fastuvpska format
t3_gencsv --regi <registration file> --pka <pKa data file> --protocol fastuvpska --output <new_pka_experiment_dir>
# Generate csv experiment import files with logp format
t3_gencsv --regi <registration file> --pka <pKa data file> --protocol logp --output <new_logp_experiment_dir>
```