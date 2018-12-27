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


# globals
git_repo_cache = set()


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
	return "__QDEP_PKG_" + hashlib.sha3_512((pkg_url + pkg_path).encode("UTF-8")).hexdigest()


def package_resolve(package, pkg_version=None, suffix=".pri"):
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
		pkg_path = "/" + re.match(path_pattern, pkg_url).group(1) + suffix

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
	global git_repo_cache

	if pkg_branch is None:
		pkg_branch = get_latest_tag(pkg_url)

	cache_dir = get_cache_dir(pkg_url, pkg_branch)
	if cache_dir in git_repo_cache:
		return cache_dir

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
		git_repo_cache.discard(cache_dir)
		raise
	finally:
		locker.release()

	git_repo_cache.add(cache_dir)
	return cache_dir, pkg_branch


def prfgen(arguments):
	qmake_res = subprocess.run([arguments.qmake, "-query", "QT_HOST_DATA"], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	prf_path = path.join(str(qmake_res.stdout).strip(), "mkspecs", "features", "qdep.prf")
	print("Generating PRF-File as: ", prf_path)
	with open(prf_path, "w") as prf_file:
		self_path = path.abspath(__file__)
		prf_file.write(qdep_prf.format(self_path, self_path))
	return 0


def pri_resolve(arguments):
	ov_map = get_override_map()
	package = arguments.input[0]
	pkg_version = arguments.input[1] if len(arguments.input[1]) > 0 else None

	pkg_url, pkg_branch, pkg_path = package_resolve(package, pkg_version=pkg_version)
	needs_cache = pkg_branch is None
	if pkg_url in ov_map:
		pkg_base = ov_map[pkg_url]
	else:
		pkg_base, pkg_branch = get_sources(pkg_url, pkg_branch, pull=arguments.pull, clone=arguments.clone)
	pkg_base = os.path.join(pkg_base, pkg_path[1:])
	print(pkg_hash(pkg_url, pkg_path))
	print(pkg_branch)
	print(pkg_base)
	print(needs_cache)
	return 0


def dephash(arguments):
	for package in arguments.input:
		pkg_url, pkg_branch, pkg_path = package_resolve(package)
		print(pkg_hash(pkg_url, pkg_path))
	return 0


def main():
	parser = argparse.ArgumentParser(description="A very basic yet simple to use dependency management tool for qmake based projects")
	parser.add_argument("-v", "--version", action="version", version="%(prog)s 1.0.0")
	parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to place the prf file for")
	parser.add_argument("--no-pull", dest="pull", action="store_false", help="Do not update existing packages that are based on branches instead of tags.")
	parser.add_argument("--no-clone", dest="clone", action="store_false", help="Do not allow installation of new packages. Trying so will lead to an error. Updating existing packages is still possible")
	parser.add_argument("operation", action="store", choices=["prfgen", "dephash", "pri-resolve"], metavar="operation", help="Specify the operation that should be performed by qdep")
	parser.add_argument("input", action="store", nargs="*", metavar="packages", help="Package descriptors to be processed by qdep")

	res = parser.parse_args()
	if res.operation == "prfgen":
		result = prfgen(res)
	elif res.operation == "dephash":
		result = dephash(res)
	elif res.operation == "pri-resolve":
		result = pri_resolve(res)
	else:
		result = -1
	sys.exit(result)


qdep_prf = """# Generated by {}
isEmpty(QDEP_PATH): QDEP_PATH = {}
isEmpty(QDEP_VERSION): QDEP_VERSION = 1.0.0
isEmpty(QDEP_CACHE_SCOPE): QDEP_CACHE_SCOPE = stash
isEmpty(QDEP_TOOL) {{
	win32: QDEP_TOOL = python "\"$$QDEP_PATH\""
	else: QDEP_TOOL = $$shell_path($$QDEP_PATH)
	QDEP_TOOL += --qmake $$shell_quote($$QMAKE_QMAKE)
	qdep_no_pull: QDEP_TOOL += --no-pull
	qdep_no_clone: QDEP_TOOL += --no-clone
}}
isEmpty(QDEP_EXPORT_FILE): QDEP_EXPORT_FILE = $$shadowed($$absolute_path($$lower("$${{TARGET}}_export.pri"), $$_PRO_FILE_PWD_))
isEmpty(__QDEP_PRIVATE_SEPERATOR): __QDEP_PRIVATE_SEPERATOR = "==="
isEmpty(__QDEP_TUPLE_SEPERATOR): __QDEP_TUPLE_SEPERATOR = "---"

CONFIG += qdep_build

# The primary dependecy collector function
defineTest(qdepCollectDependencies) {{
	# transform all dependencies into unique hashes
	qdep_dependencies = 
	for(arg, ARGS): qdep_dependencies += $$shell_quote($$arg)
	qdep_hashes = $$system($$QDEP_TOOL dephash $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return(false)
	
	for(dep_hash, qdep_hashes) {{
		# handle each dependency, but each package only once
		dep_pkg = $$take_first(ARGS)
		!contains(__QDEP_INCLUDE_CACHE, $$dep_hash) {{
			# Install the sources and extract some parameters
			dep_data = $$system($$QDEP_TOOL pri-resolve $$dep_pkg $$shell_quote($$first($${{dep_hash}}.version)), lines, qdep_ok)
			!equals(qdep_ok, 0):return(false)
			!equals(dep_hash, $$take_first(dep_data)):error("Cricital internal error: dependencies out of sync"):return(false)
			
			dep_version = $$take_first(dep_data)
			dep_path = $$take_first(dep_data)
			dep_needs_cache = $$take_first(dep_data)
		
			$${{dep_hash}}.package = $$dep_pkg
			$${{dep_hash}}.version = $$dep_version
			$${{dep_hash}}.path = $$dep_path
			$${{dep_hash}}.exports = 
			$${{dep_hash}}.local = 1
			export($${{dep_hash}}.package)
			export($${{dep_hash}}.version)
			export($${{dep_hash}}.path)
			export($${{dep_hash}}.local)
			
			# Cache the package version for dependencies with undetermined versions
			!qdep_no_cache:equals(dep_needs_cache, True):!cache($${{dep_hash}}.version, set $$QDEP_CACHE_SCOPE):warning("Failed to cache package version for $$dep_pkg")
			
			# Find all dependencies that package depends on and call this method recursively for those
			sub_deps = $$fromfile($$dep_path, QDEP_DEPENDS)
			__QDEP_REAL_DEPS_STACK += $$dep_hash			
			!isEmpty(sub_deps):!qdepCollectDependencies($$sub_deps):return(false)			
			__QDEP_INCLUDE_CACHE *= $$take_last(__QDEP_REAL_DEPS_STACK)
			export(__QDEP_INCLUDE_CACHE)
			
			# Handle all defines for symbol exports, if specified
			sub_exports = $$fromfile($$dep_path, QDEP_PACKAGE_EXPORTS)
			
			!static:!staticlib: \\
				qdep_export_all|contains(QDEP_EXPORTS, $$dep_pkg): \\
				for(sub_export, sub_exports) {{
					DEFINES += "$${{sub_export}}=Q_DECL_EXPORT"
					QDEP_EXPORTED_DEFINES += "$${{sub_export}}=Q_DECL_IMPORT"
					$${{dep_hash}}.exports += $$sub_export
			}} else: \\
				for(sub_export, sub_exports): \\
				DEFINES += "$${{sub_export}}="
			export(DEFINES)
			export(QDEP_EXPORTED_DEFINES)
			export($${{dep_hash}}.exports)
		}} else: \\
			!equals(dep_version, $$first($${{dep_hash}}.version)): \\
			warning("Detected includes of multiple different versions of the same dependency. Package \\"$$first($${{dep_hash}}.package)\\" is used, and version \\"$$dep_version\\" was detected.")
	}}
	
	return(true)
}}

# A function to create a pri file to include the library and all exported
defineTest(qdepCreateExportPri) {{	
	out_file_data = 
	out_file_data += "DEFINES += $$QDEP_EXPORTED_DEFINES $$QDEP_DEFINES"
	out_file_data += "INCLUDEPATH += $$QDEP_EXPORTED_INCLUDEPATH $$QDEP_INCLUDEPATH"
	for(exp_var, QDEP_VAR_EXPORTS): out_file_data += "$$exp_var += $$member($$exp_var, 0, -1)"
	write_file($$first(ARGS), out_file_data):return(true)
	else:return(false)
}}

# A function to get includepath, defines and others from indirect dependencies
defineTest(qdepCollectLinkDependencies) {{
	for(link_proj, ARGS) {{
		# get all dependencies from the link project and the corresponding internal stuff
		proj_path = $$absolute_path($$link_proj, $$_PRO_FILE_PWD_)
		link_depends = $$fromfile($$proj_path, __QDEP_PRIVATE_VARS_EXPORT)
		!qdepSplitPrivateVar(__qdep_tmp_priv_vars, $$link_depends)
		
		# update project vars from extracted stuff
		DEFINES += $${{__qdep_tmp_priv_vars.defines}}
		INCLUDEPATH += $${{__qdep_tmp_priv_vars.includepath}}
		for(dep_hash, __qdep_tmp_priv_vars.include_cache) {{
			!contains(__QDEP_INCLUDE_CACHE, $$dep_hash) {{
				DEFINES += $$fromfile($$first($${{dep_hash}}.path), DEFINES)
				INCLUDEPATH += $$fromfile($$first($${{dep_hash}}.path), INCLUDEPATH)
				qdep_extra_vars = $$fromfile($$first($${{dep_hash}}.path), QDEP_VAR_EXPORTS)
				for(extra_var, qdep_extra_vars) {{
					$${{extra_var}} += $$fromfile($$first($${{dep_hash}}.path), $${{extra_var}})
					export($${{extra_var}})
				}}
			
				# Handle all defines for symbol exports, if specified
				sub_exports = $$fromfile($$first($${{dep_hash}}.path), QDEP_PACKAGE_EXPORTS)
				for(sub_export, sub_exports) {{
					contains($${{dep_hash}}.exports, $$sub_export): DEFINES += "$${{sub_export}}=Q_DECL_IMPORT"
					else: DEFINES += "$${{sub_export}}="
				}}
				
				$${{dep_hash}}.local = 0
				export($${{dep_hash}}.local)
				__QDEP_INCLUDE_CACHE += $$dep_hash
			}}
		}}
		export(DEFINES)
		export(INCLUDEPATH)
		export(__QDEP_INCLUDE_CACHE)
		
		# link the library, if not disabled
		!qdep_no_link {{
			INCLUDEPATH += $$dirname(proj_path)
			export(INCLUDEPATH)
			
			out_libdir = $$shadowed($$dirname(proj_path))
			win32:CONFIG(release, debug|release): LIBS += "-L$${{out_libdir}}/release/"
			else:win32:CONFIG(debug, debug|release): LIBS += "-L$${{out_libdir}}/debug/"
			else:unix: LIBS += "-L$${{out_libdir}}/"
			LIBS += "-l$${{__qdep_tmp_priv_vars.target}}"
			export(LIBS)
			
			!equals(__qdep_tmp_priv_vars.is_dynamic, 1) {{
				DEPENDPATH += $$dirname(proj_path)
				export(DEPENDPATH)
				
				win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $${{out_libdir}}/release/lib$${{__qdep_tmp_priv_vars.target}}.a
				else:win32-g++:CONFIG(debug, debug|release): PRE_TARGETDEPS += $${{out_libdir}}/debug/lib$${{__qdep_tmp_priv_vars.target}}.a
				else:win32:!win32-g++:CONFIG(release, debug|release): PRE_TARGETDEPS += $${{out_libdir}}/release/$${{__qdep_tmp_priv_vars.target}}.lib
				else:win32:!win32-g++:CONFIG(debug, debug|release): PRE_TARGETDEPS += $${{out_libdir}}/debug/$${{__qdep_tmp_priv_vars.target}}.lib
				else:unix: PRE_TARGETDEPS += $${{out_libdir}}/lib$${{__qdep_tmp_priv_vars.target}}.a
				export(PRE_TARGETDEPS)
			}}
		}}
	}}

	return(true)
}}

# Combines all private qdep vars into one super variable to speed up imports
defineReplace(qdepJoinPrivateVar) {{
	for(dep, __QDEP_INCLUDE_CACHE) {{
		include_dep_tuples += $$dep $$first($${{dep}}.package) $$first($${{dep}}.version) $$first($${{dep}}.path)
		for(exp,  $${{dep}}.exports): include_dep_tuples += $$exp
		include_dep_tuples += $$__QDEP_TUPLE_SEPERATOR
	}}
	static|staticlib: qdep_is_dynamic = 0
	else: qdep_is_dynamic = 1
	return($$include_dep_tuples $$__QDEP_PRIVATE_SEPERATOR $$QDEP_DEFINES $$__QDEP_PRIVATE_SEPERATOR $$QDEP_INCLUDEPATH $$__QDEP_PRIVATE_SEPERATOR $$TARGET $$__QDEP_PRIVATE_SEPERATOR $$qdep_is_dynamic)
}}

# Split previously concatenated qdep vars into the ones passed to the function
defineTest(qdepSplitPrivateVar) {{
	out_var = $$take_first(ARGS)
	state_list = include_cache defines includepath target is_dynamic
	state = $$take_first(state_list)
	inc_state = hash
	$${{out_var}}.$${{state}} = 
	for(arg, ARGS) {{
		equals(arg, $$__QDEP_PRIVATE_SEPERATOR) {{
			export($${{out_var}}.$${{state}})
			state = $$take_first(state_list)
			$${{out_var}}.$${{state}} = 
		}} else:equals(state, include_cache) {{
			equals(arg, $$__QDEP_TUPLE_SEPERATOR) {{
				export($${{current_hash}}.exports)
				inc_state = hash
			}} else:equals(inc_state, hash) {{
				$${{out_var}}.$${{state}} += $$arg
				current_hash = $$arg
				inc_state = package
			}} else:equals(inc_state, package) {{
				$${{current_hash}}.package = $$arg
				export($${{current_hash}}.package)
				inc_state = version
			}} else:equals(inc_state, version) {{
				$${{current_hash}}.version = $$arg
				export($${{current_hash}}.version)
				inc_state = path
			}} else:equals(inc_state, path) {{
				$${{current_hash}}.path = $$arg
				export($${{current_hash}}.path)
				inc_state = exports
			}} else:equals(inc_state, exports) {{
				$${{current_hash}}.exports += $$arg
			}} else:return(false)
		}} else: $${{out_var}}.$${{state}} += $$arg
	}}
	export($${{out_var}}.$${{state}})	
	return(true)
}}

# First collect all indirect dependencies
#!isEmpty(QDEP_LINK_DEPENDS): \\
#	!qdepCollectLinkDependencies($$QDEP_LINK_DEPENDS): \\
#	error("Failed to resolve all QDEP_LINK_DEPENDS")

# Collect all dependencies and then include them
!isEmpty(QDEP_DEPENDS): {{
	!qdepCollectDependencies($$QDEP_DEPENDS):error("Failed to collect all dependencies")
	else:for(dep, __QDEP_INCLUDE_CACHE) {{
		__qdep_define_offset = $$size(DEFINES)
		__qdep_include_offset = $$size(INCLUDEPATH)
		equals($${{dep}}.local, 1):include($$first($${{dep}}.path)) {{
			qdep_export_all|contains(QDEP_EXPORTS, $$first($${{dep}}.package)) {{
				QDEP_EXPORTED_DEFINES += $$member(DEFINES, $$__qdep_define_offset, -1)
				export(QDEP_EXPORTED_DEFINES)
				QDEP_EXPORTED_INCLUDEPATH += $$member(INCLUDEPATH, $$__qdep_include_offset, -1)
				export(QDEP_EXPORTED_INCLUDEPATH)
			}}
		}} else:error("Failed to include pri file $$dep")
	}}
}}

qdep_export_all|!isEmpty(QDEP_EXPORTS):!qdepCreateExportPri($$QDEP_EXPORT_FILE):error("Failed to create export file $$QDEP_EXPORT_FILE")

DEFINES += $$QDEP_DEFINES
INCLUDEPATH += $$QDEP_INCLUDEPATH

# Join private vars
__QDEP_PRIVATE_VARS_EXPORT = $$qdepJoinPrivateVar()
"""

if __name__ == '__main__':
	main()
