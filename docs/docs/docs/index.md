This page explains how to install Mol\* Volumes & Segmentations 2.0

# Install the server
To install the server, clone the Github repository and change current directory to the root repository directory (`cellstar-volume-server-v2` by default):

<!-- TODO: update repo link to volseg -->
```shell
git clone https://github.com/aliaksei-chareshneu/cellstar-volume-server-v2.git
cd cellstar-volume-server-v2
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
conda activate cellstar-volume-server-3.10
```
