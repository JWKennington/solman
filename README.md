# solman

**Sol**utions **man**ual writing utility. Though this utility is written in Python, the user is not expected to write
any python as part of writing solutions. Rather, the solutions are written individually as markdown files (.md) in a 
meaningful directory structure. This package aims to convert those separate solutions into a variety of outputs, 
including a single LaTeX file as well as Pelican-compatible blog posts / web pages.  

Test Result: [![CircleCI](https://circleci.com/gh/JWKennington/solman/tree/master.svg?style=svg)](https://circleci.com/gh/JWKennington/pyperbolic/tree/master)


## Solution Groups

A SolutionGroup represents a related collection of problem solutions. The problem solutions must be grouped into
sections, by means of subdirectories. Each problem solution is a single ".md" file, but the SolutionGroup can be 
converted into a single LaTeX file. Exercise solution files begin with "ex-" prefix and problem solutions begin with 
"prob-" prefix (for instances when the distinction is useful).

### Solution Group Structure

A SolutionGroup has a few important pieces:

1. **Sections** a hierarchical level of grouping for problem solutions, often a chapter or section in the text from where the problems came.
1. **Solutions** markdown files that may include latex. Each file represents the solution to a single problem, allowing for maximum versioning across problems.
1. **MetaData** a YAML file at the top of the directory structure containing relevant metadata fields. 

Specifically, the meta data file MUST contain the following fields:

- _Author_ The author of the problems
- _Book_ The source of the problems
- _Category_ A categorical descriptor of the group (i.e. "Maths" or "Physics") 
- _Name_ A name for the group
- _SolutionAuthor_ The author of the solutions

The meta data file may also contain the following OPTIONAL fields:

- _ISBN_ The ISBN of the text from where the problems come
- _ReferencesFile_ A BibTex file containing references, include the ".bib"
- _SectionPrefix_ (default "Chapter") - the prefix for the section headings
- _SolutionDate_ (default datetime.date.today) - The date of the solutions. Only set this value if the solutions are no longer likely to change.
- _Subcategory_ A generic subcategorical label for the group, i.e. "Linear Algebra" or "Mechanics"
- _Tags_ A comma-separated list of tags for the problems


## Sample File Structure

The file structure below represents an example of a set of solutions called "demo",
in which there are two sections (1 and 2), each of which have 1 exercise solution and 
2 problem solutions. Notice how the problem solutions are prefixed with "prob-" and the 
exercise solutions are prefixed with "ex-". Also notice how the meta file is at the top
of the directory. The bibtex file is optional.

```
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
```

## Creating a SolutionGroup

Creating a SolutionGroup is simple. Once you have a directory structure that complies with above criteria, point
the SolutionGroup.from_meta function at your meta file, and all solution files will be automatically discovered.
Suppose that in the above example, the "demo" folder is in the home directory (or "~"). Then the below code 
would be sufficient to create the associated SolutionGroup:

```python
>>> from solman import SolutionGroup
>>> s = SolutionGroup.from_meta("~/demo/meta.yaml")
>>> s.name
"SampleName"
``` 


## Converting solutions to LaTeX

A SolutionGroup is capable of compiling all solutions into a single LaTeX file. Each solutions file (.md) is 
converted from Markdown to LaTex source using PanDoc [1]. The resulting LaTeX source snippets are combined using
a Jinja template [2]. Finally, the result is converted to PDF using latexmk (to properly handle the building of
document-references, i.e. table of contents or bibliography). The SolutionGroup class has a method for creating 
a Latex file:

```python
>>> s.to_latex('~/sample.tex') # will output a combined LaTeX file
```


## Converting solutions to PDF

Similar to converting solutions to LaTeX, converting solutions to pdf (via prior conversion to LaTeX) is as simple
as calling the "to_pdf" method of the SolutionGroup.

```python
>>> s.to_pdf('~/sample.pdf') # will output a combined PDF file
```


## References
1. https://pandoc.org/
1. http://jinja.pocoo.org/docs/2.10/
