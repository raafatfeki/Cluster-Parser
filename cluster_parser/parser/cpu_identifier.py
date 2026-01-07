import re

class CPUIdentifier:
	ARCHITECTURE_MAP = {
		'sandybridge': [r'\bv1\b'],
		'ivybridge': [r'\bv2\b'],
		'haswell': [r'\bv3\b'],
		'broadwell': [r'\bv4\b'],
		'skylake': [r'\bIntel\b.*?[0-9]1[0-9]{2}'],
		'cascadelake': [r'\bIntel\b.*?[0-9]2[0-9]{2}'],
		'icelake': [r'\bIntel\b.*?[0-9]3[0-9]{2}'],
		'sapphirerapid': [r'\bIntel\b.*?[0-9]4[0-9]{2}'],
		'emeraldrapid': [r'\bIntel\b.*?[0-9]5[0-9]{2}'],
		'graniterapid': [r'\bIntel\b.*?\b6[0-9]{3}[A-Z]?\b'],
		'naples': [r'epyc\s*[0-9]{3}1'],
		'rome': [r'epyc\s*[0-9]{3}2'],
		'milan': [r'epyc\s*[0-9]{3}3'],
		'genoa': [r'epyc\s*[0-9]{3}4'],
		'turin': [r'epyc\s*[0-9]{3}5'],
	}

	@classmethod
	def identify(cls, cpu_model: str) -> str:
		text = cpu_model.lower()
		for arch, patterns in cls.ARCHITECTURE_MAP.items():
			for pat in patterns:
				if re.search(pat, text, re.IGNORECASE):
					return arch
		return "unknown"
