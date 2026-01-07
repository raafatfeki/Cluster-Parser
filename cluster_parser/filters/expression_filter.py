import re
import ast

class ExpressionFilter:
	"""
	Evaluates logical expressions like:
	  (os == sles AND cpu == rome) OR (nv_gpu > 0)
	  NOT (os == sles AND nv_gpu == 0)
	"""

	ALLOWED_OPS = ['==', '!=', '>', '>=', '<', '<=', 'in', 'has']

	@staticmethod
	def _check_condition(node_info, key, op, value):
		if key not in node_info:
			return False
		node_value = node_info[key]

		# Auto-convert numeric values for correct comparison
		if re.fullmatch(r'-?\d+', str(value)):
			value = int(value)
			try:
				node_value = int(node_value)
			except ValueError:
				pass

		try:
			if op == '==': return node_value == value
			if op == '!=': return node_value != value
			if op == '>':  return node_value > value
			if op == '>=': return node_value >= value
			if op == '<':  return node_value < value
			if op == '<=': return node_value <= value
			if op == 'in': return node_value in value
			if op == 'has': return value in node_value
		except Exception:
			return False
		return False

	@classmethod
	def _compile_expression(cls, expr_str: str):
		"""
		Convert the user's expression (using AND, OR, NOT, parentheses) into a
		Python-evaluable expression using our safe `check()` helper.
		"""
		expr = expr_str.strip()

		# Normalize logical keywords (case-insensitive)
		expr = re.sub(r'\bAND\b', 'and', expr, flags=re.IGNORECASE)
		expr = re.sub(r'\bOR\b', 'or', expr, flags=re.IGNORECASE)
		expr = re.sub(r'\bNOT\b', 'not', expr, flags=re.IGNORECASE)

		# Replace atomic conditions with callable checks
		ops_pattern = '|'.join(re.escape(op) for op in cls.ALLOWED_OPS)
		cond_pattern = rf'([a-zA-Z_][a-zA-Z0-9_]*)\s*({ops_pattern})\s*("[^"]*"|\'[^\']*\'|[^ )]+)'

		def repl(match):
			key, op, val = match.groups()
			val = val.strip().strip('"\'')
			return f'check(node_info, "{key}", "{op}", "{val}")'

		expr_code = re.sub(cond_pattern, repl, expr)

		try:
			tree = ast.parse(expr_code, mode='eval')
			# Optional: sanity check to allow only safe AST nodes
			for node in ast.walk(tree):
				if not isinstance(node, (ast.Expression, ast.BoolOp, ast.UnaryOp, ast.BinOp,
										 ast.Compare, ast.Call, ast.Load, ast.Name, ast.Constant,
										 ast.And, ast.Or, ast.Not)):
					raise ValueError("Unsafe or unsupported syntax detected.")
			return compile(tree, "<filter_expr>", "eval")
		except Exception as e:
			raise ValueError(f"Invalid filter expression: {e}")

	@classmethod
	def apply(cls, nodes_map: dict, expr_str: str):
		"""Return nodes matching the logical expression."""
		compiled = cls._compile_expression(expr_str)
		matching = []
		for host, node_info in nodes_map.items():
			try:
				result = eval(compiled, {'check': cls._check_condition, 'node_info': node_info})
				if result:
					matching.append(host)
			except Exception:
				continue
		return matching
