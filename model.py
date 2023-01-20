import os
import re
import ast
import sys
import json
import yaml

import requests
import argparse

from datetime import datetime
import pandas as pd
import numpy as np

from helpers import *
from automatic_keyword_generator import *

from collections import Counter
import math

import pdb


def get_column_names():

    feat_cols = [
        'Keywords',
        'Overview',
        'Organization',
        'pub_keyword',
        'pub_title']
    cfp = ["desc", "title", "dept"]
    return [i + "_" + j + "_sim" for i in feat_cols for j in cfp]


class Top_Scholar_Identifier():
    """This is a class to identify the top N scholars for a given proposal. 
    The proposal dataset created using 'main_extractor.py' will be utilized to get details of the proposal / grant. 
    The analytical dataset of user-publications created using 'create_analytical_data.py' will be utilized to get scholar profiles.
    """

    def __init__(self, n_cores, id_no, top_k, generator_, agency, params):
        """ Constructor

        :param n_cores: No: of CPU cores to be used for the process
        :type n_cores: `int`
        :param id_no: Opportunity Number of the proposal
        :type id_no: `str`
        :param top_k: The number of scholars to be recommended
        :type top_k: `int`
        :param generator_: The generator to be used for keyword extraction
        :type generator_: `str`
        :param agency: The agency which is awarding the grant
        :type agency: `str`      
        :param params: Parameters read from the configuration file
        :type params: `dict`     
        
        """

        # Set the parameters
        self.n_cores = params['CPU_COUNT'] if n_cores == 0 else n_cores
        # self.output_path = params['OUTPUT_PATH']
        self.output_path = os.path.dirname(os.path.abspath(__file__)) + '/' + params['OUTPUT_PATH']
        self.id_no = params['PROPOSAL_ID'] if id_no == '' else id_no
        self.top_k = params['top_k_scholars'] if top_k == 0 else top_k
        self.generator_ = generator_
        agency_map = {
            'NSF': 'National Science Foundation',
            'nsf': 'National Science Foundation',
            'nih': 'National Institutes of Health',
            'NIH': 'National Institutes of Health'}
        self.proposal_data_file = os.path.join(
            self.output_path, params['AGENCIES_EXTRACTED_FILENAME_DICT'][agency_map[agency]])
        self.analytical_filename = params["ANALYTICAL_DATSET"]
        self.scholars_filename = params["SCHOLARS_DATASET"]

    def read_data(self):
        """ Function which will read data from the initialized CSV files
        regarding proposal and scholar datails and save them as pandas dataframe
                
        :param None : 

        :return: None
		:rtype: 
        """

        # Read scholars' basic data
        self.user_df = pd.read_csv(
            os.path.join(
                self.output_path,
                self.scholars_filename))

        # Read scholars' publication data
        self.ad = pd.read_csv(
            os.path.join(
                self.output_path,
                self.analytical_filename))

        # Read proposal data
        self.cfp_df = pd.read_csv(self.proposal_data_file)
        self.cfp_df.fillna(" ", inplace=True)

        self.proposal = self.cfp_df[self.cfp_df["Opportunity Number"]
                                    == self.id_no].reset_index(drop=True).iloc[0]

    def get_section_keys_for_proposal(self):
        """ Function to get keywords from Description, Title adn Department sections of the proposal text
        
        :param None : 

        :return: None
		:rtype:   
        """

        # Get keys from the description of proposal
        self.desc_keys = [
            i for i in get_keys(
                self.proposal["Description"],
                generator=self.generator_,
                ntop=self.top_k) if len(i) > 3]
        # Get keys from the Title of proposal
        self.title_keys = [
            i for i in get_keys(
                self.proposal["Title"],
                generator=self.generator_,
                ntop=self.top_k) if len(i) > 3]
        # Get keys from the Department of proposal
        self.dept_keys = [
            i for i in get_keys(
                self.proposal["Department"],
                generator=self.generator_,
                ntop=self.top_k) if len(i) > 3]

    def get_top_scholars(self, ntop_=20):
        """ Main function to calculate the scholars suitable for the given proposal
        
        :param ntop_: No of scholars to be recommended
        :type ntop_: `int`
        
        :return: self.recommend_df
		:rtype: class `Pandas.DataFrame`

        """

        # Create a list of lists. Each sublist contain a user's id, his/her section keys (from analytical database), proposal's sections keys
        # That is if there are 'n' users with 'm' sentions from his profile and 'k' section in proposal, the main list will consist of 'n'*'m'*'k' sublists
        self.similarity_lists = []
        feat_cols = [
            'Keywords',
            'Overview',
            'Organization',
            'pub_keyword',
            'pub_title']

        for i in feat_cols:
            for j in [self.desc_keys, self.title_keys, self.dept_keys]:
                self.similarity_lists.append([(i, j, k) for i, j, k in zip(
                    self.ad["user_id"], self.ad[i], [j] * self.ad.shape[0])])

        # Run counter cosine similarity as parallel tasks
        self.score_lists = []
        for k in self.similarity_lists:
            sims = parallelize(
                self.n_cores,
                func=counter_cosine_similarity,
                arg1=k)
            self.score_lists.append(sims)

        self.sim_df = pd.DataFrame(
            {"user_id": [list(i.keys())[0] for i in sims]})

        col_names = get_column_names()
        for col, k in zip(col_names, range(len(col_names))):
            self.sim_df[col] = [list(i.values())[0]
                                for i in self.score_lists[k]]

        # Append the similarity values to the original dataframe
        self.sim_df["total_sim"] = self.sim_df.sum(axis=1)
        print("Max of self.sim[total_sim] :", self.sim_df["total_sim"].max())
        self.sim_df.sort_values("total_sim", ascending=False, inplace=True)
        self.sub_df = self.sim_df[:self.top_k]
        self.ids = self.sub_df["user_id"].values.tolist()

        # Create dataframe with only top scholars
        self.recommend_df = self.user_df[self.user_df["User_id"].isin(
            self.ids)]
        self.recommend_df.set_index("User_id", inplace=True)
        self.recommend_df = self.recommend_df.loc[self.ids]

        return self.recommend_df


