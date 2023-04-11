#!/bin/bash

if [[ $(git fetch) ]]; then
    git pull
    sudo chmod +x ./bin/*
    ./bin/install-vessegen.sh
    ./bin/install-desktop.sh
else
    echo "No updates available."
fi