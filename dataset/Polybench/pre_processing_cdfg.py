import subprocess
import os
import sys
import io
import shutil
from pathlib import Path
import time

import networkx as nx
import graphviz as gvz
import pandas as pd
import csv

from sklearn.preprocessing import OneHotEncoder
import extract_vivado_info as vivado_info

dataset_path = "./raw"


graph_path = dataset_path + "/graphs"

pragma_file_path = dataset_path + "/pragma_file"

vivado_run_status_file = "./raw/pragma_file/custom_coloring_vivado_run_status.csv"







is_start_of_path = [0, 1, 'misc']
    
    # 'LUT': list(range(0, 1000)) ,

possible_edge_type_list = [2,4,8] # 2: compatibility, 4: data-flow, 8: control-flow




def expr_to_opcode(node_name):
    if node_name in {'LOAD', 'STORE', 'ASSIGN', 'READ_COND', 'MULTI_READ_COND'}:
        # return lower case
        return node_name.lower()
    # check
    if node_name.endswith("expr"):
        return "_".join(node_name.split("_")[:-1])
    # check if node_name starts with '__'
    if node_name == "__float_mule8m23b_127nih":
        return "fmul"
    if node_name == "__float_adde8m23b_127nih":
        return "fadd"
    if node_name.startswith("gimple"):
        return node_name.split("_")[1]
    return node_name



def opcode_get_type(opcode):
    if opcode in {'load', 'store'}:
        return 'memory'
    if opcode in {'lshift', 'rshift', 'bit_ior', 'bit_and'}:
        return 'bitwise'
    if opcode in {'plus', 'ternary-plus', 'mult'}:
        return 'arithmetic'
    if opcode in {'float', 'convert', 'nop',}:
        return 'conversion'
    if opcode in {'return', 'switch_cond', 'read_cond', 'multi_read_cond', 'cond'}:
        return 'control'
    if opcode in {'phi', 'eq', 'ne', 'gt', 'lt', 'pointer_plus', 'addr', 'assign', 'extract_bit'}:
        return 'other'
    if opcode in {'fmul','fadd'}:
        return 'function'

    
    return 'misc'




def set_graph_node_info(DG, nodeid, **kwargs): 
    graph_node = DG.nodes[nodeid]
    for attr_name in kwargs:
        graph_node[attr_name] = kwargs[attr_name]

def cdfg_attribute_filter(CDFG_raw, CDFG, coloring_file):
    node_attr_to_keep = ["node_id", "bitwidth", "resource_area"]
    edge_attr_to_keep = ['edge_type']  # should be "type"


    # Add filtered node attributes to the new graph
    for node, data in CDFG_raw.nodes(data=True):
        opcode = expr_to_opcode(data.get("opcode", None))
        #print("node: ", node)
        #print("raw opcode: ", data.get("opcode", None))
        #print("get opcode: ", opcode)
        optype = opcode_get_type(opcode)
        bitwidth = data.get("bitwidth", None)
        lut = data.get("resource_area", None)
        CDFG.add_node(node, node_id=data.get("node_id", None), opcode=opcode,optype=optype,bitwidth=bitwidth,lut=lut)
        

    # Add filtered edge attributes to the new graph
    coloring_solution = pd.read_csv(coloring_file)
    first_column = coloring_solution.iloc[:, 0]
    third_column = coloring_solution.iloc[:, 2]
    
    # construct a dictionary to store first column and third column map, with value converted to int
    node_color_map = dict(zip(first_column, third_column))
    
    # print(type(node_color_map))
    # print("node and color map: ", node_color_map)
    
    for u,v,data in CDFG_raw.edges(data=True):
        edge_type=data.get("edge_type", None)
        # print("u type:", type(u))
        # print("edge_type:", edge_type)
        # check compatibility
        if edge_type == '2':
            # print("src node {} color: {}".format(u, node_color_map.get(u, None)))
            # print("dst node {} color: {}".format(v, node_color_map.get(v, None))) 
            if node_color_map.get(int(u), None) != node_color_map.get(int(v), None):
            
                #print("compatibility not detected, not adding the edge")
                continue
        #print("add edge of type {} between {} and {}".format(edge_type, u, v))
        CDFG.add_edge(u,v, edge_type=edge_type)

