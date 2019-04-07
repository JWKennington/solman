"""Build LaTeX"""


import jinja2
import os
import pathlib


_TEMPLATE = pathlib.Path(__file__).parent / 'templates' / 'template.tex'
_ENV = jinja2.Environment(
	block_start_string = '\BLOCK{',
	block_end_string = '}',
	variable_start_string = '\VAR{',
	variable_end_string = '}',
	comment_start_string = '\#{',
	comment_end_string = '}',
	line_statement_prefix = '%%',
	line_comment_prefix = '%#',
	trim_blocks = True,
	autoescape = False,
	loader = jinja2.FileSystemLoader(os.path.abspath('/'))
)


def render_solutions_tex(title: str, soln_author: str, abstract: str, body: str, bib_file: str, outfile: pathlib.Path=None):
	template = _ENV.get_template(_TEMPLATE.as_posix())
	options = {
		'SolutionTitle': title,
		'SolutionAuthor': soln_author,
		'Abstract': abstract,
		'Body': body,
	}
	if bib_file is not None:
		options['Bib'] = bib_file

	rendered = template.render(**options)

	if outfile is None:
		return rendered

	with open(outfile, 'w') as fid:
		fid.write(rendered)
