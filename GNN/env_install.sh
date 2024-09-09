#!/usr/bin/env bash
# make sure command is : source HEC_GNN_env_install.sh

# install anaconda3.
# cd ~/
# wget https://repo.anaconda.com/archive/Anaconda3-2019.07-Linux-x86_64.sh
# bash Anaconda3-2019.07-Linux-x86_64.sh


source ~/.bashrc
# export TORCH_CUDA_ARCH_LIST="7.0;7.5"   # v100: 7.0; 2080ti: 7.5; titan xp: 6.1

# # make sure system cuda version is the same with pytorch cuda
# # follow the instruction of PyTorch Geometric: https://pytorch-geometric.readthedocs.io/en/latest/notes/installation.html
# export PATH=/usr/local/cuda-11.3/bin:$PATH
# export LD_LIBRARY_PATH=/usr/local/cuda-11.3/lib64:$LD_LIBRARY_PATH

# conda create -n HEC_GNN python==3.12
# conda activate HEC_GNN

# install packages for feature extraction 
conda install networkx
pip install graphviz
pip install pydot
conda install matplotlib

# make sure pytorch version >=1.4.0
conda install pytorch==2.2.0 torchvision==0.17.0 torchaudio==2.2.0 pytorch-cuda=12.1 -c pytorch -c nvidia
pip install tensorboard

# command to install pytorch geometric, please refer to the official website for latest installation.
#  https://pytorch-geometric.readthedocs.io/en/latest/notes/installation.html
CUDA=cu121
TORCH=2.2.0

conda install pyg=2.5.1 -c pyg
pip install pyg_lib torch_scatter torch_sparse torch_cluster torch_spline_conv -f https://data.pyg.org/whl/torch-${TORCH}+${CUDA}.html 
# pip3 install torch-scatter -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html
# pip3 install torch-sparse -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html
# if error,please try:
# pip3 install torch-scatter==2.0.6
# pip3 install torch-sparse==0.6.9

# pip3 install torch-geometric==1.6.3


# pip install torch-cluster -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html
# pip install torch-spline-conv -f https://pytorch-geometric.com/whl/torch-${TORCH}+${CUDA}.html

pip install requests

# install useful modules
pip install tqdm

# additional package required for ogb experiments
pip install ogb
### check the version of ogb installed, if it is not the latest
python -c "import ogb; print(ogb.__version__)"
# please update the version by running
pip install -U ogb

# additional package required for dgl implementation
# pip install dgl-cu102
