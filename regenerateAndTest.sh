#!/bin/bash
set -ex

# pytest
cd neuromllite/test
pytest -v
cd -


# test example in multiple simulators
cd examples

rm -rf *dat *nml LEMS* x86_64 *mod *hoc

echo
echo "**** Running Example 1 ****"
python Example1.py

echo
echo "**** Running Example 2 ****"
python Example2.py
python Example2.py -nml

echo
echo "**** Running Example 3 ****"
python Example3.py
python Example3.py -netpyne
python Example3.py -jnmlnrn
python Example3.py -jnmlnetpyne
python Example3.py -eden

echo
echo "**** Running Example 4 ****"
python Example4.py
python Example4.py -netpyne
if [[ "$CI" != "true" ]]; then
    python Example4.py -pynnnest
    python Example4.py -pynnnrn
fi
#python Example4.py -pynnbrian  # Not supported in python 3...
python Example4.py -jnmlnetpyne
python Example4.py -jnmlnrn
python Example4.py -jnml
python Example4.py -sonata

echo
echo "**** Running Example 5 ****"

if [[ "$CI" != "true" ]]; then
    python Example5.py
fi
#python Example5.py -netpyne  # Takes 2-3 mins

echo
echo "**** Running Example 6 ****"
python Example6.py
python Example6.py -nml
python Example6.py -nml -noinputs

echo
echo "**** Running Example 7 ****"
python Example7.py
python Example7.py -jnmlnrn
python Example7.py -jnml
if [[ "$CI" != "true" ]]; then
    python Example7.py -pynnnest
    python Example7.py -pynnnrn
fi

echo
echo "**** Running Example 8 ****"
python Example8.py
#python Example8.py -jnmlnrn
#python Example8.py -jnml

jnml -validate *nml  # All until now should be valid...

echo
echo "**** Running Example 9 ****"
python Example9.py
python Example9.py -jnml


echo
echo "**** Running Example 10 ****"
python Example10.py
python Example10.py -jnml
python Example10.py -mdf

echo
echo "**** Running Example 11 ****"
python Example11.py
python Example11.py -jnml

echo
echo "**** Running Example 12 ****"
python Example12.py
python Example12.py -jnmlnrn

echo
echo "**** Running Arbor Example ****"
cd arbor
python ArborExample.py
python ArborExample.py -arbor


echo
echo "** All generated and tested! **"

cd ../../docs
python generate.py

cd ..
