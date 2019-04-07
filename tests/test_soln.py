"""Unittests for building solutions files"""


from distutils.spawn import find_executable
import pathlib
import tempfile
import unittest
from solman import soln


DEMO_ROOT = pathlib.Path(__file__).parent / 'demo'
LATEXMK_AVAILABLE = find_executable('latexmk') is not None


class SolutionGroupTest(unittest.TestCase):
    def setUp(self):
        self.solns = soln.SolutionGroup.from_meta(DEMO_ROOT / 'meta.yml')

    def test_demo(self):
        self.assertEqual(repr(self.solns), "SolutionGroup(SampleName, 4P, 2E)")

    def test_to_latex(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_file = pathlib.Path(tmp) / 'demo_tmp.tex' 
            self.solns.with_meta_overrides(references_file=None).to_latex(tmp_file.as_posix())
            with open(tmp_file.as_posix(), 'r') as fid:
                result = fid.read()
                msg = "\nExpected:\n{}\n\nGot:\n{}".format(DEMO_TEX_FILE, result)
                if result != DEMO_TEX_FILE:
                    results_lines = [line for line in result.split('\n') if line]
                    expected_lines = [line for line in DEMO_TEX_FILE.split('\n') if line]
                    if len(results_lines) != len(expected_lines):
                        msg += "\n\nOther:\nUnequal Number of nontrivial lines: result {:d} expected {:d}".format(len(results_lines), len(expected_lines))
                    else:
                        diff_lines = [(rline, eline) for rline, eline in zip(results_lines, expected_lines) if rline != eline]
                        msg += "\n\nOther:\nUnequal Lines:\n{}".format('\n'.join("\nDiffLine {:d}:\nExpected: {}\nGot: {}\n".format(n, l[0], l[1]) for n, l in enumerate(diff_lines)))
                self.assertEqual(result, DEMO_TEX_FILE, msg=msg)


DEMO_TEX_FILE = r"""
\title{SampleName Solutions}
\author{Solution Author}
\date{2019-04-06 00:00:00}

\documentclass[12pt]{article}

\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{hyperref}
\usepackage[style=phys]{biblatex}
\addbibresource{}

\begin{document}
\maketitle

\begin{abstract}
The following is a selection of solutions for various problems and exercises found 
in Sample Book Title by Problem Author. These solutions were written by Solution Author and updated 
last on 04-06-2019
\end{abstract}

\tableofcontents
\newpage

\section{ Chapter 1 }
\subsection{ Problem 1 }
This is a sample solution for problem 1.1. The below is some latex that
will be used in the solution \[ \int_{a}^b f(x) dx = F(b) - F(a) \] In
the above its clear that the define integral \$ f \$.


\subsection{ Problem 2 }
This is a sample solution for problem 1.2. The below is some latex that
will be used in the solution \[ a = b = c = d \] In the above its clear
that \$ inline \$. The end.


\section{ Chapter 2 }
\subsection{ Problem 1 }
This is a sample solution for problem 2.1. The below is some latex that
will be used in the solution \[ \int_{a}^b f(x) dx = F(b) - F(a) \] In
the above its clear that the define integral \$ f \$.


\subsection{ Problem 2 }
This is a sample solution for problem 2.2. The below is some latex that
will be used in the solution \[ a = b = c = d \] In the above its clear
that \$ inline \$. The end.



\end{document}
""".strip()
