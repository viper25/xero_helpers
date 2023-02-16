#!/bin/bash
cd /home/azureuser/jobs/stosc_xero_member_contributions/
source .env/bin/activate

# virtualenv is now active, which means your PATH has been modified.
# Don't try to run python from /usr/bin/python, just run "python" and
# let the PATH figure out which version to run (based on what your
# virtualenv has configured).
python member_contribution.py
