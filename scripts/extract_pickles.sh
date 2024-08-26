#!/bin/sh

echo "Extracting pickles..."
cat /app/archive/pickles_part_* > /app/pickles.tar.gz && tar --warning=no-unknown-keyword -xzf /app/pickles.tar.gz -C /app
echo ls /app/data
echo "Done."