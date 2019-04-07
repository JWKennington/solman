"""Setup file
"""


import setuptools
import solman


with open("README.md", "r") as fh:
    long_description = fh.read()


setuptools.setup(name='apsjournals',
                 version=solman.__version__,
                 description='Solutions manual writing utility in Python.',
                 long_description=long_description,
                 long_description_content_type="text/markdown",
                 url=solman.__github_url__,
                 author='James W. Kennington',
                 author_email='jameswkennington@gmail.com',
                 license='MIT',
                 packages=setuptools.find_packages(),
                 zip_safe=False, 
                 include_package_data=True)
