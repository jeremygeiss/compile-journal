#!/bin/bash

# A script to create and open a daily journal file

# Create a new file path and store it in a variable
filename=$HOME/Dropbox/Writing/journals/journal_$( date '+%Y-%m-%d_%H%M' ).md

# Open the file in Neovim
nvim "$filename"
