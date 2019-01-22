import argparse

import argcomplete

from qdep.qdep import *
from qdep.internal.private import *


def complete_path(prefix, filter_fn):
	def map_dir_contents(base_dir, file):
		full_path = path.join(base_dir, file)
		if path.isdir(full_path):
			return full_path + "/"
		else:
			return full_path

	path_base, path_name = path.split(prefix)
	if len(path_base) == 0:
		path_base = "."
	return map(lambda f: map_dir_contents(path_base, f), filter(lambda f: filter_fn(path_base, path_name, f), os.listdir(path_base)))


def complete_executable(prefix, limiter=None):
	def filter_dir_contents(base_dir, base_name, file):
		if path.isdir(path.join(base_dir, file)):
			return True
		elif file.startswith(base_name) and (limiter is None or limiter in file):
			return True
		else:
			return False

	return complete_path(prefix, filter_dir_contents)


def complete_suffix(prefix, suffix):
	def filter_dir_contents(base_dir, base_name, file):
		if path.isdir(path.join(base_dir, file)):
			return True
		elif file.startswith(base_name) and file.endswith(suffix):
			return True
		else:
			return False

	return complete_path(prefix, filter_dir_contents)


def qmake_completer(prefix, **kwargs):
	return complete_executable(prefix, "qmake")


def make_completer(prefix, **kwargs):
	return complete_executable(prefix, "make")


def dir_completer(prefix, **kwargs):
	def filter_dir_contents(base_dir, base_name, file):
		return path.isdir(path.join(base_dir, file)) and file.startswith(base_name)

	return complete_path(prefix, filter_dir_contents)


def pro_completer(prefix, **kwargs):
	return complete_suffix(prefix, ".pro")


def pri_completer(prefix, **kwargs):
	return complete_suffix(prefix, ".pri")


