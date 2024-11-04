#!/bin/bash

# Constants
HOME_DIR=/home/vibinjk/jobs/stosc_announcements
CODE_DIR=$HOME_DIR/announcements-slides
SCRIPT_FILE=announcement_goolge_generator.py
ENV_DIR=env/bin/activate
LOG_DIR=./logs
BASE_LOG_FILE=logfile
LOG_EXTENSION=.log

# Functions
activate_env() {
  cd $CODE_DIR
  source $ENV_DIR
}

update_code() {

  # Fetch the latest changes from the remote repository
  git fetch origin
  # Get the name of the current branch
  branch=$(git rev-parse --abbrev-ref HEAD)
  # Check if there are changes in the remote repository
  if git diff --quiet origin/$branch; then
    echo "No changes in the remote repository. Skipping git pull."
  else
    # Check if requirements.txt has changed in the remote repository
    if git diff --name-only origin/$branch | grep --quiet "requirements.txt"; then
      # Pull the changes and install the new requirements
      git pull origin $branch
      pip install -r requirements.txt
    else
      # No changes to requirements.txt, just pull the changes
      git pull origin $branch
    fi
  fi
}

start_process() {  
    #  read arguments passed to shell script
    args="$@"
    output_file="$LOG_DIR/$BASE_LOG_FILE$LOG_EXTENSION"
    # pass arguments to python script
    python3 -u ./$SCRIPT_FILE $args  >> $output_file 2>&1 
}

activate_env
update_code
start_process

# supported arguments
# --bdays           [Birthdays and anniversaries only]
# --announcements   [Announcements only]
# --images          [also generate images]