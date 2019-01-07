#!/usr/bin/env python3

import argparse
import sys
import subprocess
import os
import os.path as path
import re
import hashlib
import shutil
import stat
import tempfile

# import appdirs with basic fallback
try:
	import appdirs

	def get_cache_dir_default():
		return appdirs.user_cache_dir("qdep")
except ImportError:
	print("Warning: Failed to find appdirs module - Cache paths might not be as expected", file=sys.stderr)

	def get_cache_dir_default():
		if sys.platform == "win32":
			return path.expanduser("~/AppData/Local/qdep/Cache")
		elif sys.platform == "darwin":
			return path.expanduser("~/Library/Caches/qdep")
		else:
			return path.join(os.getenv('XDG_CACHE_HOME', path.expanduser('~/.cache')), "qdep")

try:
	from lockfile import LockFile as FileLocker
except ImportError:
	print("Warning: Failed to find lockfile module - parallel execution of qdep is not possible!", file=sys.stderr)

	# dummy class
	class FileLocker:
		def __init__(self, lock_path):
			pass

		def acquire(self):
			pass

		def release(self):
			pass


def get_cache_dir(pkg_url, pkg_branch):
	cache_dir = os.getenv("QDEP_CACHE_DIR", get_cache_dir_default())
	cache_dir = path.join(cache_dir, "src", hashlib.sha3_256(pkg_url.encode("UTF-8")).hexdigest(), pkg_branch)
	os.makedirs(cache_dir, exist_ok=True)
	return cache_dir


def get_override_map():
	or_env = os.getenv("QDEP_SOURCE_OVERRIDE")
	if or_env is None:
		return {}

	or_map = {}
	for env_info in or_env.split(";"):
		env_pair = env_info.split("^")
		if len(env_pair) == 2:
			or_map[env_pair[0]] = env_pair[1]
	return or_map


def pkg_hash(pkg_url, pkg_path):
	return "__QDEP_PKG_" + hashlib.sha3_256((pkg_url + pkg_path).encode("UTF-8")).hexdigest()


def package_resolve(package, pkg_version=None, project=False):
	pattern = re.compile(r'^(?:([^@\/]+\/[^@\/]+)|(\w+:\/\/.*\.git|[^@:]*@[^@]*:[^@]+\.git))(?:@([^\/\s]+)(\/.*)?)?$')
	path_pattern = re.compile(r'^.*\/([^\/]+)\.git$')

	match = re.match(pattern, package)
	if not match:
		raise Exception("Given package is not a valid package descriptor: " + package)

	# extract package url
	if match.group(1) is not None:
		pkg_url = os.getenv("QDEP_DEFAULT_PKG_FN", "https://github.com/{}.git").format(match.group(1))
	elif match.group(2) is not None:
		pkg_url = match.group(2)
	else:
		raise Exception("Invalid package specified: " + package)

	# extract branch
	if match.group(3) is not None:
		pkg_branch = match.group(3)
	elif pkg_version is not None:
		pkg_branch = pkg_version
	else:
		pkg_branch = None

	# extract pri path
	if match.group(4) is not None:
		pkg_path = match.group(4)
	else:
		pkg_path = "/" + re.match(path_pattern, pkg_url).group(1) + (".pro" if project else ".pri")

	return pkg_url, pkg_branch, pkg_path


