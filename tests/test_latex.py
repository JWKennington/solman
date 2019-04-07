"""Unittests for building solutions files"""


from distutils.spawn import find_executable
import hashlib
import pathlib
import PyPDF2 as pypdf
import tempfile
import unittest
from solman import soln, latex


DEMO_ROOT = pathlib.Path(__file__).parent / 'demo'
LATEXMK_AVAILABLE = find_executable('latexmk') is not None


class LatexTest(unittest.TestCase):
    def setUp(self):
        self.solns = soln.SolutionGroup.from_meta(DEMO_ROOT / 'meta.yml')

    @unittest.skipIf(not LATEXMK_AVAILABLE, 'Must have pdflatex executable to test pdf compilation')
    def test_to_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            tmp_file = pathlib.Path(tmp) / 'demo_tmp.tex'
            self.solns.to_latex(tmp_file.as_posix())
            base_file = DEMO_ROOT / 'base_file.pdf'
            pdf_file = tmp / 'demo_file.pdf'
            latex.render_pdf(tmp_file.as_posix(), pdf_file)
            base_checksum = pdf_file_checksum(base_file.as_posix())
            new_checksum = pdf_file_checksum(pdf_file.as_posix())
            self.assertEqual(new_checksum, base_checksum)


def pdf_file_checksum(filepath: str) -> str:
    with open(filepath, 'rb') as fid:
        doc = pypdf.PdfFileReader(fid)
        page_contents = tuple(doc.getPage(n).extractText() for n in range(doc.getNumPages()))
        m = hashlib.sha1()
        m.update('|||'.join(page_contents).encode())
        return m.hexdigest()


DEMO_TEX_FILE = r"""
\title{SampleName Solutions}
\author{Solution Author}
\date{2019-04-06}

\documentclass[12pt]{article}

\begin{document}
\maketitle

\begin{abstract}
The following is a selection of solutions for various problems and exercises found 
in Sample Book Title by Problem Author. These solutions were written by Solution Author and updated 
last on 04-06-2019
\end{abstract}

\section{ Chapter 1 }
\subsection{ Problem 1 }
This is a sample solution for problem 1.1. The below is some latex that
will be used in the solution \[\int_{a}^b f(x) dx = F(b) - F(a)\] In the
above its clear that the define integral \(f\).


\subsection{ Problem 2 }
This is a sample solution for problem 1.2. The below is some latex that
will be used in the solution \[a = b = c = d\] In the above its clear
that \(inline\). The end.


\section{ Chapter 2 }
\subsection{ Problem 1 }
This is a sample solution for problem 2.1. The below is some latex that
will be used in the solution \[\int_{a}^b f(x) dx = F(b) - F(a)\] In the
above its clear that the define integral \(f\).


\subsection{ Problem 2 }
This is a sample solution for problem 2.2. The below is some latex that
will be used in the solution \[a = b = c = d\] In the above its clear
that \(inline\). The end.


\nocite{*}
\bibliographystyle{natbib}
\bibliography{ references.bib }

\end{document}
""".strip()
