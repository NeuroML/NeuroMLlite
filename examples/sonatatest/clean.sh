mkdir ~/temp/dump3
mv -v report*txt  *.dat *.spikes *.gdf *.hoc *.mod  *~ *.log *nrn.py NET_*nml *brian.py *brian2.py *h5 *nest.py *pynn.py *definition.py  *netpyne.py  *moose.py  *.nestml *.png *.ini *.svg *.pov *.gv *cell.json *synapse.json *main.json tmp* *csv *pyc ~/temp/dump3
cd network
mv -v *csv *.h5 ~/temp/dump3
rm -rf x86_64 i386 umac *.pyc *~ .*~