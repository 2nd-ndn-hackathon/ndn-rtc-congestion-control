#!/bin/sh

# echo "run as $0 <log_file> <test_name> <[c1,c3,c4,c5]>"

csv="../results/day2/test$2.$3.csv"
log="../results/day2/test$2.$3.log"

echo "running analysis on $1. results are in $csv..."
./parse-scripts/analyze.py $1 5 --no-headers > "$csv"
echo "copying log $1 to $log..."
cp "$1" "$log"
echo "done!"
