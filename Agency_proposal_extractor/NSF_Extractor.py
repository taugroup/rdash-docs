from helpers import parallelize, tokenize
import os
import re
import requests
from tqdm import tqdm
import pdb
import argparse
import yaml
import sys

import numpy as np
import pandas as pd

from bs4 import BeautifulSoup
from multiprocessing import Pool

sys.path.append('..')


""" ITEMS TO CORRECT :
    - Remove ID from 'processing' (token extraction)
"""


def processing(id_, text):
    # pdb.set_trace()
    p_text = tokenize(text)

    # ORIGINAL CODE
    # return " ".join([i for i in p_text if (i not in ["national", "science", "foundation", id_ ] and not i.isdigit())])
    # MODIFIED CODE - TO BE DELETED
    return " ".join([i for i in p_text if (
        i not in ["national", "science", "foundation"] and not i.isdigit())])


def remove_tags(text):

    re_text = re.sub(r'<[^>]+>', ' ', str(text))
    return re_text.replace("\xa0", "")


def isSection(ele, eleId):
    return ele.name == 'h3' and ele.find("a", {"id": eleId}) is not None


def clean_text(text):

    re_text = re.sub(r'<[^>]+>', ' ', str(text))
    re_text = re.sub(' +', ' ', re_text)
    return re_text.replace("\xa0", "")


class NSFExtractor():
    """ Class which contains all the required functions to extract data from the NSF website
    """


    def __init__(self, urls, data, save_filename):
        """ Constructor
        
        :param urls: Array of URLs from which proposal data need to be extracted
        :type urls: `numpy.ndarray`
        :param data: List of URLs from which proposal data need to be extracted
        :type data: class `Pandas.DataFrame`
        :param save_filename: Filename to save the extracted NIH data
        :type save_filename: `str`
        
        :return: data
		:rtype: `str`

        """
        self.urls = urls
        self.main_data = data
        self.idx = urls
        self.save_filename = save_filename

    def get_response(self, url):
        """ Function to retrieve response from NSF page. The processed response will be save as self.soup

        :param url: The URL from which response is to be retrieved
        :type url: `str`
        
        :return: Response Data
        :rtype: class `response`
        """
        payload = {}
        headers = {}
        response = requests.request("GET", url, headers=headers, data=payload)
        self.soup = BeautifulSoup(response.text, "html.parser")
        try:
            nsf_url = self.soup.find_all(
                "a", href=True, text="HTML")[0]['href']
            if nsf_url[:5] == '/pubs':
                nsf_url = "https://www.nsf.gov" + nsf_url
            self.response = requests.request(
                "GET", nsf_url, headers=headers, data=payload)
            response_str = self.response.text
            self.soup = BeautifulSoup(response_str, "html.parser")

        except BaseException:
            return ''
        return self.response

    def get_title(self):
        """ Function to extract the Title details from NSF webpage. The webpage details are obtained from self.soup
        
        :return: Title 
        :rtype:  `str`
        """
        return processing(self.idx, remove_tags(self.soup.find("title")))

    def get_dept(self):
        """ Function to extract the Department details from NSF webpage. The webpage details are obtained from self.soup
        
        :return: Department
        :rtype:  `str`
        """

        dept_text = self.soup.find("table").find(
            "table").find("tr").find_all("td")[-1]
        dept_text = remove_tags(str(dept_text))
        return processing(self.idx, dept_text)

    def get_intro_desc(self):
        """ Function to extract the Introduction and Description from NSF webpage. 
        The webpage details are obtained from self.soup. 
        
        :return: Tuple containing the extracted text for introduction / description 
        :rtype:  `Tuple`
        """
        elements = self.soup.find_all()
        idxList = []
        for idx in range(len(elements)):
            if isSection(elements[idx], "pgm_intr_txt"):
                idxList.append(idx)
            if isSection(elements[idx], "pgm_desc_txt"):
                idxList.append(idx)
            if isSection(elements[idx], "awd_info"):
                idxList.append(idx)

        intr_text = " ".join([remove_tags(str(i))
                             for i in elements[idxList[0] + 1:idxList[1]]])
        desc_text = " ".join([remove_tags(str(i))
                             for i in elements[idxList[1] + 1:idxList[2]]])

        return processing(self.idx, intr_text), processing(self.idx, desc_text)

    def extract_page_info(self, url, i):
        """ Function to extract all details from NSF webpage.
        
        :param url: The URL from which proposal details should be extracted
        :type url: `str'
        :param i: A placeholde number for idnetifying the URL index
        :type i: `int  `

        :return: List containing 'URL',keywords for organization, keywords for description 
        :rtype: `list`
        """
        try:
            response = self.get_response(url)
            title = self.get_title()
            dept = self.get_dept()
            intr, desc = self.get_intro_desc()
            return [url, title, dept, intr, desc]
        except BaseException:
            return [url] + [np.nan] * 4

    def extract_all(self, n_cores, output_path):
        """ Parent function to extract all webpage details from NSF (using URLs extracted from Grants.gov). 
        The function saves all the details to the 'save_filename' file in 'output_path'


        :param n_cores: No: of cores of CPU to be utilized for parallel processing
        :type n_cores: `int`
        :param output_path: The path where all the data is saved
        :type output_path: `str`


        :return: None
        """

        ipt = [(i, j) for i, j in zip(self.urls, range(len(self.urls)))]
        descs = []

        # #TEST
        # ipt = ipt[:10]
        # self.extract_page_info(ipt[7][0], ipt[7][1])
        descs = parallelize(
            n_cores=n_cores,
            func=self.extract_page_info,
            arg1=ipt)
        cfp_df = pd.DataFrame(
            descs,
            columns=[
                "URL",
                "Title",
                "Organization",
                "Introduction",
                "Description_"])
        cfp_df = cfp_df.assign(
            Description=lambda x: x['Introduction'] +
            ' ' +
            x['Description_'])
        cfp_df.drop(['Introduction', 'Description_'], axis=1)
        final_data = pd.merge(cfp_df,
                              self.main_data[['OPPORTUNITY NUMBER',
                                              'OpportunityTitle',
                                              'AdditionalInformationURL']],
                              left_on='URL',
                              right_on='AdditionalInformationURL',
                              how='left')
        final_data = final_data[['OPPORTUNITY NUMBER', 'URL',
                                 'OpportunityTitle', 'Organization', 'Description']]
        final_data.rename(
            columns={
                'OpportunityTitle': 'Title',
                'OPPORTUNITY NUMBER': 'Opportunity Number',
                'Organization': 'Department'},
            inplace=True)
        final_data.to_csv(
            os.path.join(
                output_path,
                self.save_filename),
            index=False)


# if __name__ == "__main__":


#     # Read arguments from command line (cmd). If no input via cmd, use config file
#     parser = argparse.ArgumentParser(description="Parameter file")
#     parser.add_argument('--config_file', metavar='FILENAME', type=str, default = 'config_updated.yml', help='Parameter file name in yaml format')
#     parser.add_argument('--agencies', metavar='AGENCIES', type=str, default = ['National Science Foundation'], help='Agencies whose proposals are to be extracted')
#     parser.add_argument('--cpu_count', metavar='CPU_COUNT', type=int, default = 0, help='No of CPU threads to be used')
#     args = parser.parse_args()

#     try:
#         params = yaml.safe_load(open(args.config_file))
#     except:
#         print(f'Error loading parameter file: {args.config_file}.')
#         sys.exit(1)

#     extractor = AgencyDataExtractor(args)
#     extractor.extract_agency_proposals()
