.. RDash documentation master file, created by
   sphinx-quickstart on Fri Oct 14 14:43:07 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

RDash - Quickstart Guide
=================================

RDash is a recommendation system that captures the opportunities for pursuing external research funds through grants, contracts, and subcontracts based on the scholar’s research profile. RDash-Grants entails analyzing a massive set of solicitations and funding opportunities and selecting the most appropriate one or group of relevant grants by considering the scholar’s preferences and research profile.

RDash consists of two main components :
   - A webapp (frontend)
   - Backend
This page will provide details on the backend component of RDash which uses Natural Language Processing for recommendation.



Setup
=========


Before using the code you should first clone the repository (currently available only to Taugroup members) and install all the required libraries. This can be done through the below snippet from your command line.


.. code-block::

   git clone https://github.com/taugroup/RDASH.git
   pip install -r requirements.txt


Usage 
=========

End-to-end recommendation system can be broken down to 7 steps. Each of the steps and their corresponding code are given below. 

Step 1 : Create a list of Scholars (with demographic details and list of publications)

.. code-block::

   python user_profile_creation.py --univ_name='TAMU'

Step 2 : Create publication database - extract the information from all publications of each user

.. code-block::

   python extract_publications.py --n_cores=20

Step 3 : Create Analytical database - with representative keywords for each user

.. code-block::

   python create_analytical_data.py --n_cores=20

Step 4 : Compile list of Grants 

.. code-block::

   python extract_proposals.py 


Step 5 : Extract grant details

.. code-block::

   python main_extractor.py --n_cores=20 --a 'National Science Foundation' 'National Institutes of Health'


Step 6 : Recommend scholars for a Proposal / grant

.. code-block::

   python recommend_scholars.py --top_k=20 --proposal_id='PD-18-1263' --n_cores=20 --agency='NSF'


Step 7 : Extract proposals to a json for searching

.. code-block::

   python extract_proposals_titles_db.py



Features
==========

- The tool extracts and creates user/scholar profile using the TAMU scholars library using APIs
- Matches and recommends user profile to research proposals
- Identify similar research profiles for each scholar
- Advance Oppurtunities for Intelligent Research
- Recommend latest relevant articles/publications for literature searcha and advancement


Workflow
===========

.. image:: /images/workflow.png


Modules
=========

Below is the documentation for various python modules used in this project. 

.. toctree::
   :maxdepth: 2
   :caption: Contents:

.. include:: automatic_keyword_generator.rst

.. include:: main_extractor.rst

.. include:: extract_proposals.rst

.. include:: create_analytical_data.rst

.. include:: extract_publications.rst

.. include:: user_profile_creation.rst

.. include:: helpers.rst

.. include::index_dup.md
   :parser: myst_parser.docutils_

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
