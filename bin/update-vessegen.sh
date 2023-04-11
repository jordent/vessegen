#!/bin/bash

if [[ $(git fetch) ]]; then
    git pull
    ./bin/install-vessegen.sh
    ./bin/install-desktop.sh
else
    echo "No updates available."
fi