

import click 
import glob
import loguru
import pandas as pd 
from pathlib import Path
from xml.etree import ElementTree


def parse_t3_pka_xml(file: Union[str, Path]) -> tuple[int]
    """
    Read XML file from the  Sirus T3  machine

    TODO: is there any difference between potentiometric and
    spectophotometric in terms of keys??
    """
    with open(file, 'r') as f:
        xmlstr = f.read()
        # Parse XML from a string
        try: 
            root = ElementTree.fromstring(xml_data)
        except:
            raise ValueError("Could not read XML")

    #TODO: check for no data 

    # grab averages, could do more here also
    pka = root.Find("MeanPkaResults")
    stdev = root.Find("MeanPkasStdDevs")
    ionic_strength = root.Find("MeanPkasAverageIonicStrength")
    temp =  root.Find("MeanPkasAverageTemperature")


    return pka, stdev, ionic_strength, temp

# don' bake into CLI so callable in script etc
def parse_pkas(t3_dir, t3_file) -> pd.DataFrame

    if not t3_dir or not t3_file:
        raise ValueError("Both t3_dir and t3_file must be provided.")
    if t3_dir and  t3_file:
        raise ValueError("Both t3_dir and t3_file cannot be provided at the same time.")

    if t3_dir:
        t3_files = glob.glob(f"{t3_dir}/*.t3")
        if not t3_files:
            raise FileNotFoundError(f"No .t3 files found in directory: {t3_dir}")
    else:
        t3_files = [t3_file]

    df = pd.DatFrame()
    for t3_file in t3_files:
        logger.debug(f"Parsing T3 XML file: {t3_file}")
        # read each, returning pka and stdev 
        pka, stdev, ionic_strength, temp =  parse_t3_pka_xml(t3_file)
        
    return df



@click.command()
@click.argument('t3-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True))
@click.argument('t3-file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True))
@click.argument('output-csv', type=click.Path(exists=False, file_okay=True, default="t3_data.csv"))
def pka(t3_dir, t3_file, output_csv):
    logger.info(f"Running T3 pKa parsing")
    df = parse_pkas(t3_dir, t3_file)
    logger.info(f"Finished, writing to {output_csv}")
    df.to_csv(output_csv, index=False)





    









