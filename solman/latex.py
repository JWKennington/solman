"""Build LaTeX"""


import datetime
import jinja2
import os
import pathlib
import shutil
import subprocess
import tempfile


class SolManException(Exception):
	pass


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


def render_solutions_tex(title: str, soln_author: str, soln_date: datetime.date, abstract: str, body: str, bib_file: str, outfile: pathlib.Path=None):
	template = _ENV.get_template(_TEMPLATE.as_posix())
	options = {
	    'Abstract': abstract,
	    'Body': body,
		'SolutionAuthor': soln_author,
		'SolutionDate': soln_date,
		'SolutionTitle': title,
	}
	if bib_file is not None:
		options['Bib'] = bib_file

	rendered = template.render(**options)

	if outfile is None:
		return rendered

	with open(outfile, 'w') as fid:
		fid.write(rendered)


def render_pdf(file: str, outfile: pathlib.Path):
	with tempfile.TemporaryDirectory() as tmp:
		tmp = pathlib.Path(tmp)
		args = ['latexmk', 
				'-outdir={}'.format(tmp.as_posix()), 
				'-jobname={}'.format(outfile.with_suffix('').name),
				'-pdf',
				file]
		commandLine = subprocess.Popen(args)
		commandLine.communicate()
		tmp_pdf = tmp / outfile.with_suffix('.pdf').name
		if not tmp_pdf.exists():
			raise SolManException('Cannot find output file, make sure latexmk had no errors')
		shutil.copyfile(tmp_pdf.as_posix(), outfile.as_posix())
