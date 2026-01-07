# Cluster-Parser
A tool for parsing nodes in a Slurm-based cluster to collect hardware and system information—including CPU details, network interfaces, GPUs, and OS versions—and query this data using database-like filters to display only nodes that match specific criteria.

---

## Table of Contents
- [Overview](#overview)  
- [Collecting Node Data](#collecting-node-data)  
- [Main Script](#main-script)  
- [Usage](#usage)  
- [Filter Examples](#filter-examples)  
- [Supported Operations](#supported-operations)  
- [Requirements](#requirements)  

---

## Overview
Cluster-Parser allows you to gather detailed information about active nodes in a Slurm cluster and filter them using logical expressions similar to SQL queries. This makes it easy to identify nodes that meet specific hardware or system requirements.

---

## Collecting Node Data
The first step is to collect data from a Slurm environment using:

```
./getNodeInfoSlurm.sh
```

- This requires the **root password** of the remote nodes and beeing root on the login Slurm Node.
- By default, the script creates a new file `nodesInfo.txt`.  
- To append information to an existing file (useful if you have different root passwords for different nodes), pass the parameter `"append"`.  

The collected information is stored in `cluster_parser/data/nodesInfo.txt`.  
A second file, `hostfile`, is also created containing only the list of available nodes, which can be useful to run commands across all nodes.

Nodes that are unreachable or have different passwords will be printed during the process.

---

## Main Script
The main script is located at:

```
cluster_parser/parse_cluster.py
```

There is also a symbolic link called `parse.py`, so you can run the script directly:

`./parse.py` or `python3 parse.py`

---

## Usage

```
usage: parse.py [-h] [--file FILE] [filter]

Cluster Node Filter

positional arguments:
  filter       Logical expression, e.g. '(os == sles AND cpu == rome) OR nv_gpu > 0'

optional arguments:
  -h, --help   show this help message and exit
  --file FILE  Path to node info file
```

- If `--file` is not provided, the script uses `cluster_parser/data/nodesInfo.txt` by default.

---

## Filter Examples
The script allows filtering nodes based on the following columns:

`hostname | os | opxs | cpu_arch | socket | cps | threads | opa100 | cn5k | mlx | nv_gpu | amd_gpu | cpu`

Example:

```
./parse.py '(os == sles AND cpu == rome) OR nv_gpu > 0'
```

This selects nodes where:
- OS is `sles` **and** CPU is AMD `rome`,  
- **or** the node has at least one NVIDIA GPU.

---

## Supported Operations
You can use the following logical and arithmetic operators in filters:

- Logical: `AND`, `OR`  
- Arithmetic: `==`, `!=`, `>`, `>=`, `<`, `<=`  
- Other: `in`, `has`  

---

## Requirements
- **pdsh**  
- **Python module `tabulate`**  

Install `tabulate` via pip if needed:

```
pip3 install tabulate
```

## Other Tool get_run_info.py

NOT READY Yet.
