set -e

cd examples

rm -rf *dat *nml LEMS* x86_64 *mod *hoc

echo
echo "**** Running Example 1 ****"
python Example1.py

echo
echo "**** Running Example 2 ****"
python Example2.py

echo
echo "**** Running Example 3 ****"
python Example3.py
python Example3.py -netpyne
python Example3.py -jnmlnrn
python Example3.py -jnmlnetpyne
python Example3.py -sonata

echo
echo "**** Running Example 4 ****"
python Example4.py
python Example4.py -pynnnest
python Example4.py -pynnnrn
python Example4.py -pynnbrian
python Example4.py -jnmlnetpyne
python Example4.py -jnmlnrn
python Example4.py -jnml

echo
echo "**** Running Example 5 ****"
python Example5.py
#python Example5.py -netpyne  # Takes 2-3 mins

echo
echo "**** Running Example 6 ****"
python Example6.py
python Example6.py -nml

echo
echo "**** Running Example 7 ****"
python Example7.py
python Example7.py -jnmlnrn
#python Example7.py -jnml

echo
echo "**** Running Example 8 ****"
python Example8.py
#python Example8.py -jnmlnrn
#python Example8.py -jnml


jnml -validate *nml

nosetests -vs

echo
echo "** All generated and tested! **"

cd ..