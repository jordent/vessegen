#!/bin/bash

git fetch
status=($(git status | grep "branch is behind"))
if [[ "$status" ]]; then
    echo "Updates found, installing updates..."
    git pull
    sudo chmod +x ./bin/*
    ./bin/install-vessegen.sh
    ./bin/install-desktop.sh
else
    echo "No updates available."
fi