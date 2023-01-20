echo ‘Creating Datasets’
/usr/bin/bash /usr/src/app/bash_file.sh
echo ‘Completed Dataset creation’
echo ‘Starting Cron Job’
cron
echo ‘Cron Job started’
echo ‘Starting Flask’
flask run --host=0.0.0.0 --port=9000