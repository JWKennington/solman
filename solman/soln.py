"""Python file for building the various solutions markdown files into
coherent LaTeX files, as well as compiling the LaTeX into pdfs
"""


import collections
import datetime
import enum
import pathlib
import pypandoc
import typing
import yaml
from solman import latex


class MetaField(str, enum.Enum):
    Author = 'Author'
    Book = 'Book'
    Category = 'Category'
    ISBN = 'ISBN'
    Name = 'Name'
    ReferencesFile = 'ReferencesFile'
    SectionPrefix = 'SectionPrefix'
    SolutionAuthor = 'SolutionAuthor'
    SolutionDate = 'SolutionDate'
    Subcategory = 'Subcategory'
    Tags = 'Tags'


class ProblemType(str, enum.Enum):
    Exercise = 'ex'
    Problem = 'prob'


class SolutionGroup:
    def __init__(self, root: pathlib.Path):
        self.root = root
        self._problems = None
        self._exercises = None
        self._init_meta()

    def __repr__(self):
        num_exercises = sum(len(v) for v in self.exercises.values())
        num_problems = sum(len(v) for v in self.problems.values())
        return 'SolutionGroup({}, {:d}P, {:d}E)'.format(self.name, num_problems, num_exercises)

    def _init_meta(self):
        meta_file = self.root / 'meta.yml'
        with open(meta_file.as_posix()) as mfid:
            meta = yaml.load(mfid)
        self.author = meta.get(MetaField.Author, None)
        self.book = meta.get(MetaField.Book, None)
        self.category = meta.get(MetaField.Category, None)
        self.isbn = meta.get(MetaField.ISBN, None)
        self.name = meta.get(MetaField.Name, None)
        self.references_file = meta.get(MetaField.ReferencesFile, None)
        self.section_prefix = meta.get(MetaField.SectionPrefix, 'Chapter')
        self.solution_author = meta.get(MetaField.SolutionAuthor, 'J. W. Kennington')
        self.solution_date = meta.get(MetaField.SolutionDate, datetime.date.today())
        self.subcategory = meta.get(MetaField.Subcategory, None)
        self.tags= meta.get(MetaField.Tags, None)
        if self.tags is not None:
            self.tags = tuple(self.tags.split(','))

    def _lazy_get_files(self, cache_attr: str, problem_type: ProblemType):
        if getattr(self, cache_attr) is None:
            soln_files = tuple(self.root.glob(pattern='**/*{}*.md'.format(problem_type))) # TODO document this naming rule
            files_by_section = collections.defaultdict(list)
            for file in soln_files:
                section = file.parent.name
                if section.isdigit():
                    section = int(section)
                files_by_section[section].append(file)
            setattr(self, cache_attr, files_by_section) 
        return getattr(self, cache_attr)

    @property
    def problems(self):
        return self._lazy_get_files('_problems', ProblemType.Problem)

    @property
    def exercises(self):
        return self._lazy_get_files('_exercises', ProblemType.Exercise)

    def title(self) -> str:
        return "{name} Solutions".format(name=self.name)

    def summary(self) -> str:
        return """
        The following is a selection of solutions for various problems and exercises found
        in {book} by {author}. These solutions were written by {solutions_author} and updated
        last on {date}.
        """.format(book=self.book,
                   author=self.author,
                   solutions_author=self.solution_author,
                   date=datetime.datetime.strftime(self.solution_date, '%m-%d-%Y'))

    def to_latex(self, outfile: typing.Union[str, pathlib.Path], problem_type: ProblemType=ProblemType.Problem):
        if isinstance(outfile, str):
            outfile = pathlib.Path(outfile)

        files_by_section = {
            ProblemType.Exercise: lambda: self.exercises,
            ProblemType.Problem: lambda: self.problems,
        }[problem_type]()

        

        body_tex = '\n\n'.join(self._section_to_latex(section, files, problem_type) for section, files in sorted(files_by_section.items(), key=lambda x: x[0]))
        return latex.render_solutions_tex(title=self.title(), 
                                          soln_author=self.solution_author, 
                                          abstract=self.summary(), 
                                          body=body_tex, 
                                          bib_file=self.references_file,
                                          outfile=outfile.as_posix())


    def _file_to_latex(self, file, problem_type):
        soln_num = file.with_suffix('').name.replace(problem_type + '-', '')
        file_tex = pypandoc.convert_file(file.as_posix(), 'latex')
        return "{section}\n{content}".format(section='\\subsection{{ {} {} }}'.format(problem_type.name, soln_num),
                                            content=file_tex)

    def _section_to_latex(self, section, files, problem_type):
        return "{section}\n{content}".format(section='\\section{{ {} {} }}'.format(self.section_prefix, str(section)),
                                             content='\n\n'.join(self._file_to_latex(file, problem_type) for file in files))
