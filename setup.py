from setuptools import setup

import neuromllite
version = neuromllite.__version__

setup(
    name='neuromllite',
    version=version,
    author='Padraig Gleeson',
    author_email='p.gleeson@gmail.com',
    packages = ['neuromllite','neuromllite.sweep'],
    url='https://github.com/NeuroML/NeuroMLlite',
    license='LICENSE.lesser',
    description='A common JSON based format for compact network specification, closely tied to NeuroML v2',
    long_description=open('README.md').read(),
    install_requires=[],
    classifiers = [
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.5',
        'Topic :: Scientific/Engineering']
)
