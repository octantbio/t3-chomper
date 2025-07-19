import click
import glob
import pandas as pd
from pathlib import Path
from typing import Union
import xmltodict
from loguru import logger 



def parse_t3_pka_xml(file: Union[str, Path]) -> tuple:
    """
    Read XML file from the Sirus T3 machine and extract pKa data.
    
    Returns:
        Tuple of (pka, stdev, ionic_strength, temp)
    """
    with open(file, 'r') as f:
        xmlstr = f.read()
        root = xmltodict.parse(xmlstr)

    try:
        pka_res = root["DirectControlAssayResultsFile"]["ProcessedData"]["FastDpasMeanResult"]
    except KeyError as e:
        raise ValueError("No pKa data found in file") from e

    def get_xml_elem(elem):
        return elem['#text']


    pka = get_xml_elem(pka_res["MeanPkaResults"])
    stdev = get_xml_elem(pka_res["MeanPkasStdDevs"])
    ionic_strength = get_xml_elem(pka_res["MeanPkasAverageIonicStrength"])
    temp = get_xml_elem(pka_res["MeanPkasAverageTemperature"])


    return pka,  stdev, ionic_strength, temp



def parse_pkas(t3_dir: Union[str, None] = None, t3_file: Union[str, None] = None) -> pd.DataFrame:
    """
    Parse one or multiple .t3 files from directory or single file into a DataFrame.

    Only one of t3_dir or t3_file must be provided.
    """
    if (t3_dir is None and t3_file is None) or (t3_dir and t3_file):
        raise ValueError("Provide either t3_dir or t3_file, but not both.")

    if t3_dir:
        t3_files = glob.glob(f"{t3_dir}/*.t3")
        if not t3_files:
            raise FileNotFoundError(f"No .t3 files found in directory: {t3_dir}")
    else:
        t3_files = [t3_file]

    rows = []
    for file in t3_files:
        logger.debug(f"Parsing T3 XML file: {file}")
        try:
            pka, stdev, ionic_strength, temp = parse_t3_pka_xml(file)
        except Exception as e:
            logger.error(f"Error parsing file {file}: {e}")
            continue

        rows.append({
            "file": Path(file).name,
            "pka": pka,
            "stdev": stdev,
            "ionic_strength": ionic_strength,
            "temperature": temp
        })

    df = pd.DataFrame(rows)
    return df


@click.command()
@click.option('--t3-dir', type=click.Path(exists=True, file_okay=False, dir_okay=True, readable=True), default=None, help="Directory containing .t3 files")
@click.option('--t3-file', type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True), default=None, help="Single .t3 file to parse")
@click.option('--output_csv', type=click.Path(exists=False, file_okay=True), default="pka_results.csv")
def pka(t3_dir, t3_file, output_csv):
    """
    CLI entry point for parsing T3 pKa XML files and exporting to CSV.
    """
    logger.info("Running T3 pKa parsing")
    df = parse_pkas(t3_dir, t3_file)
    logger.info(f"Finished parsing, writing to {output_csv}")
    df.to_csv(output_csv, index=False)


if __name__ == "__main__":
    pka()
