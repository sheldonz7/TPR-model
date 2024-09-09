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


dataset_path = "./raw"


graph_path = dataset_path + "/graphs"


vivado_run_status_file = "./raw/pragma_file/custom_coloring_vivado_run_status.csv"




allowable_features = {
    'possible_opcode_list': [
        'load', 'store',
        'lshift', 'rshift', 'bit_ior', 'bit_and',
        'plus', 'ternary-plus' 'mult',
        'float', 'convert', 'nop',
        'return', 'switch_cond', 'read_cond', 'multi_read_cond', 'cond',
        'phi', 'eq', 'ne', 'gt', 'lt', 'pointer-plus', 'addr', 'assign', 'extract_bit',
        'fmul','fadd',
        'misc'
    ],
    'opcode_category': ['memory','bitwise','arithmetic','control','conversion','function','other', 'misc'],
    'bitwidth': list(range(0, 256)) + ['misc'],
    'is_start_of_path': [0, 1, 'misc'],
    
    # 'LUT': list(range(0, 1000)) ,

    'possible_edge_type_list': [2,4,8] # 2: compatibility, 4: data-flow, 8: control-flow
}



def expr_to_opcode(node_name):
    if node_name in {'LOAD', 'STORE', 'ASSIGN', 'READ_COND', 'MULTI_READ_COND'}:
        # return lower case
        return node_name.lower()
    # check
    if node_name.endswith("expr"):
        return node_name.split("_")[:-1]
    # check if node_name starts with '__'
    if node_name == "__float_mule8m23b_127nih":
        return "fmul"
    if node_name == "__float_addes8m23b_127nih":
        return "fadd"
    if node_name.startswith("gimple"):
        return node_name.split("_")[1]
    return node_name


def safe_index(l, e):
    """
    Return index of element e in list l. If e is not present, return the last index
    """
    try:
        return l.index(e)
    except:
        return len(l) - 1


def opcode_type(opcode):
    if opcode in {'load', 'store'}:
        return 'memory'
    if opcode in {'lshift', 'rshift', 'bit_ior', 'bit_and'}:
        return 'bitwise'
    if opcode in {'plus', 'ternary-plus' 'mult'}:
        return 'arithmetic'
    if opcode in {'float', 'convert', 'nop',}:
        return 'conversion'
    if opcode in {'return', 'switch_cond', 'read_cond', 'multi_read_cond', 'cond'}:
        return 'control'
    if opcode in {'phi', 'eq', 'ne', 'gt', 'lt', 'pointer-plus', 'addr', 'assign', 'extract_bit'}:
        return 'other'
    if opcode in {'fmul','fadd'}:
        return 'function'

    
    return 'misc'


def node_to_feature_vector(node):
    """
    Converts node object to feature list of indices
    :return: list
    """

    if node=={}:
        node_feature = [
      #          len(allowable_features['node_category'])-1,
                len(allowable_features['bitwidth'])-1,
                len(allowable_features['opcode_category'])-1,
                len(allowable_features['possible_opcode_list'])-1,
                len(allowable_features['possible_is_start_of_path'])-1,
       #         len(allowable_features['possible_is_LCDnode'])-1,
        #        len(allowable_features['possible_cluster_group_num'])-1,
                len(allowable_features['LUT'])-1,
        #        len(allowable_features['DSP'])-1,
        #        len(allowable_features['FF'])-1
                ]
        return node_feature
        
    if node['category']=='nodes':
        node_feature = [
        #        safe_index(allowable_features['node_category'], node['category']),
                safe_index(allowable_features['bitwidth'], int(node['bitwidth'])),
                safe_index(allowable_features['opcode_category'], opcode_type(node['opcode'])),
                safe_index(allowable_features['possible_opcode_list'], node['opcode']),
                safe_index(allowable_features['possible_is_start_of_path'], int(node['m_isStartOfPath'])),
       #         safe_index(allowable_features['possible_is_LCDnode'], int(node['m_isLCDNode'])),
        #        safe_index(allowable_features['possible_cluster_group_num'], int(node['m_clusterGroupNumber'])),
                safe_index(allowable_features['LUT'], int(node['LUT'])),
        #        safe_index(allowable_features['DSP'], int(node['DSP'])),
        #        safe_index(allowable_features['FF'], int(node['FF']))
                ]
    elif node['category']=='ports':
        node_feature = [
        #        safe_index(allowable_features['node_category'], node['category']),
                safe_index(allowable_features['bitwidth'], int(node['bitwidth'])),
                len(allowable_features['opcode_category'])-1,
                len(allowable_features['possible_opcode_list'])-1,
                len(allowable_features['possible_is_start_of_path'])-1,
         #       len(allowable_features['possible_is_LCDnode'])-1,
         #       len(allowable_features['possible_cluster_group_num'])-1,
                len(allowable_features['LUT'])-1,
          #      len(allowable_features['DSP'])-1,
          #      len(allowable_features['FF'])-1
                ]
    elif node['category']=='blocks':
        node_feature = [
       #         safe_index(allowable_features['node_category'], node['category']),
                len(allowable_features['bitwidth'])-1,
                len(allowable_features['opcode_category'])-1,
                len(allowable_features['possible_opcode_list'])-1,
                len(allowable_features['possible_is_start_of_path'])-1,
        #        len(allowable_features['possible_is_LCDnode'])-1,
        #        len(allowable_features['possible_cluster_group_num'])-1,
                len(allowable_features['LUT'])-1,
        #        len(allowable_features['DSP'])-1,
        #        len(allowable_features['FF'])-1
                ]
    return node_feature

def get_node_feature_dims():
    return list(map(len, [
#        allowable_features['node_category'],
        allowable_features['bitwidth'],
        allowable_features['opcode_category'],
        allowable_features['possible_opcode_list'],
        allowable_features['possible_is_start_of_path'],
 #       allowable_features['possible_is_LCDnode'],
  #      allowable_features['possible_cluster_group_num'],
        allowable_features['LUT'],
   #     allowable_features['DSP'],
    #    allowable_features['FF'],
        ]))



def filter_compatibility_edge(coloring_file, cdfg_file, filtered_cdfg_file):
    output_file = open(filtered_cdfg_file, "w")
    cdfg_file = open(cdfg_file, "r")
    coloring_file = open(coloring_file, "r")

    coloring_csv = pd.read_csv(coloring_file)






def feature_embed(cdfg_file, out_dir):



    CDFG = nx.DiGraph(nx.drawing.nx_agraph.read_dot(cdfg_file))
    #CDFG = nx.DiGraph(nx.drawing.nx_pydot.read_dot(cdfg_file))
    print("CDFG: ", CDFG)

    # print all nodes
    # print("Nodes of CDFG: ")
    # print(CDFG.nodes())

    # # print all edges
    # print("Edges of CDFG: ")
    # print(CDFG.edges())



def run_routine(graph_list):
    

    for prj_name in graph_list:

        


        feature_embed()



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

    feature_embed("./raw/graphs/atax_io1_l1n1n1_l3n1n1/cdfg_0_copy.dot", "")