#!/bin/bash

if [[ $2 ]]; then
    echo "Too many arguments provided!"
else
    git fetch
    status=($(git status | grep "branch is behind"))
    if [[ "$status" ]]; then
        echo "Updates found, installing updates..."
        git pull
        sudo chmod +x ./bin/*
        ./bin/install-vessegen.sh
        if [[ $1 == "desktop" ]]; then
            ./bin/install-desktop.sh
        fi
    else
        echo "No updates available."
    fi
fi