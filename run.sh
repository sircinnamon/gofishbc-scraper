#!/bin/bash

hashseed=274965444
at=$(cat .pb_token)
PYTHONHASHSEED=$hashseed PB_ACCESS_TOKEN="$at" python3 main.py