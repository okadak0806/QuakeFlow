# FROM continuumio/miniconda3

FROM ubuntu:22.04

ENV PATH="/root/miniconda3/bin:${PATH}"
# ARG PATH="/root/miniconda3/bin:${PATH}"
RUN apt-get update && apt-get install -y wget make gcc gfortran && rm -rf /var/lib/apt/lists/*

RUN wget \
    https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh \
    && mkdir /root/.conda \
    && bash Miniconda3-latest-Linux-x86_64.sh -b \
    && rm -f Miniconda3-latest-Linux-x86_64.sh 

# Setup env variables
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY env.yml /app
# RUN conda env update -f=env.yml -n base
SHELL ["/bin/bash", "-c"]
RUN conda init bash
RUN conda env create -f=env.yml -n quakeflow
# RUN pip install --no-cache-dir --upgrade -i https://pypi.anaconda.org/zhuwq0/simple gmma
RUN conda clean --all -y

ENV TF_ENABLE_MKL_NATIVE_FORMAT=0
ENV PATH="/root/miniconda3/envs/quakeflow/bin:${PATH}"
WORKDIR /home/jovyan/work
CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--port=8888", "--allow-root"]