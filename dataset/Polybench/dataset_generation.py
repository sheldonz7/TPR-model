import os
import time
import csv
import argparse
import collections
import pathlib
import numpy as np 
import networkx as nx
import sklearn
from sklearn.preprocessing import OneHotEncoder
import torch
import torch_geometric.data
import shutil


graph_path = "./raw/graphs"
dataset_path = "./dataset_1"

numeric_item = ['bitwidth', 'lut', 'fan_in', 'fan_out']
categ_item = ['opcode', 'optype']

opcode_categ = [['load'], ['store'],
        ['lshift'], ['rshift'], ['bit_ior'], ['bit_and'],
        ['plus'], ['ternary-plus'], ['mult'],
        ['float'], ['convert'], ['nop'],
        ['return'], ['switch_cond'], ['read_cond'], ['multi_read_cond'], ['cond'],
        ['phi'], ['eq'], ['ne'], ['gt'], ['lt'], ['pointer-plus'], ['addr'], ['assign'], ['extract_bit'],
        ['fmul'],['fadd'],
        ['misc']]

optype_categ = [['memory'],['bitwise'],['arithmetic'],['control'],['conversion'],['function'],['other'], ['misc']]


def onehot_enc_gen():
    optype_enc = OneHotEncoder(handle_unknown = 'ignore')
    optype_enc.fit(optype_categ)
    opcode_enc = OneHotEncoder(handle_unknown = 'ignore')
    opcode_enc.fit(opcode_categ)
    return optype_enc, opcode_enc



def get_ppa(perf_file_path):
    with open(perf_file_path, 'r') as f:
        reader = csv.reader(f)
        # skip the first row
        next(reader)
        # read the second row
        row = next(reader)
        ppa = list([float(row[0]), float(row[1]), float(row[2]) / 1000])

    return ppa




def generate_dot(CDFG, optype_enc, opcode_enc, dot_store_path):
    print("generating dot file...")
    pyg_DG = CDFG.__class__()
    pyg_DG.add_nodes_from(CDFG)
    pyg_DG.add_edges_from(CDFG.edges)


    for nodeid in CDFG.nodes():
        node_feat = list()
        for feat_item in numeric_item:
            if feat_item not in CDFG.nodes[nodeid]:
                print("ERROR: feat_item = {}, not in nodeid = {}".format(feat_item, nodeid))
                raise AssertionError()
            else:
                if type(CDFG.nodes[nodeid][feat_item]) == int:
                    node_feat.append(int(CDFG.nodes[nodeid][feat_item]))
                elif type(CDFG.nodes[nodeid][feat_item]) == str:
                    float_val = float(CDFG.nodes[nodeid][feat_item].strip('\"'))
                    node_feat.append(float_val)
                else:
                    print("ERROR: feat_item = {}, not with type str or int, with type {}".format(feat_item, type(DG.nodes[nodeid][feat_item])))
                    raise AssertionError()

        c_optype = CDFG.nodes[nodeid]['optype']
        c_opcode = CDFG.nodes[nodeid]['opcode']
        # if c_opcode == 'fsub_fadd': c_opcode = 'fadd_fsub'
        # elif c_opcode == 'store_load': c_opcode = 'load_store'
            
        onehot_optype = optype_enc.transform([[c_optype]]).toarray()
        onehot_optype = onehot_optype.reshape(np.shape(onehot_optype)[1])
        onehot_opcode = opcode_enc.transform([[c_opcode]]).toarray()
        onehot_opcode = onehot_opcode.reshape(np.shape(onehot_opcode)[1])
        
        node_feat = np.concatenate((node_feat, onehot_optype), axis = 0)
        node_feat = np.concatenate((node_feat, onehot_opcode), axis = 0)
        pyg_DG.nodes[nodeid]['x'] = list(node_feat)

    # edge_type_dict = gen_edge_type_dict()
    for srcid, dstid in CDFG.edges():
        # pyg_DG[srcid][dstid]['edge_attr'] = [float(DG[srcid][dstid]['src_activity'].strip('\"')), float(DG[srcid][dstid]['src_act_ratio'].strip('\"')), 
        #     float(DG[srcid][dstid]['dst_activity'].strip('\"')), float(DG[srcid][dstid]['dst_act_ratio'].strip('\"'))]
        # if DG.nodes[srcid]['opcode'] in ['fadd', 'fsub', 'fsub_fadd', 'fadd_fsub', 'fmul', 'fdiv', 'fsqrt']:
        #     src_type = 'arith'
        # else:
        #     src_type = 'others'
        # if DG.nodes[dstid]['opcode'] in ['fadd', 'fsub', 'fsub_fadd', 'fadd_fsub', 'fmul', 'fdiv', 'fsqrt']:
        #     dst_type = 'arith'
        # else:
        #     dst_type = 'others'
        
        # pyg_DG[srcid][dstid]['edge_type'] = int(CDFG[srcid][dstid]['edge_type'])
        
        # get edge type from CDFG and copy it into pyg_DG
        for multi_edge_index, edge_data in CDFG[srcid][dstid].items():
            pyg_DG[srcid][dstid][multi_edge_index]['edge_type'] = int(edge_data['edge_type'])

    nx.nx_pydot.write_dot(pyg_DG, dot_store_path)
    return pyg_DG



