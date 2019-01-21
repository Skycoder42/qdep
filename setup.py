import setuptools
from qdep.qdep import version

with open("README.md", "r") as fh:
	long_description = fh.read()

setuptools.setup(
	name="qdep",
	version=version,
	author="Skycoder42",
	author_email="skycoder42.de@gmx.de",
	description="A very basic yet simple to use dependency management tool for qmake based projects",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/Skycoder42/qdep",
	packages=setuptools.find_packages(),
	install_requires=[
		"appdirs",
		"lockfile",
		"argcomplete"
	],
	classifiers=[
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: BSD License",
		"Operating System :: OS Independent",
	],
	entry_points={
		"console_scripts": [
			'qdep=qdep.internal.cli:main'
		]
	}
)
