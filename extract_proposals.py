import os
import re
import zipfile
import requests
import datetime
import argparse
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
import yaml

from bs4 import BeautifulSoup
from xml.dom import minidom

import pdb

from helpers import get_formatted_date


class GrantsDataExtractor(object):
    """ Class which will extract data from the Grants.Gov website.

    As per design, we will first download the list of all Open proposals from the Grants.gov.
    Later for each proposal, further data is extracted from the dedicated webpage (for example from NSF website).
        
    """

    def __init__(self, xml_url, csv_url, agencies, params):
        """ Constructor

        :param xml_url: The URL from which XML file is to be downloaded
        :type xml_url: `str`
        :param csv_url: The URL from which CSV file is to be downloaded
        :type csv_url: `str`
        :param agencies: List of agencies for which proposals are to be extracted
        :type agencies: `List`
        :param params: Deafult set of parameters read from the CONFIG.yml file
        :type params: `Dict`
        
        :return: None
        """
        self.output_path = params['OUTPUT_PATH']
        self.output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.output_path )
        self.xml_url = params['XML_URL'] if xml_url == '' else xml_url
        self.csv_url = params['CSV_URL'] if csv_url == '' else csv_url
        self.agencies_filenames = params['AGENCIES_FILENAME_DICT']
        self.agencies = params['AGENCIES'] if agencies == [] else agencies
        self.tags = params['TAGS']
        self.open_proposal_filename = params["OPEN_PROPOSALS_DATASET"]
        self.grants_filename = params["GRANTS_DATASET"]
        self.grants_download_folder = params["GRANTS_DOWNLOAD_FOLDER"]
        self.grants_download_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.grants_download_folder )
        self.grant_downloaded_csv_filename = params["GRANTS_DOWNLOAD_CSV_FILENAME"]
        
        if not os.path.exists(self.output_path):
            os.mkdir(self.output_path)

    def ExtractCSVData(self):
        """ Function to extract data from the downloaded CSV file 
        Once the data is extracted it will be saved as a dataframe - self.metadata
        
        :return: None
        """

        response = requests.get(self.csv_url)

        if not os.path.exists(
            os.path.join(
                os.getcwd(),
                self.grants_download_folder)):
            os.mkdir(os.path.join(os.getcwd(), self.grants_download_folder))

        open(
            os.path.join(
                os.getcwd(),
                self.grants_download_folder,
                self.grant_downloaded_csv_filename),
            'wb').write(
            response.content)

        # Read data from CSV
        self.metadata = pd.read_csv(
            os.path.join(
                os.getcwd(),
                self.grants_download_folder,
                self.grant_downloaded_csv_filename),
            error_bad_lines=False,
            warn_bad_lines=False)

        column_names = self.metadata.columns
        self.metadata.reset_index(inplace=True)
        self.metadata = self.metadata.iloc[:, :len(column_names)]
        self.metadata.columns = column_names

        # Extract hyperlink
        self.metadata['URL'] = self.metadata['OPPORTUNITY NUMBER'].apply(
            lambda x: x.split('"')[1]) 
        self.metadata['OPPORTUNITY NUMBER'] = self.metadata['OPPORTUNITY NUMBER'].apply(
            lambda x: x.split('"')[-2])

    def ExtractXMLData(self):
        """ Function to extract data from the XML file.
        Once the data is extracted it will be saved as a dataframe - self.opps_df
        
        :param None: 
        
        :return: None
        """

        response = requests.request("GET", self.xml_url, headers={}, data={})
        response_str = response.text
        soup = BeautifulSoup(response_str, "html.parser")

        zip_url = soup.findAll('a', href=True, text=re.compile(
            "GrantsDBExtract"))[-1]['href']
        filename = zip_url.split('/')[-1]
        print("DOWNLOADING ZIP FILE FROM - ", zip_url)
        response = requests.get(zip_url)
        open(
            os.path.join(
                os.getcwd(),
                self.grants_download_folder,
                filename),
            'wb').write(
            response.content)

        with zipfile.ZipFile(os.path.join(os.getcwd(), self.grants_download_folder, filename), 'r') as zip_ref:
            zip_ref.extractall(
                os.path.join(
                    os.getcwd(),
                    self.grants_download_folder))
        doc = minidom.parse(
            os.path.join(
                os.getcwd(),
                self.grants_download_folder,
                filename.replace(
                    '.zip',
                    '') + '.xml'))

        opps = doc.getElementsByTagName("OpportunitySynopsisDetail_1_0")

        opp_list = []
        for opp in tqdm(opps):
            dict_ = {}
            for tag in self.tags:
                try:
                    dict_[tag] = opp.getElementsByTagName(
                        tag)[0].firstChild.data
                except BaseException:
                    dict_[tag] = ''
            opp_list.append(dict_)

        self.opps_df = pd.DataFrame(opp_list)

    def ProcessXMLData(self):
        """ Function to process extracted the XML data.
        Reformat columns - CloseDate, PostDate. LastUpdateDate.
        Identify Open Proposals.

        :param None : 
        
        :return: None
        """

        # Reformate Columns
        self.opps_df['CloseDate'] = get_formatted_date(
            data=self.opps_df['CloseDate'], format_='%m%d%Y')
        self.opps_df['PostDate'] = get_formatted_date(
            data=self.opps_df['PostDate'], format_='%m%d%Y')
        self.opps_df['LastUpdatedDate'] = get_formatted_date(
            data=self.opps_df['LastUpdatedDate'], format_='%m%d%Y')

        self.data = pd.merge(self.opps_df,
                             self.metadata[['OPPORTUNITY NUMBER',
                                            'URL']],
                             how='left',
                             left_on='OpportunityNumber',
                             right_on='OPPORTUNITY NUMBER')

        # Identify Open proposals
        self.open_df = self.data[(
            self.data['CloseDate'] > datetime.date.today())]
        self.open_df.reset_index(drop=True, inplace=True)

    def SaveXMLData(self):
        """ Function to save all the XML Data to CSV files. Specifically, Open Proposals agency wise will be saved in seprate files.

        :param None : 
        
        :return: None
        """

        for agency in self.agencies:
            agency_dataset = self.open_df[self.open_df['AgencyName'] == agency]
            agency_dataset.to_csv(
                os.path.join(
                    self.output_path,
                    self.agencies_filenames[agency]))

        self.data.to_csv(
            os.path.join(
                self.output_path,
                self.grants_filename),
            index=False)
        self.open_df.to_csv(
            os.path.join(
                self.output_path,
                self.open_proposal_filename),
            index=False)

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
    parser.add_argument(
        '--xml_url',
        metavar='XML_URL',
        type=str,
        default='',
        help='URL to download the XML FILE')
    parser.add_argument(
        '--csv_url',
        metavar='XML_URL',
        type=str,
        default='',
        help='URL to download the CSV FILE')
    parser.add_argument(
        '--agencies',
        metavar='AGENCIES',
        type=list,
        default=[
            'National Science Foundation',
            'National Institutes of Health'],
        help='List of agencies for which proposals are to be extracted')
    args = parser.parse_args()
    
    print("\n\nExtracting Proposals from Grants.gov")

    try:
        params = yaml.safe_load(open(args.config_file))
    except BaseException:
        print(f'Error loading parameter file: {args.config_file}.')
        sys.exit(1)

    data_extractor = GrantsDataExtractor(
        xml_url=args.xml_url,
        csv_url=args.csv_url,
        agencies=args.agencies,
        params=params)
    data_extractor.ExtractCSVData()
    data_extractor.ExtractXMLData()
    data_extractor.ProcessXMLData()
    data_extractor.SaveXMLData()
    
    print("TASK COMPLETED : Successfully Extracted Proposals ..")