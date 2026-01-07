#!/usr/bin/env python3
import os
import sys
import argparse
from tabulate import tabulate
from parser.node_parser import NodeParser
from parser.cpu_identifier import CPUIdentifier
from filters.expression_filter import ExpressionFilter


class ClusterFilterApp:
	def __init__(self, input_file: str):
		self.input_file = input_file
		self.nodes = {}

	def load_nodes(self):
		try:
			with open(self.input_file, 'r') as file:
				for line in file:
					if not line.strip():
						continue
					parsed = NodeParser.parse_line(line)
					if parsed:
						parsed["cpu"] = CPUIdentifier.identify(parsed["cpu_arch"])
						self.nodes[parsed["hostname"]] = parsed
		except FileNotFoundError:
			print(f"Error: File '{self.input_file}' not found.")
			sys.exit(1)
		except Exception as e:
			print(f"Error reading file: {e}")
			sys.exit(1)

	def filter_nodes(self, expr: str):
		return ExpressionFilter.apply(self.nodes, expr)

	def display_nodes(self, hostnames):
		if not hostnames:
			print("No nodes matched the filter.")
			return

		headers = list(self.nodes[next(iter(hostnames))].keys())
		table = []
		for h in hostnames:
			row = [self.nodes[h].get(k, "N/A") for k in headers]
			table.append(row)

		print(tabulate(table, headers=headers, tablefmt="grid"))


def main():
	parser = argparse.ArgumentParser(description="Cluster Node Filter")
	parser.add_argument("filter", nargs="?", default="True",help="Logical expression, e.g. '(os == sles AND cpu == rome) OR nv_gpu > 0'")
	parser.add_argument("--file", default=f"{os.path.dirname(os.path.realpath(__file__))}/data/nodesInfo.txt", help="Path to node info file")
	args = parser.parse_args()

	app = ClusterFilterApp(args.file)
	app.load_nodes()
	result = app.filter_nodes(args.filter)
	app.display_nodes(result)


if __name__ == "__main__":
	main()