def recommend(config_file,top_k,proposal_id,generator,cpu_count,agency,db_path,output_file):

    """ Read arguments from command line (cmd). If no input via cmd, use config
        file 
    """
    print(db_path,output_file,"db_path,output_file")
    try:
        file = db_path + config_file
        params = yaml.safe_load(open(config_file))
    except BaseException:
        print(f'Error loading parameter file: {config_file}.')
        sys.exit(1)

    # Initialize a class object with all parameters
    obj = Top_Scholar_Identifier(
        n_cores=cpu_count,
        agency=agency,
        id_no=proposal_id,
        top_k=top_k,
        generator_=generator,
        params=params)

    # Reads (CSV file) with data regarding Proposal, Scholar details and
    obj.read_data()

    # Extract keyword for proposal
    obj.get_section_keys_for_proposal()

    # Get recommendations
    recommendations = obj.get_top_scholars(ntop_=top_k)
    recommendations = recommendations.fillna('')
    
    d = []
    for index, row in recommendations.iterrows():
        scholar = {}
        scholar["Netid"], scholar["Name"], scholar["Email"] = row["Netid"], row["Name"], row["Email"]
        scholar["Type"], scholar["Keywords"] = row["Type"], row["Keywords"].replace("'", "").replace('"',"")
        scholar["n_publications"] = row["n_publications"]
        scholar["n_research"], scholar["Awards"], scholar["n_awards"] = row["n_research"], row["Awards"], row["n_awards"]
        scholar["Organizations"], scholar["Course"], scholar["Department"] = row["Organizations"], row["Course"], row["Department"]
        # print(json.loads(row["Publications"]))
        d.append(scholar)
    
    json_object = json.dumps(d, indent=4)
    json_path = os.path.dirname(os.path.abspath(__file__)) + output_file + ".json"
    # Writing to output.json
    with open(json_path, "w") as outfile:
        outfile.write(json_object)
    

    # Save the recommendation
    # save_pandas_to_csv(df=recommendations,output_path=os.path.join(obj.output_path,output_file + ".csv"),index=False)
    # recommendations_list = recommendations.values.tolist()
    
    return json_object