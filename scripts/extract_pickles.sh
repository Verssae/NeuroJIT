#!/bin/sh

if [ -d "/app/data/pickles" ] && [ "$(ls -A /app/data/pickles)" ]; then
    echo "Pickles directory already exists and is not empty. Skipping extraction."
else
    echo "Extracting pickles..."
    cat /app/archive/pickles_part_* > /app/pickles.tar.gz && tar --warning=no-unknown-keyword -xzf /app/pickles.tar.gz -C /app
    echo "Done."
fi