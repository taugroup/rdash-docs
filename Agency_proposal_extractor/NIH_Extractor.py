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

from helpers import parallelize


def clean_text(text):
    """ Function to clean a given text. Removes all junk characters and replaces multiple spaces by single space
        
        :param text: Text to be cleaned
        :type text: `str`
        
        :return: Cleaned Text
		:rtype: `str`

    """
    re_text = re.sub(r'<[^>]+>', ' ', str(text))
    re_text = re.sub(' +', ' ', re_text)
    return re_text.replace("\xa0", "")


class NIHExtractor():
    """ Class which contains all the required functions to extract data from the NIH website
    """


    def __init__(self, urls, data, save_filename):
        """ Constructor
        
        :param urls: Array of URLs from which proposal data need to be extracted
        :type urls: `numpy.ndarray`
        :param data: List of URLs from which proposal data need to be extracted
        :type data: class `Pandas.DataFrame`
        :param save_filename: Filename to save the extracted NIH data
        :type save_filename: `str`
        
        :return: None

        """

        self.urls = urls
        self.main_data = data
        self.save_filename = save_filename

    def get_response(self, url):
        """ Function to retrieve response from NIH page. The processed response will be save as self.soup

        :param url: The URL from which response is to be retrieved
        :type url: `str`
        
        :return: Response Data
        :rtype: class `response`
        """
        payload = {}
        headers = {}
        self.response = requests.request(
            "GET", url, headers=headers, data=payload)
        response_str = self.response.text
        self.soup = BeautifulSoup(response_str, "html.parser")
        return self.response

    def get_organisation(self):
        """ Function to extract the organization details from NIH webpage. The webpage details are obtained from self.soup
        
        :return: Department 
        :rtype:  `str`
        """
        try:
            dept = self.soup.findAll(
                'div', {'class': 'col-md-8 datacolumn'})[1].getText()
            dept = ' '.join(dept.splitlines())

            if not dept == '':
                return dept
            else:
                divs = self.soup.findAll('div')
                div = self.soup.find('div',
                                     {'class': 'col-md-4 datalabel',
                                      'data-element-type': 'LINKED_ELEMENT'})
                dept = divs[divs.index(div) + 1].getText()
                dept = ' '.join(dept.splitlines())

                if not dept == '':
                    return dept
                else:
                    dept = self.soup.findAll(
                        'div', {'class': 'col-md-8 datacolumn'})[2].getText()
                    dept = ' '.join(dept.splitlines())

                    if not dept == '':
                        return dept
        except BaseException:
            return dept

    def get_description(self):
        """ Function to extract the Description from NIH webpage. The webpage details are obtained from self.soup
        
        :return: Description 
        :rtype:  `str`
        """
        try:
            divs = self.soup.find_all()
            div_1 = self.soup.find('a', {'name': '_Section_I._Funding'})
            idx1 = divs.index(div_1)

            desc = []
            for i in divs[idx1:]:
                desc.append(i.getText())
                if i.find('a', {'href': '#_Section_VIII._Other'}):
                    break
            desc = ''.join(''.join(desc).splitlines())

            return clean_text(desc)

        except BaseException:
            return ''

    def extract_page_info(self, url, i):
        """ Function to extract all details from NIH webpage.
        
        :param url: The URL from which proposal details should be extracted
        :type url: `str'
        :param i: A placeholde number for idnetifying the URL index
        :type i: `int  `

        :return: List containing 'URL',keywords for organization, keywords for description 
        :rtype: `list`
        """

        try:
            response = self.get_response(url)
            if self.get_response(url).status_code == 404:
                return [url] + [np.nan] * 2
            org = self.get_organisation()
            desc = self.get_description()
            return [url, org, desc]
        except BaseException:
            return [url] + [np.nan] * 2

    def extract_all(self, n_cores, output_path):
        """ Parent function to extract all webpage details from NIH (using URLs extracted from Grants.gov). 
        The function saves all the details to the 'save_filename' file in 'output_path'


        :param n_cores: No: of cores of CPU to be utilized for parallel processing
        :type n_cores: `int`
        :param output_path: The path where all the data is saved
        :type output_path: `str`


        :return: None
        """
        ipt = [(i, j) for i, j in zip(self.urls, range(len(self.urls)))]
        descs = []

        # TODELETE
        # ipt = ipt[:10]
        descs = parallelize(
            n_cores=n_cores,
            func=self.extract_page_info,
            arg1=ipt)

        cfp_df = pd.DataFrame(
            descs,
            columns=[
                "URL",
                "Organization",
                "Description"])
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