def main():
	parser = argparse.ArgumentParser(description="A very basic yet simple to use dependency management tool for qmake based projects.")
	parser.add_argument("--version", action="version", version=version)
	parser.add_argument("--trace", action="store_true", help="In case of an exception, print the whole stack trace")

	sub_args = parser.add_subparsers(dest="operation", title="Operations", metavar="{operation}")

	prfgen_parser = sub_args.add_parser("prfgen", help="Generate a qmake project feature (prf) for the given qmake.")
	prfgen_parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to place the prf file for.").completer = qmake_completer
	prfgen_parser.add_argument("-d", "--dir", dest="dir", action="store", help="The directory containing the mkspec folder where to place the prf file. If not specified, qmake is queried form the location.").completer = dir_completer

	init_parser = sub_args.add_parser("init", help="Initialize a pro file to use qdep by adding the required lines.")
	init_parser.add_argument("profile", help="The path to the pro file to add the qdep code to.").completer = pro_completer

	lupdate_parser = sub_args.add_parser("lupdate", help="Run lupdate for the QDEP_TRANSLATION variable in a given pri file.")
	lupdate_parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to find the corresponding lupdate for.").completer = qmake_completer
	lupdate_parser.add_argument("--pri-file", dest="pri_path", action="store", required=True, help="The path to the pri-file that contains a QDEP_TRANSLATIONS variable, to generate translations for.").completer = pri_completer
	lupdate_parser.add_argument("largs", action="store", nargs="*", metavar="lupdate-argument", help="Additionals arguments to be passed to lupdate. MUST be proceeded by '--'!")

	clear_parser = sub_args.add_parser("clear", help="Remove all sources from the users global cache.")
	clear_parser.add_argument("-y", "--yes", dest="yes", action="store_true", help="Immediatly remove the caches, without asking for confirmation first.")

	versions_parser = sub_args.add_parser("versions", help="List all known versions/tags of the given package")
	versions_parser.add_argument("-b", "--branches", dest="branches", action="store_true", help="Include branches into the output.")
	versions_parser.add_argument("--no-tags", dest="tags", action="store_false", help="Exclude tags from the output.")
	versions_parser.add_argument("-s", "--short", dest="short", action="store_true", help="Print output as a single, uncommented line")
	versions_parser.add_argument("--limit", action="store", type=int, help="Limit the returned lists to the LIMIT newest entries per type.")
	versions_parser.add_argument("package", help="The package to list the versions for. Specify without a version of pro/pri file path!")

	query_parser = sub_args.add_parser("query", help="Query details about a given package identifier")
	query_parser.add_argument("--expand", action="store_true", help="Only expand the package name, don't output anything else.")
	query_parser.add_argument("--no-check", dest="check", action="store_false", help="Do not check if the package actually exists.")
	query_parser.add_argument("--versions", action="store_true", help="Also query and display all available tags and branches. See 'qdep.py versions' for alternative formats.")
	query_parser.add_argument("package", help="The package to query information for.")

	get_parser = sub_args.add_parser("get", help="Download the sources of one ore more packages into the source cache.")
	get_parser.add_argument("--extract", action="store_true", help="Run in pro-file mode. Arguments are interpreted as pro files and are scanned for dependencies")
	get_parser.add_argument("--eval", action="store_true", help="Fully evaluate all pro files by running qmake on them. Implies '--extract'.")
	get_parser.add_argument("--no-recurse", dest="recurse", action="store_false", help="Do not scan downloaded packages for further dependencies.")
	get_parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to use for evaluation if '--eval' was specified.").completer = qmake_completer
	get_parser.add_argument("--make", action="store", default="make", help="The path to a make executable to use for evaluation if '--eval' was specified.").completer = make_completer
	get_parser.add_argument("-d", "--dir", "--cache-dir", dest="dir", action="store", help="Specify the directory where to download the sources to. Shorthand for using the QDEP_CACHE_DIR environment variable.").completer = dir_completer
	get_parser.add_argument("args", nargs="+", help="The packages (or pro files if using '--extract') to download the sources for.").completer = pro_completer

	update_parser = sub_args.add_parser("update", help="Check for newer versions of used packages and optionally update them.")
	update_parser.add_argument("--eval", action="store_true", help="Fully evaluate all pro files by running qmake on them.")
	update_parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to use for evaluation if '--eval' was specified.").completer = qmake_completer
	update_parser.add_argument("--make", action="store", default="make", help="The path to a make executable to use for evaluation if '--eval' was specified.").completer = make_completer
	update_parser.add_argument("--replace", action="store_true", help="Automatically replace newer packages in the evaluated project files instead of printing to the console.")
	update_parser.add_argument("profile", metavar="pro-file", help="The qmake pro-file to update dependencies for.").completer = pro_completer

	dephash_parser = sub_args.add_parser("dephash", help="[INTERNAL] Generated unique identifying hashes for qdep packages.")
	dephash_parser.add_argument("--project", action="store_true", help="Interpret input as a project dependency, not a normal pri dependency.")
	dephash_parser.add_argument("--pkgpath", action="store_true", help="Return the hash and the pro/pri subpath as tuple, seperated by a ';'.")
	dephash_parser.add_argument("input", action="store", nargs="*", metavar="package", help="The packages to generate hashes for.")

	pkgresolve_parser = sub_args.add_parser("pkgresolve", help="[INTERNAL] Download the given qdep package and extract relevant information from it.")
	pkgresolve_parser.add_argument("--no-pull", dest="pull", action="store_false", help="Do not update existing packages that are based on branches instead of tags.")
	pkgresolve_parser.add_argument("--no-clone", dest="clone", action="store_false", help="Do not allow installation of new packages. Trying so will lead to an error. Updating existing packages is still possible.")
	pkgresolve_parser.add_argument("--project", dest="project", action="store_true", help="Interpret input as a project dependency, not a normal pri dependency")
	pkgresolve_parser.add_argument("package", action="store", metavar="package", help="The package identifier of the package to be downloaded and resolved.")
	pkgresolve_parser.add_argument("version", action="store", nargs="?", metavar="latest-version", help="The previously cached version for packages with no version identifier.")

	hookgen_parser = sub_args.add_parser("hookgen", help="[INTERNAL] Generate a header file with a method to load all resource hooks.")
	hookgen_parser.add_argument("--hooks", action="store", nargs="*", help="The names of additional hook functions to be referenced.")
	hookgen_parser.add_argument("prefix", action="store", help="The target name to use as part of the generated hook method.")
	hookgen_parser.add_argument("header", action="store", help="The path to the header-file to be generated.")
	hookgen_parser.add_argument("dummy", action="store", metavar="pro-file", help="The path to the current pro file - needed for Makefile rules.")
	hookgen_parser.add_argument("resources", action="store", nargs="*", metavar="resource", help="Paths to the resource-files to generate the hooks for.")

	hookimp_parser = sub_args.add_parser("hookimp", help="[INTERNAL] Generate a source file that includes and runs all qdep hooks as normal startup hook.")
	hookimp_parser.add_argument("--hooks", action="store", nargs="*", help="The names of additional hook functions to be referenced.")
	hookimp_parser.add_argument("outfile", action="store", help="The path to the cpp-file to be generated.")
	hookimp_parser.add_argument("dummy", action="store", metavar="pro-file", help="The path to the current pro file - needed for Makefile rules.")
	hookimp_parser.add_argument("headers", action="store", nargs="*", metavar="header", help="Paths to the header-files that contain hooks to be run.")

	lconvert_parser = sub_args.add_parser("lconvert", help="[INTERNAL] Combine ts files with translations from qdep packages.")
	lconvert_parser.add_argument("--combine", action="store", nargs="*", help="The qdep ts files that should be combined into the real ones.")
	lconvert_parser.add_argument("tsfile", action="store", help="The path to the ts file to combine with the qdep ts files.")
	lconvert_parser.add_argument("outfile", action="store", help="The path to the ts file to be generated.")
	lconvert_parser.add_argument("largs", action="store", nargs="+", metavar="lconvert-tool", help="Path to the lconvert tool as well as additional arguments to it.")

	prolink_parser = sub_args.add_parser("prolink", help="[INTERNAL] Resolve the path a linked project dependency would be at.")
	prolink_parser.add_argument("prodir", action="store", help="The directory of the pro file that includes the other one.")
	prolink_parser.add_argument("pkghash", action="store", help="The hash identifier of the project to link.")
	prolink_parser.add_argument("pkgpath", action="store", help="The path to the pro file within the dependency.")
	prolink_parser.add_argument("--link", action="store", help="Perform the link operation and create the symlink/dirtree, based on the given path to the dependency sources.")

	argcomplete.autocomplete(parser)
	res = parser.parse_args()

	try:
		if res.operation == "prfgen":
			prfgen(path.abspath(sys.argv[0]), res.qmake, res.dir)
		elif res.operation == "init":
			init(res.profile)
		elif res.operation == "lupdate":
			lupdate(res.pri_path, res.qmake, res.largs)
		elif res.operation == "clear":
			clear(res.yes)
		elif res.operation == "versions":
			versions(res.package, res.tags, res.branches, res.short, res.limit)
		elif res.operation == "query":
			query(res.package, res.check, res.versions, res.expand)
		elif res.operation == "get":
			get(*res.args, extract=res.extract, evaluate=res.eval, recurse=res.recurse, qmake=res.qmake, make=res.make, cache_dir=res.dir)
		elif res.operation == "update":
			update(res.profile, res.eval, res.replace, res.qmake, res.make)
		elif res.operation == "dephash":
			dephash(*res.input, project=res.project, pkgpath=res.pkgpath)
		elif res.operation == "pkgresolve":
			pkgresolve(res.package, res.version, res.project, res.pull, res.clone)
		elif res.operation == "hookgen":
			hookgen(res.prefix, res.header, res.resources, res.hooks)
		elif res.operation == "hookimp":
			hookimp(res.outfile, res.headers, res.hooks)
		elif res.operation == "lconvert":
			lconvert(res.tsfile, res.outfile, *res.combine, lconvert_args=res.largs)
		elif res.operation == "prolink":
			prolink(res.prodir, res.pkghash, res.pkgpath, res.link)
		else:
			parser.print_help()
			return 1

		return 0
	except Exception as exception:
		if res.trace or True:
			raise
		else:
			print(exception, file=sys.stderr)
		return 1


if __name__ == '__main__':
	sys.exit(main())
