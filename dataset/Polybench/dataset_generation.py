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

numerical_item = ['bitwidth', 'LUT']
categorical_item = ['opcode', 'optype']


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



def generate_dot():




def generate_dataframe():





if __name__ == "__main__":
