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
    'bitwidth': list(range(0, 256)),
    'opcode_category': ['memory','bitwise','arithmetic','control','conversion','other'],
    'possible_opcode_list': [

    ],
    
    'is_start_of_path': [0,1],
    
    'LUT': list(range(0, 1000)),

    'possible_edge_type_list': [2,4,8] # 2: compatibility, 4: data-flow, 8: control-flow
}






def filter_compatibility_edge(coloring_file, cdfg_file, filtered_cdfg_file):
    output_file = open(filtered_cdfg_file, "w")
    cdfg_file = open(cdfg_file, "r")
    coloring_file = open(coloring_file, "r")

    coloring_csv = pd.read_csv(coloring_file)






def feature_embed(cdfg_file, out_dir):



    #CDFG = nx.DiGraph(nx.drawing.nx_agraph.read_dot(cdfg_file))
    CDFG = nx.DiGraph(nx.drawing.nx_pydot.read_dot(cdfg_file))
    print("CDFG: ", CDFG)




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