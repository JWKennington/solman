"""Python file for building the various solutions markdown files into
coherent LaTeX files, as well as compiling the LaTeX into pdfs
"""


import collections
import datetime
import enum
import pathlib
import pypandoc
import types
import typing
import yaml
from solman import latex


class SolManError(ValueError):
    pass


MetaField = collections.namedtuple('MetaField', 'key attr coercion required default')


def meta_field(key: str, attr: str, coercion_func: types.FunctionType=None, required: bool=False, default: typing.Any=None):
    return MetaField(key, attr, coercion_func, required, default)


class MetaFields:
    Author = meta_field('Author', 'author', required=True)
    Book = meta_field('Book', 'book', required=True)
    Category = meta_field('Category', 'category', required=True)
    ISBN = meta_field('ISBN', 'isbn')
    Name = meta_field('Name', 'name', required=True)
    ReferencesFile = meta_field('ReferencesFile', 'references_file')
    SectionPrefix = meta_field('SectionPrefix', 'section_prefix', default='Chapter')
    SolutionAuthor = meta_field('SolutionAuthor', 'solution_author', required=True)
    SolutionDate = meta_field('SolutionDate', 'solution_date', default=datetime.date.today(), coercion_func=lambda d: d if isinstance(d, datetime.date) else datetime.datetime.strptime(d, '%m-%d-%Y'))
    Subcategory = meta_field('Subcategory', 'subcategory')
    Tags = meta_field('Tags', 'tags', coercion_func=lambda comma_separated: tuple(comma_separated.split(',')))


class ProblemType(str, enum.Enum):
    Exercise = 'ex'
    Problem = 'prob'


class SolutionGroup:
    __slots__ = ('_problems', '_exercises',
                 'name', 'root',
                 'author', 'book', 'isbn', 'references_file', 'section_prefix',
                 'category', 'subcategory', 'tags',
                 'solution_author', 'solution_date')

    def __init__(self, name: str, root: pathlib.Path, author: str, book: str, category: str, solution_author: str, isbn: str=None, references_file: str=None, 
                 section_prefix: str='Chapter', subcategory: str=None, tags: typing.List[str]=None, solution_date: datetime.date=None):
        self.name = name
        self.root = root
        self.author = author
        self.book = book
        self.isbn = isbn
        self.references_file = references_file
        self.section_prefix = section_prefix
        self.category = category
        self.subcategory = subcategory
        self.tags = tags
        self.solution_author = solution_author
        if solution_date is None:
            solution_date = datetime.date.today()
        self.solution_date = solution_date
        self._problems = None
        self._exercises = None

    def __repr__(self):
        num_exercises = sum(len(v) for v in self.exercises.values())
        num_problems = sum(len(v) for v in self.problems.values())
        return 'SolutionGroup({}, {:d}P, {:d}E)'.format(self.name, num_problems, num_exercises)

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
        return ("The following is a selection of solutions for various problems and exercises found \n"
                "in {book} by {author}. These solutions were written by {solutions_author} and updated \n"
                "last on {date}").format(book=self.book,
                                         author=self.author,
                                         solutions_author=self.solution_author,
                                         date=datetime.datetime.strftime(self.solution_date, '%m-%d-%Y')).strip()

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
                                          soln_date=self.solution_date,
                                          abstract=self.summary(), 
                                          body=body_tex, 
                                          bib_file=(self.root / self.references_file).as_posix() if self.references_file is not None else None,
                                          outfile=outfile.as_posix())


    def _file_to_latex(self, file, problem_type):
        soln_num = file.with_suffix('').name.replace(problem_type + '-', '')
        file_tex = pypandoc.convert_file(file.as_posix(), 'latex')
        return "{section}\n{content}".format(section='\\subsection{{ {} {} }}'.format(problem_type.name, soln_num),
                                            content=file_tex)

    def _section_to_latex(self, section, files, problem_type):
        return "{section}\n{content}".format(section='\\section{{ {} {} }}'.format(self.section_prefix, str(section)),
                                             content='\n\n'.join(self._file_to_latex(file, problem_type) for file in files))

    @staticmethod
    def from_meta(meta_file: pathlib.Path):
        with open(meta_file.as_posix()) as mfid:
            meta = yaml.load(mfid)

        def get_meta_field(meta, field):
            value = meta.get(field.key, field.default)
            if value is None and field.required:
                raise SolManError('Required field missing from config: {}'.format(field.key))
            if field.coercion is not None:
                value = field.coercion(value)
            return value

        kwargs = {field.attr: get_meta_field(meta, field) for field in
                  [getattr(MetaFields, f) for f in dir(MetaFields) if
                   not callable(getattr(MetaFields, f)) and not f.startswith('__')]}
        kwargs['root'] = meta_file.parent
        return SolutionGroup(**kwargs)

    def with_meta_overrides(self, **meta_overrides):
        """
        name: str, root: pathlib.Path, author: str, book: str, category: str, solution_author: str, isbn: str=None, references_file: str=None, 
                 section_prefix: str='Chapter', subcategory: str=None, tags: typing.List[str]=None, solution_date: datetime.date=None

        """
        kwargs = {
            'name': self.name, 
            'root': self.root, 
            'author': self.author, 
            'book': self.book, 
            'category': self.category, 
            'solution_author': self.solution_author,
            'isbn': self.isbn, 
            'references_file': self.references_file, 
            'section_prefix': self.section_prefix, 
            'subcategory': self.subcategory, 
            'tags': self.tags, 
            'solution_date': self.solution_date
        }
        kwargs.update(meta_overrides)
        new = SolutionGroup(**kwargs)
        new._problems = self.problems
        new._exercises = self.exercises
        return new