# feature computation
def fan_in_out_compute(DG):
    for nodeid in DG.nodes:
        # only look at edge with edge_type = 8
        fan_in_edges = [edge for edge in DG.in_edges(nodeid, data=True) if edge[2].get('edge_type', None) == '4']
        DG.nodes[nodeid]['fan_in'] = len(list(fan_in_edges))
        fan_out_edges = [edge for edge in DG.out_edges(nodeid, data=True) if edge[2].get('edge_type', None) == '4']
        DG.nodes[nodeid]['fan_out'] = len(list(fan_out_edges))


def check_start_of_path(DG):
    for nodeid in DG.nodes:
        if DG.nodes[nodeid]['fan_in'] == 0 and DG.nodes[nodeid]['fan_out'] > 0:
            DG.nodes[nodeid]['start_of_path'] = 1
        else:
            DG.nodes[nodeid]['start_of_path'] = 0
            
    return

def graph_node_feat_to_file(out_dir, CDFG):
    with open('{}/graph_node_feature.csv'.format(out_dir), 'w+', newline = '') as wfile:
        writer = csv.writer(wfile)
        title = ['nodeid', 'node_id', 'optype', 'opcode', 'bitwidth', 'fan_in', 'fan_out', 'lut']
        writer.writerow(title)
        for nodeid, data in CDFG.nodes(data=True):
            wr_line = [nodeid]
            for val_name in title[1:]:
                if val_name in data:
                    if type(data[val_name]) == str:
                        c_val = data[val_name].strip('\"')
                    else:
                        c_val = data[val_name]
                else:
                    c_val = 0
                wr_line += [c_val]
            writer.writerow(wr_line)


def graph_edge_feat_to_file(out_dir, CDFG):
    with open('{}/graph_edge_feature.csv'.format(out_dir), 'w+', newline = '') as wfile:
        writer = csv.writer(wfile)
        title = ['src_id', 'dst_id', 'edge_type']
        writer.writerow(title)
        for u, v, data in CDFG.edges(data=True):
            wr_line = [u, v]
            for val_name in title[2:]:
                if val_name in data:
                    if type(data[val_name]) == str:
                        c_val = data[val_name].strip('\"')
                    else:
                        c_val = data[val_name]
                else:
                    c_val = 0
                wr_line += [c_val]
            writer.writerow(wr_line)

def feature_embed(cdfg_dir):
    #CDFG = nx.DiGraph(nx.drawing.nx_agraph.read_dot(cdfg_file))
    # CDFG_raw = nx.DiGraph(nx.drawing.nx_pydot.read_dot(cdfg_file))
    # CDFG = CDFG_raw.copy()
    # print("CDFG copy: ", CDFG)
    CDFG = CDFG_raw = nx.MultiDiGraph(nx.drawing.nx_pydot.read_dot("{}/cdfg_filtered.dot".format(cdfg_dir)))

    fan_in_out_compute(CDFG)
    check_start_of_path(CDFG)

    
    #print("CDFG after fan in out compute: ")
    #print_graph(CDFG)
    
    graph_node_feat_to_file(cdfg_dir, CDFG)
    graph_edge_feat_to_file(cdfg_dir, CDFG)

    nx.nx_pydot.write_dot(CDFG, "{}/cdfg_0.dot".format(cdfg_dir))



    # # Print all nodes and their attributes
    # print("Nodes of CDFG: ")
    # for node, data in CDFG.nodes(data=True):
    #     print(f"Node: {node}, Data: {data}")

    # # Print all edges and their attributes
    # print("Edges of CDFG: ")
    # for u, v, data in CDFG.edges(data=True):
    #     print(f"Edge from {u} to {v}, Data: {data}")




def print_graph(graph):
    # Print all nodes and their attributes
    print("Nodes of CDFG: ")
    for node, data in graph.nodes(data=True):
        print(f"Node: {node}, Data: {data}")

    # Print all edges and their attributes
    print("Edges of CDFG: ")
    for u, v, data in graph.edges(data=True):
        print(f"Edge from {u} to {v}, Data: {data}")

# def run_routine(graph_list):
    

#     for prj_name in graph_list:

        


#         feature_embed()



