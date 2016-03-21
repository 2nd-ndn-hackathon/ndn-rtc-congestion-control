#!/bin/sh

echo "run as $0 <log_file> <test_name> <[c1,c3,c4,c5]>

./parse-scripts/analyze.py $1 5 --no-headers > ../results/day2/test$2.$3.csv
cp $1 ../results/day2/tes$2.$3.log
