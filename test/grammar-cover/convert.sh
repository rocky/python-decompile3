#!/bin/bash
for VERS in 3{7,} ; do
    GRAMMAR_TXT=grammar-${VERS}.txt
    spark-parser-coverage --max-count 3000 --path spark-grammar-${VERS}.cover > $GRAMMAR_TXT
done
