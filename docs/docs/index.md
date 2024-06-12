This page explains how to install Mol\* Volumes & Segmentations 2.0

# Install the server
To install the server, clone the Github repository and change current directory to the root repository directory (`molstar-volseg` by default):

```shell
git clone https://github.com/molstar/molstar-volseg.git
cd molstar-volseg
```
# Set up and activate the environment
Set up the environment using either Conda:

```shell
conda env create -f environment.yaml
```

or Mamba:

```shell
mamba env create -f environment.yaml
```

Activate the created environment:

```shell
conda activate cellstar-volume-server
```
