#!/bin/bash

while getopts i:u:m:s:d:c:a:r: flag
do
    case "${flag}" in
        i) server_ip=${OPTARG};; # IP address of the server
        u) server_username=${OPTARG};; # SSH user of the server
        m) mode=${OPTARG};; # prod/staging
        s) ssh_key=${OPTARG};; # ssh key
        d) base_directory=${OPTARG};; # base directory
        c) docker_container=${OPTARG};; # docker container
        a) application_name=${OPTARG};; # application name
        r) serverBaseDirectory=${OPTARG};; # server base directory
    esac
done

if [ -z $mode ];
then
    echo "Please provide application mode using parameter '-m'. The mode can either be 'prod' or 'staging'"
    exit 1
fi

if [ -z $server_ip ];
then
    echo "Please provide ip address of the server using the parameter '-i'"
    exit 1
fi

if [ -z $server_username ];
then
    echo "Please provide the ssh username of the server using the parameter '-u'"
    exit 1
fi

if [ -z $ssh_key ];
then
    echo "Please provide the ssh key path using the parameter '-s'"
    exit 1
fi

if [ -z $base_directory ];
then
    echo "Please provide the base directory path using the parameter '-d'"
    exit 1
fi

if [ -z $docker_container ];
then
    echo "Please provide the docker container name using the parameter '-c'"
    exit 1
fi

if [ -z $application_name ];
then
    echo "Please provide the application name using the parameter '-a'"
    exit 1
fi

if [ -z $serverBaseDirectory ];
then
    echo "Please provide the remote server directory using the parameter '-r'"
    exit 1
fi

echo "Running deployment script for application mode '$mode' from directory '$base_directory' to server '$server_username@$server_ip'"
# Server variables
server="$server_username@$server_ip" # Server info

# Application variables
remote_server_application_directory="/$serverBaseDirectory/$application_name"

echo "Deploying application to server $server"

# 1. If resource_management folder exists then stop the docker compose
echo "Stopping the docker container"
ssh -i $ssh_key $server "if [ -d $application_directory ]; then cd $application_directory && docker compose down; else echo 'The application directory does not exist. Not stopping the container'; fi"

# 2. Install rsync and zip  in current server. Create a zip file with timestamp as name using rsync with all contents except those of .gitignore
# echo "Installing rsync and zip"
# apt-get install rsync zip

temp_directory_name="${application_name}_$(date +%s)"

echo "Creating a zip file $temp_directory_name using rsync with all contents except the files mentioned in .gitignore"
rsync -av --exclude-from=.gitignore $base_directory/ $temp_directory_name/
# Copy env file if it exists
if [ -f "$base_directory/.env" ]; then
    echo "Copying .env file to the temp directory from $base_directory to $temp_directory_name"
    cp $base_directory/.env $temp_directory_name/
else
    echo ".env file does not exist in $base_directory"
fi
zip -r $temp_directory_name.zip $temp_directory_name/
rm -rf $temp_directory_name

# 3. Copy the zip file to the server
echo "Copying the zip file to the server"
scp -i $ssh_key $temp_directory_name.zip $server:~/$temp_directory_name.zip

# 4. Unzip the file in the server and copy content to the correct directory
echo "Unzipping the file in the server"
ssh -i $ssh_key $server "unzip $temp_directory_name.zip -d ~/"

# 5. Move the contents inside the unzipped folder to remote server application directory. Create the directory if it does not exist.
echo "Moving the contents inside the unzipped folder to remote server application directory"
ssh -i $ssh_key $server "cp ~/$temp_directory_name/* $remote_server_application_directory/ -r && cp ~/$temp_directory_name/.env $remote_server_application_directory/ -r && rm -rf ~/$temp_directory_name"

# 6. Fetch all zip files in ascending order of modified date and remove the oldest five zip files
echo "Removing oldest five zip files"
ssh -i $ssh_key $server "ls -lt --time-style=+%s ~/$application_name*.zip 2>/dev/null | sort -k6 -n | head -n 5 | awk '{print $7}' | xargs rm --"

# 7. Move docker-compose.prod.yml to docker-compose.yml
echo "Moving docker-compose.production.yml to docker-compose.yml"
ssh -i $ssh_key $server "mv $remote_server_application_directory/docker-compose.production.yml $remote_server_application_directory/docker-compose.yml"

# 8. Run migration and collectstatic for django application through docker compose
echo "Running migration and collectstatic for django application"
ssh -i $ssh_key $server "cd $remote_server_application_directory && docker compose run --rm $docker_container python manage.py migrate && docker compose run --rm $docker_container python manage.py collectstatic --noinput"

# 9. Change permission of staticfiles to publicly accessible
echo "Changing permission of staticfiles to publicly accessible"
ssh -i $ssh_key $server "sudo chmod -R 775 $remote_server_application_directory/staticfiles"

# 9. Start the docker container in application directory
echo "Starting the docker container"
ssh -i $ssh_key $server "cd $remote_server_application_directory && docker compose up --build -d"



