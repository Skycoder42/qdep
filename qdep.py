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
		def __init__(self, path):
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
	for env_info in or_env.split("}"):
		env_pair = env_info.split("{")
		if len(env_pair) == 2:
			or_map[env_pair[0]] = env_pair[1]
	return or_map


def package_resolve(packages, suffix=".pri"):
	or_map = get_override_map()
	pattern = re.compile(r'^(?:([^@\/]+\/[^@\/]+)|([^@]*@[^@]*:[^@\/]+\/[^@\/]+\.git|\w+:\/\/[^@]*\.git))(?:@([^\/]+)(\/.*)?)?$')
	path_pattern = re.compile(r'^.*\/([^\/]+)\.git$')
	pkg_list = []
	for package in packages:
		package = or_map[package] if package in or_map else package
		match = re.match(pattern, package)
		if not match:
			raise Exception("Given package is not a valid package descriptor: " + package)

		# extract package url
		if match.group(1) is not None:
			pkg_url = "https://github.com/{}.git".format(match.group(1))
		elif match.group(2) is not None:
			pkg_url = match.group(2)
		else:
			raise Exception("Invalid package specified: " + package)

		# extract branch
		if match.group(3) is not None:
			pkg_branch = match.group(3)
		else:
			pkg_branch = None

		# extract pri path
		if match.group(4) is not None:
			pkg_path = match.group(4)
		else:
			pkg_path = "/" + re.match(path_pattern, pkg_url).group(1) + suffix

		pkg_list.append((pkg_url, pkg_branch, pkg_path))
	return pkg_list


def get_all_tags(pkg_url):
	ls_res = subprocess.run(["git", "ls-remote", "--tags", "--exit-code", pkg_url], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	ref_pattern = re.compile(r'[a-fA-F0-9]+\s+refs\/tags\/([^\s]+)')
	tags = []
	for match in re.finditer(ref_pattern, ls_res.stdout):
		tags.append(match.group(1))
	return tags


def get_latest_tag(pkg_url):
	return get_all_tags(pkg_url)[-1]


def get_sources(pkg_url, pkg_branch):
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
			head_ref_res = subprocess.run(["git", "symbolic-ref", "HEAD"], cwd=cache_dir, stdout=subprocess.DEVNULL)
			if head_ref_res.returncode == 0:
				subprocess.run(["git", "pull", "--force", "--ff-only", "--update-shallow", "--recurse-submodules"], cwd=cache_dir, stdout=subprocess.DEVNULL, check=True)
				needs_ro = True
		else:
			subprocess.run(["git", "clone", "--recurse-submodules", "--shallow-submodules", "--depth", "1", "--branch", pkg_branch, pkg_url, cache_dir], check=True)
			needs_ro = True

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
		git_repo_cache.remove(cache_dir)
	finally:
		locker.release()

	git_repo_cache.add(cache_dir)
	return cache_dir


def prfgen(arguments):
	qmake_res = subprocess.run([arguments.qmake, "-query", "QT_HOST_DATA"], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	prf_path = path.join(str(qmake_res.stdout).strip(), "mkspecs", "features", "qdep.prf")
	print("Generating PRF-File as: ", prf_path)
	with open(prf_path, "w") as prf_file:
		self_path = path.abspath(__file__)
		prf_file.write(qdep_prf.format(self_path, self_path))
	return 0


def pri_resolve(arguments):
	for pkg_url, pkg_branch, pkg_path in package_resolve(arguments.input):
		# get the sources
		pkg_base = get_sources(pkg_url, pkg_branch)
		pkg_base = os.path.join(pkg_base, pkg_path[1:])
		print(hashlib.sha3_512(pkg_base.encode("UTF-8")).hexdigest(), pkg_base)
	return 0


def main():
	parser = argparse.ArgumentParser(description="A very basic yet simple to use dependency management tool for qmake based projects")
	parser.add_argument("-v", "--version", action="version", version='%(prog)s 1.0')
	parser.add_argument("--qmake", action="store", default="qmake", help="The path to a qmake executable to place the prf file for")
	parser.add_argument("operation", action="store", choices=["prfgen", "pri-resolve"], metavar="operation", help="Specify the operation that should be performed by qdep")
	parser.add_argument("input", action="store", nargs="*", metavar="packages", help="Package descriptors to be processed by qdep")

	res = parser.parse_args()
	if res.operation == "prfgen":
		result = prfgen(res)
	elif res.operation == "pri-resolve":
		result = pri_resolve(res)
	else:
		result = -1
	sys.exit(result)


qdep_prf = """# Generated by {}
isEmpty(QDEP_PATH): QDEP_PATH = {}
isEmpty(QDEP_VERSION): QDEP_VERSION = 1.0.0
isEmpty(QDEP_TOOL) {{
	QDEP_TOOL = $$shell_path($$QDEP_PATH) --qmake $$shell_quote($$QMAKE_QMAKE)
	win32: QDEP_TOOL = python $$QDEP_TOOL
}}

defineTest(qdepCollectDependencies) {{
	qdep_dependencies = 
	for(arg, ARGS): qdep_dependencies += $$shell_quote($$arg)
	qdep_paths = $$system($$QDEP_PATH pri-resolve $$qdep_dependencies, lines, qdep_ok)
	!equals(qdep_ok, 0):return(false)
	
	for(dep, qdep_paths) {{
		dep_parts = $$split(dep, " ")
		dep_hash = $$take_first(dep_parts)
		
		!contains(__QDEP_INCLUDE_CACHE, $$dep_hash) {{
			__QDEP_INCLUDE_CACHE += $$dep_hash
			export(__QDEP_INCLUDE_CACHE)
			
			dep_path = $$join(dep_parts, " ")
			sub_deps = $$fromfile($$dep_path, QDEP_DEPENDS)
			__QDEP_REAL_DEPS_STACK += $$dep_path
			
			!isEmpty(sub_deps):!qdepCollectDependencies($$sub_deps):return(false)
			
			__QDEP_REAL_DEPS += $$take_last(__QDEP_REAL_DEPS_STACK)
			export(__QDEP_REAL_DEPS)
		}}
	}}
	
	return(true)
}}

!isEmpty(QDEP_DEPENDS): {{
	!qdepCollectDependencies($$QDEP_DEPENDS):error("Failed to collect all dependencies")
	else: \\
		for(dep, __QDEP_REAL_DEPS): \\
		!include($$dep): \\
		error("Failed to include pri file $$dep")
}}
"""

if __name__ == '__main__':
	main()
