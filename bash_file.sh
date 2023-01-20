/usr/bin/python3 /usr/src/app/user_profile_creation.py >  /usr/src/app/stdout/user_profile_creation.txt
/usr/bin/python3 /usr/src/app/extract_publications.py >  /usr/src/app/stdout/extract_publications.txt
/usr/bin/python3 /usr/src/app/create_analytical_data.py >  /usr/src/app/stdout/create_analytical_data.txt
/usr/bin/python3 /usr/src/app/extract_proposals.py  --config=/usr/src/app/config.yml > /usr/src/app/stdout/extract_proposals.txt
/usr/bin/python3 /usr/src/app/main_extractor.py  --config=/usr/src/app/config.yml >  /usr/src/app/stdout/main_extractor.txt
/usr/bin/python3 /usr/src/app/extract_proposals_titles_db.py > /usr/src/app/stdout/extract_proposals_titles_db.txt
