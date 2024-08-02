# Panda-bambu installation tips
for linux Docker container, to be able to debug Bambu:
docker run -it --shm-size=8gb --gpus all -v $HOME/workspace/:/workspace/ --security-opt seccomp=unconfined --cap-add=SYS_PTRACE --name bambu-debug bambu-env


# docker instruction
docker run -it --shm-size=8gb --gpus all -v $HOME/workspace/:/workspace/ --name bambu-app nvidia/cuda:11.7.1-cudnn8-devel-ubuntu20.04


# docker create user
sudo addgroup --gid 3000 mygroupname && 
sudo adduser --uid 4000 --gid 3000 --disabled-password --gecos "" myusername

https://stackoverflow.com/questions/52331354/ensure-both-user-name-and-user-id-are-the-same-in-host-and-docker-container