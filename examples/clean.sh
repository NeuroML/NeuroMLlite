mkdir ~/temp/dump
mv -v report*txt *.pdf *.dat *.spikes *.gdf *.pkl *.hoc *.mod  *~ *.log *nrn.py NET_*nml *brian.py *brian2.py *nest.py *pynn.py *definition.py  *netpyne.py  *moose.py  *.nestml *.png *.ini *.svg *.pov *.gv *cell.json *synapse.json *main.json tmp* *csv *mdf.json *mdf.yaml *.mdf *eden.py ~/temp/dump
rm -rf x86_64 i386 umac arm64  *.pyc *.c *.so  __pycache__ *~ .*~
rm -rf ./test_files/test_inputs/x86_64 ./test_files/x86_64 ./spikeratetest/x86_64
