mysql --user root --execute 'DROP DATABASE IF EXISTS greenday_v2'
mysql --user root --execute 'CREATE DATABASE greenday_v2 CHARACTER SET utf8 COLLATE utf8_general_ci'
mysql --user root --execute 'GRANT ALL PRIVILEGES ON greenday_v2.* TO greenday@localhost IDENTIFIED BY ""'
./bin/manage.py migrate --settings=greenday_core.settings.local --noinput
./bin/manage.py loaddata data.json
./bin/manage.py generate_videos --project_id=1 --channel_id=sirianews --number=50 --tag_ids=1,2,3,4,5,6,7,8,9,10
./bin/manage.py generate_videos --project_id=1 --channel_id=warleak --number=50 --tag_ids=6,7,8,9,10
./bin/manage.py generate_videos --project_id=1 --channel_id=MNFIRAQ --number=50 --tag_ids=1,2,3,4,5
./bin/manage.py generate_videos --project_id=1 --playlist_id=PL79_lTaZCAa7XP7iXrZPD_EXof4r5VQuh --number=50
./bin/manage.py generate_videos --project_id=2 --channel_id=SwindonTownFC007 --number=50 --tag_ids=11,12,13,14,15
./bin/manage.py syncsearchdocs --settings=greenday_core.settings.local
