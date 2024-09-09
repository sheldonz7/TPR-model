
#FROM nvidia/cuda:12.1.0-cudnn8-devel-ubuntu20.04
#FROM nvidia/cuda:11.3.1-cudnn8-devel-ubuntu20.04
FROM ubuntu:20.04


# Set environment variable to avoid prompts
ENV DEBIAN_FRONTEND=noninteractive


# container related arguments
ARG USERNAME
ARG USERID
ARG GROUPNAME
ARG GROUPID



WORKDIR /


# Bambu dependencies



# create user and group
RUN addgroup --gid $GROUPID $GROUPNAME
RUN adduser --uid $USERID --gid $GROUPID --disabled-password --gecos "" $USERNAME