def df_graph_construct(cdfg_dir):
    CDFG_raw = nx.MultiDiGraph(nx.drawing.nx_pydot.read_dot("{}/cdfg_raw.dot".format(cdfg_dir)))
    CDFG = nx.MultiDiGraph()
    #print("CDFG")
    #print_graph(CDFG_raw)
    
    cdfg_attribute_filter(CDFG_raw, CDFG, "{}/coloring.csv".format(cdfg_dir))
    #print("CDFG after attribute filtering")
    #print_graph(CDFG)
    # cdfg_compatibility_filter(CDFG, coloring_file)
    # print_graph(CDFG)

    #################
    # other pre-processing steps that we currently do not have


    #################

    #CDFG = nx.convert_node_labels_to_integers(CDFG)

    nx.nx_pydot.write_dot(CDFG, "{}/cdfg_filtered.dot".format(cdfg_dir))







def extract_cdfg():
    vivado_run_status = pd.read_csv(vivado_run_status_file)
    first_column = vivado_run_status.iloc[:, 0]
    second_column = vivado_run_status.iloc[:, 1]
    sixth_column = vivado_run_status.iloc[:, 5]



    if not os.path.exists(graph_path):
        os.makedirs(graph_path)

    for design_point_name, coloring_solution_name, vivado_run_success in zip(first_column, second_column, sixth_column):
        # if not vivado_run_success:
        #     continue
        design_name = design_point_name.split("_")[0]
        bambu_run_path = "{}/{}/{}".format(pragma_file_path, design_point_name, coloring_solution_name + "_bambu_run")
            
        if not os.path.exists(bambu_run_path):
            print("skip {}".format(bambu_run_path))
        
        
        if not os.path.exists("{}/{}".format(graph_path, design_point_name)):
            os.makedirs("{}/{}".format(graph_path, design_point_name))

        if not os.path.exists("{}/{}/{}".format(graph_path, design_point_name, coloring_solution_name)):
            os.mkdir("{}/{}/{}".format(graph_path, design_point_name, coloring_solution_name))

        shutil.copy("{}/{}_cdfg_bulk_graph.dot".format(bambu_run_path,design_name), "{}/{}/{}/cdfg_raw.dot".format(graph_path, design_point_name, coloring_solution_name))
        shutil.copy("{}/coloring_result.csv".format(bambu_run_path), "{}/{}/{}/coloring.csv".format(graph_path, design_point_name, coloring_solution_name))
        f = open("trash.csv", "a")

        vivado_info.extract_perf(10, bambu_run_path, f)
        f.close()
        shutil.copy("{}/perf_measure.csv".format(bambu_run_path), "{}/{}/{}/perf_measure.csv".format(graph_path, design_point_name, coloring_solution_name))
if __name__ == "__main__":

    # read vivado_run_status_file
    vivado_run_status = pd.read_csv(vivado_run_status_file)
    first_column = vivado_run_status.iloc[:, 0]
    second_column = vivado_run_status.iloc[:, 1]
    sixth_column = vivado_run_status.iloc[:, 5]
    




    # for design_point_name, coloring_solution_name, vivado_run_success in zip(first_column, second_column, sixth_column):
    #     if not vivado_run_success:
    #         continue
        
    #     coloring_index = coloring_solution_name.split("_")[-1]

    #     print("Generate data for design point {} {}".format(design_point_name, coloring_solution_name))
    #     cdfg_file = "{}/{}/cdfg_{}.dot".format(graph_path, design_point_name, coloring_index)
    #     coloring_file = "{}/{}/cdfg_{}_coloring.csv".format(graph_path, design_point_name, coloring_index)
    #     perf_file = "{}/{}/cdfg_{}perf_measure.csv".format(graph_path, design_point_name, coloring_index)
    #     filtered_cdfg_file = "{}/{}/cdfg_{}_filtered.dot".format(graph_path, design_point_name, coloring_index)
        

    #     filter_compatibility_edge(coloring_file, cdfg_file, filtered_cdfg_file)
    # run_routine()
    # extract_cdfg()

    for design_point_name, coloring_solution_name, vivado_run_success in zip(first_column, second_column, sixth_column):
        # if not vivado_run_success:
        #     continue
        
        # extract vivado info + copy files into graph path

        print("pre processing design point {} {}".format(design_point_name, coloring_solution_name))

        df_graph_construct("{}/{}/{}".format(graph_path, design_point_name, coloring_solution_name))
        feature_embed("{}/{}/{}".format(graph_path, design_point_name, coloring_solution_name))

   # df_graph_construct("{}/{}/{}".format(graph_path, "atax_io1_l1n1n1_l3n1n1", "coloring_60"))
    #feature_embed("{}/{}/{}".format(graph_path, "atax_io1_l1n1n1_l3n1n1", "coloring_60"))