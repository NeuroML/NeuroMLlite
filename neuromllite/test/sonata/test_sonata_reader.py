from neuromllite.SonataReader import get_neuroml_from_sonata


def main():

    ids = ["5_cells_iclamp", "9_cells", "300_intfire", "300_cells"]
    ids += ["sim_tests/intfire/one_cell_iclamp_nest/input"]
    ids += ["sim_tests/intfire/ten_cells_iclamp_nest/input"]
    ids += ["sim_tests/intfire/ten_cells_spikes_nest/input"]
    # ids = ['sim_tests/intfire/ten_cells_spikes/input']
    # ids = ['300_cells']

    # ids = ['300_intfire']
    # ids = ['300_pointneurons','sim_tests/intfire/one_cell_iclamp/input']

    # id = '300_intfire'
    # id =
    # id = 'small_iclamp'
    ## https://github.com/pgleeson/sonata/tree/intfire

    for id in ids:
        print("***************************************************************")
        filename = "../../../../git/sonatapg/examples/%s/config.json" % id
        if "/" in id:
            id = id.split("/")[-2]

        print("****        Testing %s (%s)         \n" % (id, filename))

        nml_doc = get_neuroml_from_sonata(filename, id, generate_lems=True)

        nml_file = "%s.net.nml" % id

        from neuroml.utils import is_valid_neuroml2

        assert is_valid_neuroml2(nml_file)

        """
        nml_file_name = '%s.net.nml'%id
        nml_file_name += '.h5'

        from neuroml.writers import NeuroMLHdf5Writer
        NeuroMLHdf5Writer.write(nml_doc,nml_file_name)
        print('Written to: %s'%nml_file_name) """

    print("** Finished testing examples: %s **" % ids)


if __name__ == "__main__":
    main()
