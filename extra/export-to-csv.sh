#!/bin/bash

# “strict mode”
set +m -euo pipefail
IFS=$'\n\t '

declare DATABASE="postgresql:///flickrhistory"
declare -a TABLES=("users" "photos")
declare OUTPUT_DIRECTORY="./"

for table in "${TABLES[@]}"; do
    (
        csv_filename="$(date "+${OUTPUT_DIRECTORY}/${table}_%Y%m%d.csv.bz2")"
        echo "\COPY \"${table}\" TO STDOUT CSV HEADER;" \
            | psql "${DATABASE}" \
            | pbzip2 -c -m1000 -9 \
            >"${csv_filename}"
    )&
done
wait
