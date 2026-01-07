import re

class NodeParser:
	LINE_PATTERN = re.compile(
		r'^(?P<hostname>[^:]+): OS=(?P<os>[^#]+)#OPXS=(?P<opxs>[^#]+)'
		r'#CPU=(?P<cpu_arch>[^#]+)#CPUINFO=(?P<socket>\d+)x(?P<cps>\d+)x(?P<threads>\d+)'
		r'#OPA100=(?P<opa100>\d+)#CN-5000=(?P<cn5k>\d+)#NV-MLX=(?P<mlx>\d+)'
		r'#NV-GPUs=(?P<nv_gpu>\d+)#AMD-GPUs=(?P<amd_gpu>\d+)#$'
	)

	@classmethod
	def parse_line(cls, line: str):
		match = cls.LINE_PATTERN.match(line.strip())
		return match.groupdict() if match else None
