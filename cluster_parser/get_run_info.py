#!/usr/bin/env python3

import os
import re
import glob

import argparse
from openpyxl import Workbook
from tabulate import tabulate

# def get_sysconfig_file(directory: str):
# 	"""
# 	Returns the path of any file starting with 'sysconfig' in the directory.
# 	If none found, returns None.
# 	"""

# 	pattern = os.path.join(directory, "sysconfig*")
# 	matches = glob.glob(pattern)

# 	if not matches:
# 		return None

# 	# Pick the first one found
# 	return matches[0]

def get_sysconfig_file(directory: str):
	pattern = os.path.join(directory, "sysconfig-*")
	candidates = glob.glob(pattern)

	regex = re.compile(
		r"^sysconfig-(.+)-[A-Za-z]{3}-\d{2}-\d{4}-\d{2}-\d{2}\.out$"
	)

	for file_path in sorted(candidates):  # deterministic pick
		filename = os.path.basename(file_path)
		if regex.match(filename):
			return file_path

	return None

def parse_hfi1_parameters(file_path: str) -> dict:
	"""
	Parses a file and extracts lines like:
	/sys/module/hfi1/parameters/Parameter:Value

	Returns:
		dict {Parameter: Value}
	"""
	params = {}

	if not os.path.isfile(file_path):
		return params

	pattern = re.compile(r"/sys/module/hfi1/parameters/([^:]+):(.+)")

	try:
		with open(file_path, "r") as f:
			for line in f:
				match = pattern.search(line.strip())
				if match:
					param = match.group(1).strip()
					value = match.group(2).strip()
					params[param] = value
				else:
					if line.startswith("fabric"):
						parts = line.split()
						if len(parts) >= 2:
							params["fabric"]=parts[1]
	except Exception:
		pass
	return params

def get_bulksvc(directory: str, params_dict):
	return params_dict.get("use_bulksvc")

def get_num_user_contexts(directory: str, params_dict):
	return params_dict.get("num_user_contexts")

def get_nodes(directory: str, params_dict=None):
	hostfile_path = os.path.join(directory, "hostfile")

	if not os.path.isfile(hostfile_path):
		return None

	try:
		with open(hostfile_path, "r") as f:
			nodes = [line.strip() for line in f if line.strip()]
		return ",".join(nodes) if nodes else None
	except Exception:
		return None	

def get_opxs_version(directory: str, params_dict=None):
	version_file = os.path.join(directory, "ifsvers")

	if not os.path.isfile(version_file):
		return None
	try:
		with open(version_file, "r") as f:
			version = f.readline().strip()
		return version if version else None
	except Exception:
		return None

def get_fabric(directory: str, params_dict=None):
	return params_dict.get("fabric")

PARAMETERS = {
	"OPXS_Version": get_opxs_version,
	"Nodes": get_nodes,
	"Fabric": get_fabric,
	"Bulksvc": get_bulksvc,
	"Num_user_contexts": get_num_user_contexts
}

def read_directories(file_path):
	"""Read file and ignore comments (#) and empty lines"""
	directories = []

	with open(file_path, "r") as f:
		for line in f:
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			directories.append(line)

	return directories

def process_data(directories):
	"""Parse parameters and detect missing directories"""
	results = []
	missing_dirs = []
	params_dict = {}

	for directory in directories:

		if not os.path.exists(directory):
			missing_dirs.append(directory)
			continue

		pattern = os.path.join(directory, "sysconfig-*")
		candidates = glob.glob(pattern)

		for file_path in candidates:
			filename = os.path.basename(file_path)
			params_dict.update(parse_hfi1_parameters(file_path))

		if not params_dict:
			raise ValueError("params_dict is empty")

		row = {"Directory": os.path.basename(os.path.normpath(directory))}

		for param, func in PARAMETERS.items():
			try:
				row[param] = func(directory, params_dict)
			except Exception:
				row[param] = None

		results.append(row)

	return results, missing_dirs

def output_excel(data, filename):
	wb = Workbook()
	ws = wb.active
	ws.title = "Parsed Data"

	headers = ["Directory"] + list(PARAMETERS.keys())
	ws.append(headers)

	for item in data:
		row = [item.get(h) for h in headers]
		ws.append(row)

	wb.save(filename)
	print(f"✅ Excel file created: {filename}")


def output_terminal(data):
	headers = ["Directory"] + list(PARAMETERS.keys())
	rows = [[item.get(h) for h in headers] for item in data]

	print("\n📋 Parsed Output:\n")
	print(tabulate(rows, headers=headers, tablefmt="grid"))


def main():
	parser = argparse.ArgumentParser(
		description="Parse directory list and extract parameters"
	)
	parser.add_argument(
		"-i", "--input",
		required=True,
		help="Input text file containing directory list"
	)
	parser.add_argument(
		"-o", "--output",
		help="Output Excel file (.xlsx). If not provided, prints to terminal."
	)

	args = parser.parse_args()

	directories = read_directories(args.input)
	data, missing_dirs = process_data(directories)

	if args.output and args.output.lower().endswith(".xlsx"):
		output_excel(data, args.output)
	else:
		output_terminal(data)

	if missing_dirs:
		print("\n⚠️ Directories that do NOT exist:")
		for d in missing_dirs:
			print(f" - {d}")
	else:
		print("\n✅ All directories exist.")


if __name__ == "__main__":
	main()
