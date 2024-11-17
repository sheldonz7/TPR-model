
import pre_process_cdfg
import dataset_generation
import sys
import networkx as nx
import time

def gen_cdfg_dataframe(CDFG_raw, coloring_file_path):

    print("pre processing CDFG")

    start = time.time()
    cdfg_filtered = pre_process_cdfg.df_graph_construct(CDFG_raw, coloring_file_path)
    end = time.time()
    print("Time taken to filter cdfg: ", end - start)
    start = time.time()
    CDFG_embedded = pre_process_cdfg.feature_embed(cdfg_filtered)
    end = time.time()
    print("Time taken to embed features: ", end - start)

    print("generating PyG dataset")

    optype_enc, opcode_enc = dataset_generation.onehot_enc_gen()

    # start = time.time()
    # nx.drawing.nx_pydot.read_dot('{}/cdfg_0.dot'.format(data_path))
    # end = time.time()
    # print("Time taken to read cdfg: ", end - start)

    start = time.time()
    #CDFG= nx.MultiDiGraph(nx.drawing.nx_pydot.read_dot('{}/cdfg_0.dot'.format(data_path)))
    CDFG_embedded = nx.convert_node_labels_to_integers(CDFG_embedded)
    end = time.time()
    print("Time taken to read cdfg: ", end - start)




    start = time.time()
    pyg_CDFG = dataset_generation.generate_dot(CDFG_embedded, optype_enc, opcode_enc, "{}/cdfg_pyg.dot".format(data_path))
    end = time.time()
    print("Time taken to generate dot: ", end - start)
    #ppa = dataset_generation.get_ppa('{}/perf_measure.csv'.format(data_path))
    start = time.time()
    dataset_generation.generate_dataframe(pyg_CDFG, "{}/cdfg.pt".format(data_path), False, None)
    end = time.time()
    print("Time taken to generate dataframe: ", end - start)

    # dataframe = torch.load('{}/pyg_pt/{}/{}_{}.pt'.format(dataset_path, kernel_name, design_point_name, prj_name))
    # dataframe_list_all[kernel_name].append(dataframe)
    print("Finish generating .pt dataframe")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 dataset_generate_runtime.py <data_path>")
        sys.exit()
    data_path = sys.argv[1]
    coloring_file_path = "{}/coloring.csv".format(data_path)
    CDFG_raw = nx.MultiDiGraph(nx.drawing.nx_pydot.read_dot("{}/cdfg_raw.dot".format(data_path)))
    gen_cdfg_dataframe(CDFG_raw, coloring_file_path)