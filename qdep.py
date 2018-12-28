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
			
			qdep_export_all|contains(QDEP_EXPORTS, $$dep_pkg) {{
				!static:!staticlib:for(sub_export, sub_exports) {{
					DEFINES += "$${{sub_export}}=Q_DECL_EXPORT"
					QDEP_EXPORTED_DEFINES += "$${{sub_export}}=Q_DECL_IMPORT"
					$${{dep_hash}}.exports += $$sub_export
				}} else:for(sub_export, sub_exports) {{
					DEFINES += "$${{sub_export}}="
					QDEP_EXPORTED_DEFINES += "$${{sub_export}}="
				}}
			}} else:for(sub_export, sub_exports): \\
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

defineReplace(qdepOutQuote) {{
	result = 
	var_name = $$1
	for(value, 2): result += "$$var_name += $${{LITERAL_DOLLAR}}$${{LITERAL_DOLLAR}}quote($$value)"
	return($$result)
}}

# A function to create a pri file to include the library and all exported
defineTest(qdepCreateExportPri) {{
	# write basic variables
	out_file_data = 
	out_file_data += $$qdepOutQuote(DEFINES, $$QDEP_EXPORTED_DEFINES $$QDEP_DEFINES)
	out_file_data += $$qdepOutQuote(INCLUDEPATH, $$QDEP_EXPORTED_INCLUDEPATH $$QDEP_INCLUDEPATH)
	for(exp_var_key, QDEP_VAR_EXPORTS): out_file_data += $$qdepOutQuote($$exp_var_key, $$eval($$exp_var_key))
	
	# write package cache
	for(dep_hash, __QDEP_INCLUDE_CACHE):equals($${{dep_hash}}.local, 1) {{
		out_file_data += $$qdepOutQuote($${{dep_hash}}.package, $$eval($${{dep_hash}}.package))
		out_file_data += $$qdepOutQuote($${{dep_hash}}.version, $$eval($${{dep_hash}}.version))
		out_file_data += $$qdepOutQuote($${{dep_hash}}.path, $$eval($${{dep_hash}}.path))
		out_file_data += $$qdepOutQuote($${{dep_hash}}.exports, $$eval($${{dep_hash}}.exports))
		out_file_data += $$qdepOutQuote($${{dep_hash}}.local, 0)
		out_file_data += $$qdepOutQuote(__QDEP_INCLUDE_CACHE, $$dep_hash)
	}}
	
	# write library linkage
	!qdep_no_link {{
		out_file_data += $$qdepOutQuote(INCLUDEPATH, $$_PRO_FILE_PWD_)
		
		out_libdir = $$shadowed($$_PRO_FILE_PWD_)
		win32 {{
			out_file_data += "CONFIG(release, debug|release): $$qdepOutQuote(LIBS, "-L$${{out_libdir}}/release/")"
			out_file_data += "else:CONFIG(debug, debug|release): $$qdepOutQuote(LIBS, "-L$${{out_libdir}}/debug/")"
		}} else:unix: out_file_data += $$qdepOutQuote(LIBS, "-L$${{out_libdir}}/")
		out_file_data += $$qdepOutQuote(LIBS, "-l$${{TARGET}}")
		
		static|staticlib {{
			out_file_data += $$qdepOutQuote(DEPENDPATH, $$_PRO_FILE_PWD_)
			
			win32-g++ {{
				out_file_data += "CONFIG(release, debug|release): $$qdepOutQuote(PRE_TARGETDEPS, "$${{out_libdir}}/release/lib$${{TARGET}}.a")"
				out_file_data += "else:CONFIG(debug, debug|release): $$qdepOutQuote(PRE_TARGETDEPS, "$${{out_libdir}}/debug/lib$${{TARGET}}.a")"
			}} else:win32:!win32-g++ {{
				out_file_data += "CONFIG(release, debug|release): $$qdepOutQuote(PRE_TARGETDEPS, "$${{out_libdir}}/release/$${{TARGET}}.lib")"
				out_file_data += "else:CONFIG(debug, debug|release): $$qdepOutQuote(PRE_TARGETDEPS, "$${{out_libdir}}/debug/$${{TARGET}}.lib")"
			}} else:unix: out_file_data += $$qdepOutQuote(PRE_TARGETDEPS, "$${{out_libdir}}/lib$${{TARGET}}.a")
		}}
	}}
	
	write_file($$first(ARGS), out_file_data):return(true)
	else:return(false)
}}

# get the full pri path of a link dependency
defineReplace(qdepLinkExpand) {{
	base_path = $$1
	suffix = $$str_member($$base_path, -4, -1)
	equals(suffix, ".pro"): base_path = "$$str_member(base_path, 0, -5)_export.pri"
	else:!equals(suffix, ".pri"): base_path = "$${{base_path}}/$$dirname(base_path)_export.pri"
	base_path = $$absolute_path($$base_path, $$_PRO_FILE_PWD_)
	s_base_path = $$shadowed($$base_path)
	!isEmpty(s_base_path):exists($$s_base_path):return($$s_base_path)
	else:!isEmpty(base_path):exists($$base_path):return($$base_path)
	else:return()
}}

# First collect all indirect dependencies
!isEmpty(QDEP_LINK_DEPENDS): \\
	for(link_dep, QDEP_LINK_DEPENDS): \\
	!include($$qdepLinkExpand($$link_dep)): \\
	error("Failed to include linked library $$link_dep")

# Collect all dependencies and then include them
!isEmpty(QDEP_DEPENDS): {{
	!qdepCollectDependencies($$QDEP_DEPENDS):error("Failed to collect all dependencies")
	else:for(dep, __QDEP_INCLUDE_CACHE):equals($${{dep}}.local, 1) {{
		__qdep_define_offset = $$size(DEFINES)
		__qdep_include_offset = $$size(INCLUDEPATH)
		include($$first($${{dep}}.path)) {{
			qdep_export_all|contains(QDEP_EXPORTS, $$first($${{dep}}.package)) {{
				QDEP_EXPORTED_DEFINES += $$member(DEFINES, $$__qdep_define_offset, -1)
				export(QDEP_EXPORTED_DEFINES)
				QDEP_EXPORTED_INCLUDEPATH += $$member(INCLUDEPATH, $$__qdep_include_offset, -1)
				export(QDEP_EXPORTED_INCLUDEPATH)
			}}
		}} else:error("Failed to include pri file $$first($${{dep}}.package)")
	}}
}}

qdep_export_all|!isEmpty(QDEP_EXPORTS): \\
	!qdepCreateExportPri($$QDEP_EXPORT_FILE): \\
	error("Failed to create export file $$QDEP_EXPORT_FILE")

DEFINES += $$QDEP_DEFINES
INCLUDEPATH += $$QDEP_INCLUDEPATH
"""

if __name__ == '__main__':
	main()
