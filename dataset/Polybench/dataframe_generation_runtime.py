
import pre_process_cdfg
import dataset_generation
import sys
import networkx as nx

def gen_cdfg_dataframe(data_path):

    print("pre processing CDFG")

    pre_process_cdfg.df_graph_construct(data_path)
    pre_process_cdfg.feature_embed(data_path)


    print("generating PyG dataset")

    optype_enc, opcode_enc = dataset_generation.onehot_enc_gen()

    

    CDFG = nx.MultiDiGraph(nx.drawing.nx_pydot.read_dot('{}/cdfg_0.dot'.format(data_path)))
    CDFG = nx.convert_node_labels_to_integers(CDFG)


    pyg_CDFG = dataset_generation.generate_dot(CDFG, optype_enc, opcode_enc, "{}/cdfg_pyg.dot".format(data_path))
    #ppa = dataset_generation.get_ppa('{}/perf_measure.csv'.format(data_path))
    dataset_generation.generate_dataframe(pyg_CDFG, "{}/cdfg.pt".format(data_path), False, None)

    # dataframe = torch.load('{}/pyg_pt/{}/{}_{}.pt'.format(dataset_path, kernel_name, design_point_name, prj_name))
    # dataframe_list_all[kernel_name].append(dataframe)
    print("Finish generating .pt dataframe")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 dataset_generate_runtime.py <data_path>")
        sys.exit()
    data_path = sys.argv[1]
    gen_cdfg_dataframe(data_path)