from Agency_proposal_extractor.NIH_Extractor import NIHExtractor
from Agency_proposal_extractor.NSF_Extractor import NSFExtractor


import argparse
import yaml
import sys
import os
import pdb

import pandas as pd


class AgencyDataExtractor():
    """ Class which can extract data from required agencey webpages.
        Currently added agencie - NIH, NSF

    """

    def __init__(self, n_cores, agencies, params):
        """ Constuctor

        :param n_cores: No of CPU cores to be used 
        :type n_cores: `int`
        :param agencies: List of agence names from which data is to be extracted
        :type agencies: `List`
        :param params: Dictionary of default parameter values from CONFIG.yml file
        :type params: `Dict`

        :return: None
        """
        self.n_cores = params['CPU_COUNT'] if n_cores == 0 else n_cores
        self.agencies_filenames = params['AGENCIES_FILENAME_DICT']
        self.agencies = params['AGENCIES'] if agencies == [] else agencies
        self.output_path = params['OUTPUT_PATH']
        self.output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.output_path )
        self.agency_extractors = {
            'National Institutes of Health': NIHExtractor,
            'National Science Foundation': NSFExtractor}
        self.extracted_agencies_filenames = params['AGENCIES_EXTRACTED_FILENAME_DICT']


    def extract_agency_proposals(self):
        """ Parent function which calls child functions to retrieve data for each agency.
        Each child function will save the data to specific files separately. 
        :param None: 
        
        :return: None
        """

        for agency in self.agencies:

            try:
                
                data = pd.read_csv(
                    os.path.join(
                        self.output_path,
                        self.agencies_filenames[agency]))
                urls = data[data['AgencyName'] ==
                            agency]['AdditionalInformationURL'].values
                extractor = self.agency_extractors[agency](
                    data=data, urls=urls, save_filename=self.extracted_agencies_filenames[agency])
                extractor.extract_all(
                    n_cores=self.n_cores,
                    output_path=self.output_path)
                print("Completed extraction for agency - :", agency)
                
            except BaseException:
                print("Error for Agency : ", agency)


if __name__ == "__main__":

    # Read arguments from command line (cmd). If no input via cmd, use config
    # file
    parser = argparse.ArgumentParser(description="Parameter file")
    parser.add_argument(
        '--config_file',
        metavar='FILENAME',
        type=str,
        default='config.yml',
        help='Parameter file name in yaml format')
    parser.add_argument('-a',
        '--agencies',
        metavar='AGENCIES',
        nargs="*",
        default=[
            'National Science Foundation',
            'National Institutes of Health'],
        help='Agencies whose proposals are to be extracted')
    parser.add_argument(
        '--n_cores',
        metavar='CPU_COUNT',
        type=int,
        default=0,
        help='No of CPU threads to be used')
    args = parser.parse_args()
    
    print("\n\nExtracting Proposals from Agencies")
    
    try:
        params = yaml.safe_load(open(args.config_file))
    except BaseException:
        print(f'Error loading parameter file: {args.config_file}.')
        sys.exit(1)

    extractor = AgencyDataExtractor(
        n_cores=args.n_cores,
        agencies=args.agencies,
        params=params)
    extractor.extract_agency_proposals()
    
    print("TASK COMPLETED : Completed Extracting Proposals") 