def generate_dataframe(CDFG, df_path, if_dataset, ppa):
    print("generating dataframe...")
    data = {}

    #print(list(CDFG.edges))

    for i, (_, feat_dict) in enumerate(CDFG.nodes(data = True)):
        for key, value in feat_dict.items():
            val_list = [float(val) for val in value]
            data[str(key)] = [val_list] if i == 0 else data[str(key)] + [val_list]
                
    for i, (_, _, feat_dict) in enumerate(CDFG.edges(data = True)):
        for key, value in feat_dict.items():
            if type(value) == str:
                data[key] = [[float(value.strip('\"'))]] if i == 0 else data[key] + [[float(value.strip('\"'))]]
            elif type(value) == int:
                data[key] = [value] if i == 0 else data[key] + [value]
            elif type(value) == list:
                data[key] = [value] if i == 0 else data[key] + [value]

    # data['overall'] = [overall_attr.clock, overall_attr.max_latency, overall_attr.min_latency, overall_attr.avg_latency, 
    #     overall_attr.lut, overall_attr.ff, overall_attr.dsp, overall_attr.bram, overall_attr.sf_lut, overall_attr.sf_ff, 
    #     overall_attr.sf_dsp, overall_attr.sf_bram, overall_attr.sf_latency]
    
    # ppa is a 3-dimensional list
    if if_dataset:
        data['y'] = ppa

    for key, item in data.items():
        try:
            data[key] = torch.tensor(item)
        except ValueError:
            pass
 
    edges = [(int(u), int(v), int(key)) for u, v, key in CDFG.edges]
    #print(edges)


    edge_index = torch.LongTensor(edges).t().contiguous()
    data['edge_index'] = edge_index.view(3, -1)
    # data['kernel_name'] = kernel_name
    # data['prj_name'] = prj_name
    dataframe = torch_geometric.data.Data.from_dict(data)
    dataframe.num_nodes = CDFG.number_of_nodes()
    torch.save(dataframe, df_path)

    return dataframe


def print_graph(graph):
    # Print all nodes and their attributes
    print("Nodes of CDFG: ")
    for node, data in graph.nodes(data=True):
        print(f"Node: {node}, Data: {data}")

    # Print all edges and their attributes
    print("Edges of CDFG: ")
    for u, v, data in graph.edges(data=True):
        print(f"Edge from {u} to {v}, Data: {data}")

if __name__ == "__main__":
    optype_enc, opcode_enc = onehot_enc_gen()

    design_list = next(os.walk(graph_path))[1]
    dataframe_list_all = dict()

    # clear old dataset
    if os.path.exists(dataset_path):
        shutil.rmtree(dataset_path)
    os.mkdir(dataset_path)
    os.mkdir(dataset_path + '/pyg_pt')
    os.mkdir(dataset_path + '/dot')

    graph_path_test_subset = ["atax_io1_l1n1n1_l3n1n1"]
    coloring_solution_test_subset = ["coloring_0"]

    for i, design_point_name in enumerate(os.listdir(graph_path)):
    # for i, design_point_name in enumerate(graph_path_test_subset):
        print("processing design point {}".format(design_point_name))
        kernel_name = design_point_name.split('_')[0]

        if not os.path.exists(dataset_path + '/pyg_pt/' + kernel_name):
            os.mkdir(dataset_path + '/pyg_pt/' + kernel_name)
        
        if not os.path.exists(dataset_path + '/dot/' + kernel_name):
            os.mkdir(dataset_path + '/dot/' + kernel_name)

        if dataframe_list_all.get(kernel_name) is None:
            dataframe_list_all[kernel_name] = list()

        for j, prj_name in enumerate(os.listdir(graph_path + '/' + design_point_name)):
        #for j, prj_name in enumerate(coloring_solution_test_subset):
            print("processing project {}".format(prj_name))
            if not os.path.exists("{}/{}/{}/cdfg_0.dot".format(graph_path, design_point_name, prj_name)):
                print("No cdfg file in {} folder".format(prj_name))
                continue
            
            CDFG = nx.MultiDiGraph(nx.drawing.nx_pydot.read_dot('{}/{}/{}/cdfg_0.dot'.format(graph_path, design_point_name, prj_name)))
            CDFG = nx.convert_node_labels_to_integers(CDFG)
            #print(CDFG.edges)
            # pyg_DG = CDFG.__class__()
            # pyg_DG.add_nodes_from(CDFG)
            # pyg_DG.add_edges_from(CDFG.edges)
            # for srcid, dstid in pyg_DG.edges():
            #     print("edge from {} to {}".format(srcid, dstid))
            #     print(pyg_DG[srcid][dstid])
            # for srcid, dstid in CDFG.edges():
            #     print("edge from {} to {}".format(srcid, dstid))
            #     print(CDFG[srcid][dstid])
            pyg_CDFG = generate_dot(CDFG, optype_enc, opcode_enc, "{}/dot/{}/{}_{}.dot".format(dataset_path, kernel_name, design_point_name, prj_name))
            ppa = get_ppa('{}/{}/{}/perf_measure.csv'.format(graph_path, design_point_name, prj_name))
            generate_dataframe(pyg_CDFG, ppa, "{}/pyg_pt/{}/{}_{}.pt".format(dataset_path, kernel_name, design_point_name, prj_name))

            dataframe = torch.load('{}/pyg_pt/{}/{}_{}.pt'.format(dataset_path, kernel_name, design_point_name, prj_name))
            dataframe_list_all[kernel_name].append(dataframe)
            print("processed {} {}".format(design_point_name, prj_name))
    
    # iterate through dataframe_list dictionary
    for kernel_name, dataframe_list in dataframe_list_all.items():

        
        torch.save(dataframe_list, '{}/pyg_pt/{}.pt'.format(dataset_path, kernel_name))

                   
        
        
  