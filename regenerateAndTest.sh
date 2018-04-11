set -e

cd examples

rm -rf *dat *json *nml LEMS* x86_64 *mod *hoc

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


jnml -validate *nml

echo
echo "** All generated and tested! **"

cd ..