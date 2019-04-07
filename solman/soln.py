"""Python file for building the various solutions markdown files into
coherent LaTeX files, as well as compiling the LaTeX into pdfs
"""


import collections
import datetime
import enum
import pathlib
import pypandoc
import tempfile
import types
import typing
import yaml
from solman import latex


class SolManError(ValueError):
    """Specific error subclass for SolMan use cases"""
    pass


MetaField = collections.namedtuple('MetaField', 'key attr coercion required default')


def meta_field(key: str, attr: str, coercion_func: types.FunctionType=None, required: bool=False, default: typing.Any=None):
    """Create a MetaField with sensible defaults

    Args:
        key:
            str, the dictionary key in the YAML file 
        attr: 
            str, the attribute name of the SolutionGroup object
        coercion_func: 
            Function, default None, an optional function to coerce the value from the YAML
        required:
            bool, default False, if True then this field MUST be in the yaml file 
        default: 
            Any, default None, an optional default value for the field.

    Returns:
        MetaField
    """
    return MetaField(key, attr, coercion_func, required, default)


class MetaFields:
    """Some fields that can be specified in the YAML"""
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
    """Types of problems"""
    Exercise = 'ex'
    Problem = 'prob'


class SolutionGroup:
    """A SolutionGroup represents a related collection of problem solutions. The problem solutions must be grouped into
    sections, by means of subdirectories. Each problem solution is a single ".md" file, but the SolutionGroup can be 
    converted into a single LaTeX file. Exercise solution files begin with "ex-" prefix and problem solutions begin with 
    "prob-" prefix (for instances when the distinction is useful).

    A SolutionGroup has a few important pieces:
        1. "Sections" - a hierarchical level of grouping for problem solutions, often a chapter or section
                        in the text from where the problems came.
        2. "Solutions" - markdown files that may include latex. Each file represents the solution to a single 
                         problem, allowing for maximum versioning across problems.
        3. "Meta" - a YAML file at the top of the directory structure containing relevant metadata fields. Specifically,
                    the meta data file MUST contain the following fields:
                        * Author - The author of the problems
                        * Book - The source of the problems
                        * Category - A categorical descriptor of the group (i.e. "Maths" or "Physics") 
                        * Name - A name for the group
                        * SolutionAuthor - The author of the solutions
                    The meta data file may also contain the following OPTIONAL fields:
                        * ISBN - The ISBN of the text from where the problems come
                        * ReferencesFile - a BibTex file containing references, include the ".bib"
                        * SectionPrefix (default "Chapter") - the prefix for the section headings
                        * SolutionDate (default datetime.date.today) - The date of the solutions. Only set this value if
                            the solutions are no longer likely to change.
                        * Subcategory - A generic subcategorical label for the group, i.e. "Linear Algebra" or "Mechanics"
                        * Tags -  A comma-separated list of tags for the problems

    Sample File Structure:
        The file structure below represents an example of a set of solutions called "demo",
        in which there are two sections (1 and 2), each of which have 1 exercise solution and 
        2 problem solutions. Notice how the problem solutions are prefixed with "prob-" and the 
        exercise solutions are prefixed with "ex-". Also notice how the meta file is at the top
        of the directory. The bibtex file is optional.
            demo
            ├── 1
            │   ├── ex-1.md
            │   ├── prob-1.md
            │   └── prob-2.md
            ├── 2
            │   ├── ex-1.md
            │   ├── prob-1.md
            │   └── prob-2.md
            ├── meta.yml
            └── references.bib

    Creating a SolutionGroup:
        Creating a SolutionGroup is simple. Once you have a directory structure that complies with above criteria, point
        the SolutionGroup.from_meta function at your meta file, and all solution files will be automatically discovered.
        Suppose that in the above example, the "demo" folder is in the home directory (or "~"). Then the below code 
        would be sufficient to create the associated SolutionGroup:
        >> SolutionGroup.from_meta("~/demo/meta.yaml") 

    Converting solutions to LaTeX:
        A SolutionGroup is capable of compiling all solutions into a single LaTeX file. Each solutions file (.md) is 
        converted from Markdown to LaTex source using PanDoc [1]. The resulting LaTeX source snippets are combined using
        a Jinja template [2]. Finally, the result is converted to PDF using latexmk (to properly handle the building of
        document-references, i.e. table of contents or bibliography).

    References:
        [1] https://pandoc.org/
        [2] http://jinja.pocoo.org/docs/2.10/
    """
    __slots__ = ('_problems', '_exercises',
                 'name', 'root',
                 'author', 'book', 'isbn', 'references_file', 'section_prefix',
                 'category', 'subcategory', 'tags',
                 'solution_author', 'solution_date')

    def __init__(self, name: str, root: pathlib.Path, author: str, book: str, category: str, solution_author: str, isbn: str=None, references_file: str=None, 
                 section_prefix: str='Chapter', subcategory: str=None, tags: typing.List[str]=None, solution_date: datetime.date=None):
        """Create a SolutionGroup

        Args:
            name:
                str, the name of the group. This value is arbitrary and left to the user. 
            root: 
                pathlib.Path, the root directory containing a meta file and subdirectories full of solution files
            author: 
                str, the name of the author of the PROBLEMS, not the solutions.
            book: 
                str, the title of the book from where the problems come.
            category: 
                str, a high-level category of the problems, i.e. "Math", "Physics"
            solution_author: 
                str, optional, the name of the author of the SOLUTIONS, not the problems.
            isbn: 
                str, optional, the ISBN of the source book of the problems
            references_file: 
                str, optional, the name of the bibtex file in the root directory
            section_prefix: 
                str, default 'Chapter', the section heading prefix.
            subcategory: 
                str, a subcategory of the group, i.e. "Linear Algebra" or "Mechanics".
            tags: 
                List[str], a list of tags of the problems group.
            solution_date: 
                datetime.date, the date on which the solutions were finalized. Only add when the SolutionGroup is complete.
        """
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
        """Helper function for caching attributes lazily.

        Args:
            cache_attr: 
                str, the name of the attribute that is being cached
            problem_type: 
                ProblemType

        Returns:
            Dict[str, List[str]] dict of lists of values
        """
        if getattr(self, cache_attr) is None:
            soln_files = tuple(self.root.glob(pattern='**/*{}*.md'.format(problem_type))) # TODO document this naming rule
            files_by_section = collections.defaultdict(list)
            for file in soln_files:
                section = file.parent.name
                if section.isdigit():
                    section = int(section)
                files_by_section[section].append(file)
            # Sort all values
            for k in files_by_section:
                files_by_section[k] = list(sorted(files_by_section[k]))
            setattr(self, cache_attr, files_by_section) 
        return getattr(self, cache_attr)

    @property
    def problems(self):
        """Problem solutions by section"""
        return self._lazy_get_files('_problems', ProblemType.Problem)

    @property
    def exercises(self):
        """Exercise solutions by section"""
        return self._lazy_get_files('_exercises', ProblemType.Exercise)

    def title(self) -> str:
        """Title of group, used for LaTeX heading"""
        return "{name} Solutions".format(name=self.name)

    def summary(self) -> str:
        """Summary text for the group, automatically generated and used for the abstract"""
        return ("The following is a selection of solutions for various problems and exercises found \n"
                "in {book} by {author}. These solutions were written by {solutions_author} and updated \n"
                "last on {date}").format(book=self.book,
                                         author=self.author,
                                         solutions_author=self.solution_author,
                                         date=datetime.datetime.strftime(self.solution_date, '%m-%d-%Y')).strip()

    def to_latex(self, outfile: typing.Union[str, pathlib.Path], problem_type: ProblemType=ProblemType.Problem):
        """Convert a solutions group to a LaTeX file. 

        Args:
            outfile: 
                str or Path, the output file.
            problem_type: 
                ProblemType, the type of problem to compile into LaTeX, either Exercise or Problem

        Returns:
            None, writes a LaTeX file to "outfile"
        """
        def _file_to_latex(file, problem_type):
            """Helper to convert an individual problem file to LaTeX"""
            soln_num = file.with_suffix('').name.replace(problem_type + '-', '')
            file_tex = pypandoc.convert_file(file.as_posix(), 'latex')
            return "{section}\n{content}".format(section='\\subsection{{ {} {} }}'.format(problem_type.name, soln_num),
                                                 content=file_tex)

        def _section_to_latex(section, files, problem_type):
            """Helper function to convert a section to LaTex"""
            return "{section}\n{content}".format(
                section='\\section{{ {} {} }}'.format(self.section_prefix, str(section)),
                content='\n\n'.join(_file_to_latex(file, problem_type) for file in files))

        if isinstance(outfile, str):
            outfile = pathlib.Path(outfile)

        files_by_section = {
            ProblemType.Exercise: lambda: self.exercises,
            ProblemType.Problem: lambda: self.problems,
        }[problem_type]()

        body_tex = '\n\n'.join(_section_to_latex(section, files, problem_type) for section, files in sorted(files_by_section.items(), key=lambda x: x[0]))
        return latex.render_solutions_tex(title=self.title(), 
                                          soln_author=self.solution_author,
                                          soln_date=self.solution_date,
                                          abstract=self.summary(), 
                                          body=body_tex, 
                                          bib_file=(self.root / self.references_file).as_posix() if self.references_file is not None else None,
                                          outfile=outfile.as_posix())

    def to_pdf(self, outfile: typing.Union[str, pathlib.Path], problem_type: ProblemType=ProblemType.Problem):
        """Convert a solutions group to a PDF file. 

        Args:
            outfile: 
                str or Path, the output file.
            problem_type: 
                ProblemType, the type of problem to compile into PDF, either Exercise or Problem

        Returns:
            None, writes a PDF file to "outfile"
        """
        if isinstance(outfile, str):
            outfile = pathlib.Path(outfile)

        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp)
            latex_file = tmp / outfile.with_suffix('.tex').name
            self.to_latex(latex_file, problem_type=problem_type)
            latex.render_pdf(latex_file.as_posix(), outfile)

    @staticmethod
    def from_meta(meta_file: pathlib.Path):
        """Create a SolutionGroup from a meta file

        Args:
            meta_file: 
                str or Path, the full path to the meta file 

        Returns:
            SolutionGroup
        """
        if isinstance(meta_file, str):
            meta_file = pathlib.Path(meta_file)
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
        """Create a similar SolutionGroup with some meta data overrides

        Args:
            **meta_overrides:
                dict, overrides 

        Returns:
            SolutionGroup
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