def get_all_tags(pkg_url):
	ls_res = subprocess.run(["git", "ls-remote", "--tags", "--exit-code", pkg_url], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	ref_pattern = re.compile(r'[a-fA-F0-9]+\s+refs\/tags\/([^\s]+)')
	tags = []
	for match in re.finditer(ref_pattern, ls_res.stdout):
		tags.append(match.group(1))
	return tags


def get_latest_tag(pkg_url):
	return get_all_tags(pkg_url)[-1]


def get_sources(pkg_url, pkg_branch, pull=True, clone=True):

	if pkg_branch is None:
		pkg_branch = get_latest_tag(pkg_url)

	cache_dir = get_cache_dir(pkg_url, pkg_branch)

	locker = FileLocker(cache_dir)
	locker.acquire()
	try:
		needs_ro = False
		if path.isdir(path.join(cache_dir, ".git")):
			if pull and not path.exists(path.join(cache_dir, ".qdep_static_branch")):
				subprocess.run(["git", "pull", "--force", "--ff-only", "--update-shallow", "--recurse-submodules"], cwd=cache_dir, stdout=subprocess.DEVNULL, check=True)
				needs_ro = True
		elif clone:
			subprocess.run(["git", "clone", "--recurse-submodules", "--shallow-submodules", "--depth", "1", "--branch", pkg_branch, pkg_url, cache_dir], check=True)
			head_ref_res = subprocess.run(["git", "symbolic-ref", "HEAD"], cwd=cache_dir, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			if head_ref_res.returncode != 0:
				open(path.join(cache_dir, ".qdep_static_branch"), 'a').close()
			needs_ro = True
		else:
			raise Exception("The --no-clone flag was specified - cannot install new packages with pulling disabled")

		if needs_ro:
			NO_WRITE_MASK = ~stat.S_IWUSR & ~stat.S_IWGRP & ~stat.S_IWOTH
			for root, dirs, files in os.walk(cache_dir, topdown=True):
				dirs[:] = [d for d in dirs if d != ".git"]
				for file in files:
					f_path = path.join(root, file)
					cur_perm = stat.S_IMODE(os.lstat(f_path).st_mode)
					os.chmod(f_path, cur_perm & NO_WRITE_MASK)
	except:
		shutil.rmtree(cache_dir, ignore_errors=True)
		raise
	finally:
		locker.release()

	return cache_dir, pkg_branch


def prfgen(arguments):
	qmake_res = subprocess.run([arguments.qmake, "-query", "QT_HOST_DATA"], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	prf_path = path.join(str(qmake_res.stdout).strip(), "mkspecs", "features", "qdep.prf")
	print("Generating PRF-File as: ", prf_path)
	with open(prf_path, "w") as prf_file:
		self_path = path.abspath(__file__)
		prf_file.write("# Generated by {}\n".format(self_path))
		prf_file.write("qdep_force|!isEmpty(OUT_PWD) {  # Used to detect if qdep was loaded from an indirect evaluation\n\n")
		prf_file.write("isEmpty(QDEP_PATH): QDEP_PATH = {}\n".format(self_path))
		prf_file.write(qdep_prf)
		prf_file.write("\n}\n")
	return 0


def lupdate(arguments):
	qmake_res = subprocess.run([arguments.qmake, "-query", "QT_HOST_BINS"], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	lupdate_path = path.join(str(qmake_res.stdout).strip(), "lupdate")
	with tempfile.TemporaryDirectory() as tmp_dir:
		tmp_pro_path = path.join(tmp_dir, "lupdate.pro")
		with open(tmp_pro_path, "w") as tmp_file:
			tmp_file.write("include({})\n".format(arguments.pri_path))
			tmp_file.write("TRANSLATIONS = $$QDEP_TRANSLATIONS\n")
		subprocess.run([lupdate_path] + arguments.largs + [tmp_pro_path], check=True)
	return 0


def dephash(arguments):
	for package in arguments.input:
		pkg_url, pkg_branch, pkg_path = package_resolve(package, project=arguments.project)
		if arguments.pkgpath:
			print(pkg_hash(pkg_url, pkg_path) + ";" + pkg_path)
		else:
			print(pkg_hash(pkg_url, pkg_path))
	return 0


def pkgresolve(arguments):
	ov_map = get_override_map()

	pkg_url, pkg_branch, pkg_path = package_resolve(arguments.package, pkg_version=arguments.version, project=arguments.project)
	needs_cache = pkg_branch is None
	if pkg_url in ov_map:
		pkg_base = ov_map[pkg_url]
	else:
		pkg_base, pkg_branch = get_sources(pkg_url, pkg_branch, pull=arguments.pull, clone=arguments.clone)
	print(pkg_hash(pkg_url, pkg_path))
	print(pkg_branch)
	print(pkg_base)
	print(pkg_path)
	print(needs_cache)
	return 0


def hookgen(arguments):
	inc_guard = path.basename(arguments.header).replace(".", "_").upper()
	with open(arguments.header, "w") as out_file:
		out_file.write("#ifndef {}\n".format(inc_guard))
		out_file.write("#define {}\n\n".format(inc_guard))

		for hook in arguments.hooks:
			out_file.write("void {}();\n".format(hook))

		out_file.write("\ninline void qdep_{}_init() {{\n".format(arguments.prefix))
		out_file.write("\t// resources\n")
		for resource in arguments.resources:  # ignore the first argument, as it is always the current pro file (to ensure this rule is always run
			out_file.write("\tQ_INIT_RESOURCE({});\n".format(path.splitext(path.basename(resource))[0]))
		out_file.write("\t// hooks\n")
		for hook in arguments.hooks:
			out_file.write("\t{}();\n".format(hook))
		out_file.write("}\n\n")

		out_file.write("#endif //{}\n".format(inc_guard))
	return 0


def hookimp(arguments):
	with open(arguments.outfile, "w") as out_file:
		targets = []
		target_regex = re.compile(r".*qdep_(.*)_hooks\.h$")

		out_file.write("#include <QtCore/QCoreApplication>\n")
		for header in arguments.headers:
			abs_path = path.abspath(header)
			out_file.write("#include \"{}\"\n".format(abs_path))
			targets.append(re.match(target_regex, header).group(1))

		out_file.write("\n")
		for hook in arguments.hooks:
			out_file.write("void {}();\n".format(hook))

		out_file.write("\nnamespace {\n\n")
		out_file.write("void __qdep_startup_hooks() {\n")
		for target in targets:
			out_file.write("\tqdep_{}_init();\n".format(target))
		for hook in arguments.hooks:
			out_file.write("\t::{}();\n".format(hook))
		out_file.write("}\n\n")
		out_file.write("}\n")
		out_file.write("Q_COREAPP_STARTUP_FUNCTION(__qdep_startup_hooks)\n")
	return 0


def lconvert(arguments):
	# sort combine args into a map of the languages
	sub_map = dict()
	for sub_arg in arguments.combine:
		sub_base = path.splitext(path.basename(sub_arg))[0]
		sub_args = sub_base.split("_")[1:]
		for arg_cnt in range(len(sub_args)):
			suffix = "_".join(sub_args[arg_cnt:])
			if suffix not in sub_map:
				sub_map[suffix] = []
			sub_map[suffix].append(sub_arg)

	# find the qm files to combine with the input
	target_base = path.splitext(path.basename(arguments.tsfile))[0]
	ts_args = target_base.split("_")[1:]
	combine_list = []
	for arg_cnt in range(len(ts_args) - 1, -1, -1):
		suffix = "_".join(ts_args[arg_cnt:])
		if suffix in sub_map:
			combine_list = combine_list + sub_map[suffix]
	combine_list.append(arguments.tsfile)

	# run lconvert
	subprocess.run(arguments.largs + ["-if", "ts", "-i"] + combine_list + ["-of", "ts", "-o", arguments.outfile], check=True)
	return 0


def prolink(arguments):
	link_target = path.join(arguments.prodir, ".qdep", arguments.pkghash, "src")
	pro_target = path.join(link_target, arguments.pkgpath[1:])

	# skip mode -> only print the path
	if arguments.link is None:
		print(pro_target)
		return 0

	# normal mode -> first unlink any existing stuff
	if path.islink(link_target):
		if os.name == 'nt' and path.isdir(link_target):
			os.rmdir(link_target)
		else:
			os.unlink(link_target)
	elif path.isdir(link_target):
		shutil.rmtree(link_target)
	elif path.exists(link_target):
		os.remove(link_target)

	# then link the correct project again
	try:
		os.makedirs(path.dirname(link_target), exist_ok=True)
		os.symlink(arguments.link, link_target, target_is_directory=True)
	except OSError:
		# symlink is not possible, copy instead
		print("Project WARNING: Failed to symlink project dependecy. Performing deep copy instead", file=sys.stderr)
		shutil.copytree(arguments.link, link_target, symlinks=True, ignore_dangling_symlinks=True)

	print(pro_target)
	return 0


def main():
	parser = argparse.ArgumentParser(description="A very basic yet simple to use dependency management tool for qmake based projects.")
	parser.add_argument("-v", "--version", action="version", version="1.0.0")

	sub_args = parser.add_subparsers(dest="operation", title="Operations", metavar="{operation}")

	prfgen_parser = sub_args.add_parser("prfgen", help="Generate a qmake project feature (prf) for the given qmake.")
	prfgen_parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to place the prf file for.")

	lupdate_parser = sub_args.add_parser("lupdate", help="...")
	lupdate_parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to find the corresponding lupdate for.")
	lupdate_parser.add_argument("--pri-file", dest="pri_path", action="store", help="The path to the pri-file that contains a QDEP_TRANSLATIONS variable, to generate translations for.")
	lupdate_parser.add_argument("largs", action="store", nargs="*", metavar="lupdate-argument", help="Additionals arguments to be passed to lupdate. MUST be proceeded by '--'!")

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

	res = parser.parse_args()
	if res.operation == "prfgen":
		result = prfgen(res)
	elif res.operation == "lupdate":
		result = lupdate(res)
	elif res.operation == "dephash":
		result = dephash(res)
	elif res.operation == "pkgresolve":
		result = pkgresolve(res)
	elif res.operation == "hookgen":
		result = hookgen(res)
	elif res.operation == "hookimp":
		result = hookimp(res)
	elif res.operation == "lconvert":
		result = lconvert(res)
	elif res.operation == "prolink":
		result = prolink(res)
	else:
		result = -1
	sys.exit(result)


qdep_prf = """isEmpty(QDEP_VERSION): QDEP_VERSION = 1.0.0
isEmpty(QDEP_TOOL) {
	win32: QDEP_TOOL = python $$system_path($$QDEP_PATH)
	else: QDEP_TOOL = $$system_path($$QDEP_PATH)
}

# verify versions are correct
__qdep_script_version = $$system($$QDEP_TOOL --version)
!equals(QDEP_VERSION, $$__qdep_script_version):error("qdep.py script version ($$__qdep_script_version) is different to qdep.prf version ($$QDEP_VERSION)! Run '$$QDEP_TOOL prfgen --qmake $$QMAKE_QMAKE' to update the prf file!")

# set some variables
isEmpty(QDEP_CACHE_SCOPE): QDEP_CACHE_SCOPE = stash

isEmpty(QDEP_GENERATED_DIR): QDEP_GENERATED_DIR = $$OUT_PWD
debug_and_release:CONFIG(release, debug|release): QDEP_GENERATED_SOURCES_DIR = $${QDEP_GENERATED_DIR}/release
else:debug_and_release:CONFIG(debug, debug|release): QDEP_GENERATED_SOURCES_DIR = $${QDEP_GENERATED_DIR}/debug
else: QDEP_GENERATED_SOURCES_DIR = $$QDEP_GENERATED_DIR
isEmpty(QDEP_GENERATED_TS_DIR): QDEP_GENERATED_TS_DIR = $$QDEP_GENERATED_DIR/.qdepts
debug_and_release:CONFIG(release, debug|release): QDEP_GENERATED_TS_DIR = $${QDEP_GENERATED_QM_DIR}/release
else:debug_and_release:CONFIG(debug, debug|release): QDEP_GENERATED_TS_DIR = $${QDEP_GENERATED_QM_DIR}/debug
isEmpty(QDEP_LCONVERT) {
	qtPrepareTool(QDEP_LCONVERT, lconvert)
	QDEP_LCONVERT += -sort-contexts 
}

isEmpty(QDEP_EXPORT_PATH): QDEP_EXPORT_PATH = $$QDEP_GENERATED_DIR
debug_and_release:CONFIG(release, debug|release): QDEP_EXPORT_PATH = $$QDEP_EXPORT_PATH/release
debug_and_release:CONFIG(debug, debug|release): QDEP_EXPORT_PATH = $$QDEP_EXPORT_PATH/debug
isEmpty(QDEP_EXPORT_NAME) {
	__qdep_base_name = $$basename(_PRO_FILE_)
	QDEP_EXPORT_NAME = $$replace(__qdep_base_name, "\\\\.[^\\\\.]*$", "_export.pri")
}

isEmpty(__QDEP_PRIVATE_SEPERATOR): __QDEP_PRIVATE_SEPERATOR = "==="
isEmpty(__QDEP_TUPLE_SEPERATOR): __QDEP_TUPLE_SEPERATOR = "---"

CONFIG += qdep_build
DEFINES += QDEP_BUILD

# The primary dependecy collector function
defineTest(qdepCollectDependencies) {
	# transform all dependencies into unique hashes
	qdep_dependencies = 
	for(arg, ARGS): qdep_dependencies += $$system_quote($$arg)
	qdep_ok = 
	qdep_hashes = $$system($$QDEP_TOOL dephash $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return(false)
	
	for(dep_hash, qdep_hashes) {
		# handle each dependency, but each package only once
		dep_pkg = $$take_first(ARGS)
		!contains(__QDEP_INCLUDE_CACHE, $$dep_hash) {
			# Install the sources and extract some parameters
			dep_extra_args = 
			qdep_no_pull: dep_extra_args += --no-pull
			qdep_no_clone: dep_extra_args += --no-clone
			!isEmpty($${dep_hash}.version): dep_vers_arg = $$system_quote($$first($${dep_hash}.version))
			else: dep_vers_arg =
			qdep_ok = 
			dep_data = $$system($$QDEP_TOOL pkgresolve $$dep_extra_args $$system_quote($$dep_pkg) $$dep_vers_arg, lines, qdep_ok)
			!equals(qdep_ok, 0):return(false)
			!equals(dep_hash, $$take_first(dep_data)):error("Cricital internal error: dependencies out of sync"):return(false)
			
			dep_version = $$take_first(dep_data)
			dep_base = $$take_first(dep_data)
			dep_path = $$take_first(dep_data)
			dep_needs_cache = $$take_first(dep_data)
		
			$${dep_hash}.package = $$dep_pkg
			$${dep_hash}.version = $$dep_version
			$${dep_hash}.path = $${dep_base}$${dep_path}
			$${dep_hash}.exports = 
			$${dep_hash}.local = 1
			export($${dep_hash}.package)
			export($${dep_hash}.version)
			export($${dep_hash}.path)
			export($${dep_hash}.local)
			
			# Cache the package version for dependencies with undetermined versions
			!qdep_no_cache:equals(dep_needs_cache, True):!cache($${dep_hash}.version, set $$QDEP_CACHE_SCOPE):warning("Failed to cache package version for $$dep_pkg")
			
			# Find all dependencies that package depends on and call this method recursively for those
			sub_deps = $$fromfile($$eval($${dep_hash}.path), QDEP_DEPENDS)
			__QDEP_REAL_DEPS_STACK += $$dep_hash			
			!isEmpty(sub_deps):!qdepCollectDependencies($$sub_deps):return(false)			
			__QDEP_INCLUDE_CACHE *= $$take_last(__QDEP_REAL_DEPS_STACK)
			export(__QDEP_INCLUDE_CACHE)
			
			# Handle all defines for symbol exports, if specified
			sub_exports = $$fromfile($$eval($${dep_hash}.path), QDEP_PACKAGE_EXPORTS)
			
			qdep_export_all|contains(QDEP_EXPORTS, $$dep_pkg) {
				!static:!staticlib:for(sub_export, sub_exports) {
					DEFINES += "$${sub_export}=Q_DECL_EXPORT"
					QDEP_EXPORTED_DEFINES += "$${sub_export}=Q_DECL_IMPORT"
					$${dep_hash}.exports += $$sub_export
				} else:for(sub_export, sub_exports) {
					DEFINES += "$${sub_export}="
					QDEP_EXPORTED_DEFINES += "$${sub_export}="
				}
			} else:for(sub_export, sub_exports): \\
				DEFINES += "$${sub_export}="
			export(DEFINES)
			export(QDEP_EXPORTED_DEFINES)
			export($${dep_hash}.exports)
		} else: \\
			!equals(dep_version, $$first($${dep_hash}.version)): \\
			warning("Detected includes of multiple different versions of the same dependency. Package \\"$$first($${dep_hash}.package)\\" is used, and version \\"$$dep_version\\" was detected.")
	}
	
	return(true)
}

# The dependecy collector function for project dependencies in subdirs projects
defineTest(qdepCollectProjectDependencies) {
	# transform all dependencies into unique hashes
	qdep_dependencies = 
	for(arg, ARGS): qdep_dependencies += $$system_quote($$arg)
	qdep_ok = 
	qdep_hashes = $$system($$QDEP_TOOL dephash --project $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return(false)
	
	for(dep_hash, qdep_hashes) {
		# handle each dependency, but each package only once
		dep_pkg = $$take_first(ARGS)
		!contains(__QDEP_INCLUDE_CACHE, $$dep_hash) {
			# Install the sources and extract some parameters
			dep_extra_args = 
			qdep_no_pull: dep_extra_args += --no-pull
			qdep_no_clone: dep_extra_args += --no-clone
			!isEmpty($${dep_hash}.version): dep_vers_arg = $$system_quote($$first($${dep_hash}.version))
			else: dep_vers_arg =
			qdep_ok = 
			dep_data = $$system($$QDEP_TOOL pkgresolve --project $$dep_extra_args $$system_quote($$dep_pkg) $$dep_vers_arg, lines, qdep_ok)
			!equals(qdep_ok, 0):return(false)
			!equals(dep_hash, $$take_first(dep_data)):error("Cricital internal error: dependencies out of sync"):return(false)
			
			dep_version = $$take_first(dep_data)
			dep_base = $$take_first(dep_data)
			dep_path = $$take_first(dep_data)
			dep_needs_cache = $$take_first(dep_data)
		
			$${dep_hash}.package = $$dep_pkg
			$${dep_hash}.version = $$dep_version
			$${dep_hash}.path = $${dep_base}$${dep_path}
			$${dep_hash}.exports = 
			$${dep_hash}.local = 0
			$${dep_hash}.target = sub$${dep_hash}
			export($${dep_hash}.package)
			export($${dep_hash}.version)
			export($${dep_hash}.path)
			export($${dep_hash}.local)
			export($${dep_hash}.target)
			
			# Cache the package version for dependencies with undetermined versions
			!qdep_no_cache:equals(dep_needs_cache, True):!cache($${dep_hash}.version, set $$QDEP_CACHE_SCOPE):warning("Failed to cache package version for $$dep_pkg")
			
			# link the project and write the version if not already there
			exists("$$_PRO_FILE_PWD_/.qdep/$${dep_hash}/.version"): linked_version = $$cat("$$_PRO_FILE_PWD_/.qdep/$${dep_hash}/.version", lines)
			else: linked_version =			
			qdep_ok = 
			!equals($${dep_hash}.version, $$linked_version) {
				$${dep_hash}.file = $$system($$QDEP_TOOL prolink --link $$system_quote($${dep_base}) $$system_quote($$_PRO_FILE_PWD_) $${dep_hash} $$system_quote($${dep_path}), lines, qdep_ok)
				!equals(qdep_ok, 0):return(false)
				!write_file("$$_PRO_FILE_PWD_/.qdep/$${dep_hash}/.version", $${dep_hash}.version): \\
					error("Failed to cache project dependency version for $$first($${dep_hash}.package)")
			} else {
				$${dep_hash}.file = $$system($$QDEP_TOOL prolink $$system_quote($$_PRO_FILE_PWD_) $${dep_hash} $$system_quote($${dep_path}), lines, qdep_ok)
				!equals(qdep_ok, 0):return(false)
			}
			export($${dep_hash}.file)
			
			# Find all further project dependencies that package depends on
			sub_deps = $$fromfile($$eval($${dep_hash}.path), QDEP_PROJECT_DEPENDS)
			!isEmpty(sub_deps) {
				qdep_ok = 
				$${dep_hash}.depends = $$system($$QDEP_TOOL dephash --project $$sub_deps, lines, qdep_ok)
				!equals(qdep_ok, 0):return(false)
				export($${dep_hash}.depends)
			}
			SUBDIRS += $${dep_hash}
			export(SUBDIRS)
			__QDEP_INCLUDE_CACHE += $${dep_hash}
			export(__QDEP_INCLUDE_CACHE)
			
			# calls this method recursively for all dependencies
			!qdepCollectProjectDependencies($$sub_deps):return(false)	
		} else: \\
			!equals(dep_version, $$first($${dep_hash}.version)): \\
			warning("Detected includes of multiple different versions of the same dependency. Package \\"$$first($${dep_hash}.package)\\" is used, and version \\"$$dep_version\\" was detected.")
	}
	
	return(true)
}

# resolve qdep_depends of subdir dependencies to the actual hashes
defineTest(qdepResolveSubdirDepends) {
	for(subproj, 1) {
		!isEmpty($${subproj}.qdep_depends) {
			qdep_dependencies = 
			for(arg, $${subproj}.qdep_depends): qdep_dependencies += $$system_quote($$arg)
			qdep_ok = 
			$${subproj}.depends += $$system($$QDEP_TOOL dephash --project $$qdep_dependencies, lines, qdep_ok)
			!equals(qdep_ok, 0):return(false)
			export($${subproj}.depends)
		}
	}
	return(true)
}

# pass the root dir and dependencies and create QDEP_LINK_DEPENDS values from it
defineReplace(qdepResolveProjectLinkDeps) {
	qdep_dependencies = 
	for(arg, 2): qdep_dependencies += $$system_quote($$arg)
	qdep_ok = 
	dep_tuples = $$system($$QDEP_TOOL dephash --project --pkgpath $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return()
	
	link_paths = 
	for(qdep_tuple, dep_tuples) {
		tpl_args = $$split(qdep_tuple, ";")
		dep_hash = $$take_first(tpl_args)
		dep_path = $$join(tpl_args, ";")
		qdep_ok = 
		link_paths += $$system($$QDEP_TOOL prolink $$system_quote($$absolute_path($$1, $$_PRO_FILE_PWD_)) $${dep_hash} $$system_quote($${dep_path}), lines, qdep_ok)
		!equals(qdep_ok, 0):return()
	}
	
	return($$link_paths)
}

# Write a quoted value for the given variable name as a single value
defineReplace(qdepOutQuote) {
	result = 
	var_name = $$1
	for(value, 2): result += "$$var_name += $${LITERAL_DOLLAR}$${LITERAL_DOLLAR}quote($$value)"
	return($$result)
}

# A function to create a pri file to include the library and all exported
defineTest(qdepCreateExportPri) {
	# write basic variables
	out_file_data = 
	out_file_data += $$qdepOutQuote(DEFINES, $$QDEP_EXPORTED_DEFINES $$QDEP_DEFINES)
	out_file_data += $$qdepOutQuote(INCLUDEPATH, $$QDEP_EXPORTED_INCLUDEPATH $$QDEP_INCLUDEPATH)
	for(exp_var_key, QDEP_VAR_EXPORTS): out_file_data += $$qdepOutQuote($$exp_var_key, $$eval($$exp_var_key))
	
	# write package cache
	for(dep_hash, __QDEP_INCLUDE_CACHE):equals($${dep_hash}.local, 1) {
		out_file_data += $$qdepOutQuote($${dep_hash}.package, $$eval($${dep_hash}.package))
		out_file_data += $$qdepOutQuote($${dep_hash}.version, $$eval($${dep_hash}.version))
		out_file_data += $$qdepOutQuote($${dep_hash}.path, $$eval($${dep_hash}.path))
		out_file_data += $$qdepOutQuote($${dep_hash}.exports, $$eval($${dep_hash}.exports))
		out_file_data += $$qdepOutQuote($${dep_hash}.local, 0)
		out_file_data += $$qdepOutQuote(__QDEP_INCLUDE_CACHE, $$dep_hash)
	}
	
	# write startup hooks
	static|staticlib {
		debug_and_release:CONFIG(release, debug|release): out_file_data += "$$qdepOutQuote(__QDEP_HOOK_FILES, $$QDEP_GENERATED_DIR/release/qdep_$${TARGET}_hooks.h)"
		else:debug_and_release:CONFIG(debug, debug|release): out_file_data += "$$qdepOutQuote(__QDEP_HOOK_FILES, $$QDEP_GENERATED_DIR/debug/qdep_$${TARGET}_hooks.h)"
		else: out_file_data += "$$qdepOutQuote(__QDEP_HOOK_FILES, $$QDEP_GENERATED_DIR/qdep_$${TARGET}_hooks.h)"
	}
	
	# write library linkage
	!qdep_no_link {
		out_file_data += $$qdepOutQuote(INCLUDEPATH, $$_PRO_FILE_PWD_)
		
		isEmpty(DESTDIR) {
			out_libdir = $$OUT_PWD
			debug_and_release:CONFIG(release, debug|release): out_libdir = $${out_libdir}/release
			else:debug_and_release:CONFIG(debug, debug|release): out_libdir = $${out_libdir}/debug
		} else: out_libdir = $$absolute_path($$DESTDIR, $$OUT_PWD)
		
		out_file_data += $$qdepOutQuote(LIBS, "-L$${out_libdir}/")
		equals(TEMPLATE, lib):out_file_data += $$qdepOutQuote(LIBS, "-l$${TARGET}")
		else {
			win32: bin_suffix = .exe
			out_file_data += $$qdepOutQuote(LIBS, "-l:$${TARGET}$${bin_suffix}")
		}
		
		static|staticlib {
			out_file_data += $$qdepOutQuote(DEPENDPATH, $$_PRO_FILE_PWD_)
			
			win32-g++: out_file_data += $$qdepOutQuote(PRE_TARGETDEPS, "$${out_libdir}/lib$${TARGET}.a")
			else:win32: out_file_data += $$qdepOutQuote(PRE_TARGETDEPS, "$${out_libdir}/$${TARGET}.lib")
			else:unix: out_file_data += $$qdepOutQuote(PRE_TARGETDEPS, "$${out_libdir}/lib$${TARGET}.a")
		}
	}
	
	write_file($$1, out_file_data):return(true)
	else:return(false)
}

# get the full pri path of a link dependency
defineReplace(qdepLinkExpand) {
	base_path = $$1
	suffix = $$str_member($$base_path, -4, -1)
	
	!equals(suffix, ".pri") {
		equals(suffix, ".pro") {
			file_name = $$basename(base_path)
			file_name = "$$str_member($$file_name, 0, -5)_export.pri"
			base_path = $$dirname(base_path)
		} else {
			file_name = "$$basename(base_path)_export.pri"
		}
		debug_and_release:CONFIG(release, debug|release): base_path = $$base_path/release/$$file_name
		else:debug_and_release:CONFIG(debug, debug|release):  base_path = $$base_path/debug/$$file_name
		else: base_path = $$base_path/$$file_name
	}

	base_path = $$absolute_path($$base_path, $$_PRO_FILE_PWD_)
	s_base_path = $$shadowed($$base_path)
	!isEmpty(s_base_path):exists($$s_base_path):return($$s_base_path)
	else:!isEmpty(base_path):exists($$base_path):return($$base_path)
	else:return()
}

# First transform project link depends to normal link depends
!isEmpty(QDEP_PROJECT_ROOT): \\
	!isEmpty(QDEP_PROJECT_LINK_DEPENDS): \\
	QDEP_LINK_DEPENDS = $$qdepResolveProjectLinkDeps($$QDEP_PROJECT_ROOT, $$QDEP_PROJECT_LINK_DEPENDS) $$QDEP_LINK_DEPENDS  # always prepend project link depends
message("*** $$QDEP_LINK_DEPENDS")

# Next collect all indirect dependencies
!isEmpty(QDEP_LINK_DEPENDS): \\
	for(link_dep, QDEP_LINK_DEPENDS): \\
	!include($$qdepLinkExpand($$link_dep)): \\
	error("Failed to include linked library $$link_dep")

# Collect all dependencies and then include them
!isEmpty(QDEP_DEPENDS): {
	__qdep_cached_hooks = $$QDEP_HOOK_FNS
	QDEP_HOOK_FNS = 
	__qdep_cached_resources = $$RESOURCES
	RESOURCES = 
	
	!qdepCollectDependencies($$QDEP_DEPENDS):error("Failed to collect all dependencies")
	else:for(dep, __QDEP_INCLUDE_CACHE):equals($${dep}.local, 1) {
		__qdep_define_offset = $$size(DEFINES)
		__qdep_include_offset = $$size(INCLUDEPATH)
		include($$first($${dep}.path)) {
			qdep_export_all|contains(QDEP_EXPORTS, $$first($${dep}.package)) {
				QDEP_EXPORTED_DEFINES += $$member(DEFINES, $$__qdep_define_offset, -1)
				export(QDEP_EXPORTED_DEFINES)
				QDEP_EXPORTED_INCLUDEPATH += $$member(INCLUDEPATH, $$__qdep_include_offset, -1)
				export(QDEP_EXPORTED_INCLUDEPATH)
			}
		} else:error("Failed to include pri file $$first($${dep}.package)")
	}
	
	QDEP_HOOK_FNS += $$__qdep_cached_hooks
	RESOURCES += $$__qdep_cached_resources
}

# Collect all project dependencies
equals(TEMPLATE, subdirs):!isEmpty(QDEP_PROJECT_DEPENDS) {
	!qdepCollectProjectDependencies($$QDEP_PROJECT_DEPENDS): \\
		error("Failed to collect all project dependencies")
	!qdepResolveSubdirDepends($$SUBDIRS): \\
		error("Failed to link all project dependencies")
}

# create special target for resource hooks in static libs
# or if not, reference their hooks of static libs (as special compiler, only for non-static apps/libs)
static|staticlib:equals(TEMPLATE, lib) {
	__qdep_hook_generator_c.name = qdep hookgen ${QMAKE_FILE_IN}
	__qdep_hook_generator_c.input = _PRO_FILE_ RESOURCES 
	__qdep_hook_generator_c.variable_out = HEADERS
	__qdep_hook_generator_c.commands = $$QDEP_TOOL hookgen --hooks $$QDEP_HOOK_FNS -- $${TARGET} ${QMAKE_FILE_OUT} ${QMAKE_FILE_IN}
	__qdep_hook_generator_c.output = $$QDEP_GENERATED_SOURCES_DIR/qdep_$${TARGET}_hooks.h
	__qdep_hook_generator_c.CONFIG += target_predeps combine no_link
	__qdep_hook_generator_c.depends += $$QDEP_PATH
	QMAKE_EXTRA_COMPILERS += __qdep_hook_generator_c
} else {
	__qdep_hook_importer_c.name = qdep hookimp ${QMAKE_FILE_IN}
	__qdep_hook_importer_c.input = _PRO_FILE_ __QDEP_HOOK_FILES
	__qdep_hook_importer_c.variable_out = GENERATED_SOURCES
	__qdep_hook_importer_c.commands = $$QDEP_TOOL hookimp --hooks $$QDEP_HOOK_FNS -- ${QMAKE_FILE_OUT} ${QMAKE_FILE_IN}
	__qdep_hook_importer_c.output = $$QDEP_GENERATED_SOURCES_DIR/qdep_imported_hooks.cpp
	__qdep_hook_importer_c.CONFIG += target_predeps combine
	__qdep_hook_importer_c.depends += $$QDEP_PATH
	QMAKE_EXTRA_COMPILERS += __qdep_hook_importer_c
}

# fix for broken lrelease make feature
{
	isEmpty(LRELEASE_DIR): LRELEASE_DIR = .qm
	debug_and_release:CONFIG(release, debug|release): __qdep_lrelease_real_dir = $${LRELEASE_DIR}/release
	else:debug_and_release:CONFIG(debug, debug|release): __qdep_lrelease_real_dir = $${LRELEASE_DIR}/debug
	else: __qdep_lrelease_real_dir = $$LRELEASE_DIR
	__qdep_lrelease_real_dir = $$absolute_path($$__qdep_lrelease_real_dir, $$OUT_PWD)
	!exists($$__qdep_lrelease_real_dir): \\
		!mkpath($$__qdep_lrelease_real_dir): \\
		warning("Failed to create lrelease directory: $$__qdep_lrelease_real_dir")
}
qm_files.CONFIG += no_check_exist

# Create special targets for translations
!qdep_no_qm_combine {
	# move translations into temporary var for the compiler to work
	__QDEP_ORIGINAL_TRANSLATIONS = $$TRANSLATIONS
	TRANSLATIONS = 

	# compiler for combined translations
	__qdep_ts_tmp = 
	for(tsfile, QDEP_TRANSLATIONS) __qdep_ts_tmp += $$system_quote($$tsfile)
	__qdep_qm_combine_c.name = qdep lrelease ${QMAKE_FILE_IN}
	__qdep_qm_combine_c.input = __QDEP_ORIGINAL_TRANSLATIONS 
	__qdep_qm_combine_c.variable_out = TRANSLATIONS
	__qdep_qm_combine_c.commands = $$QDEP_TOOL lconvert --combine $$__qdep_ts_tmp -- ${QMAKE_FILE_IN} ${QMAKE_FILE_OUT} $$QDEP_LCONVERT
	__qdep_qm_combine_c.output = $$QDEP_GENERATED_TS_DIR/${QMAKE_FILE_BASE}.ts
	__qdep_qm_combine_c.CONFIG += no_link
	__qdep_qm_combine_c.depends += $$QDEP_PATH $$QDEP_LCONVERT_EXE $$QDEP_TRANSLATIONS
	QMAKE_EXTRA_COMPILERS += __qdep_qm_combine_c
	
	# copy from lrelease.prf - needed as TRANSLATIONS is now empty
	for(translation, $$list($$__QDEP_ORIGINAL_TRANSLATIONS $$EXTRA_TRANSLATIONS)) {
		translation = $$basename(translation)
		QM_FILES += $$__qdep_lrelease_real_dir/$$replace(translation, \\\\..*$, .qm)
	}
} else {
	# add qdep translations to extra to allow lrelease processing
	EXTRA_TRANSLATIONS += $$QDEP_TRANSLATIONS
}

# Create qdep pri export, if modules should be exported
equals(TEMPLATE, lib):!qdep_no_link|qdep_export_all|!isEmpty(QDEP_EXPORTS): \\
	!qdepCreateExportPri($$QDEP_EXPORT_PATH/$$QDEP_EXPORT_NAME): \\
	error("Failed to create export file $$QDEP_EXPORT_FILE")

DEFINES += $$QDEP_DEFINES
INCLUDEPATH += $$QDEP_INCLUDEPATH
"""

if __name__ == '__main__':
	main()
