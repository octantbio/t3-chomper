# T3 chomper

Parse data from  Pion Sirius T3 instrument (https://www.pion-inc.com/solutions/products/siriust3) XML files


# WARNING HIGHLY WIP 


# Instructions

First clone and install the repo

```bash
git clone git@github.com:OpenADMET/t3-chomper.git
cd t3-chomper
pip install -e . 
```

You can then parse file(s) from the T3 instrument using the CLI

```bash
t3_extract <file or path> --protocol pka --output pka_output.csv
```

Or generate CSV import files to create a pka experiment:

```bash
t3_gencsv --regi <registration file> --pka <estimated pka file> --protocol pka --output <pka_experiment_dir>
```