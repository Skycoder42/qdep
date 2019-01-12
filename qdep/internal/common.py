import hashlib
import os
import re
import shutil
import stat
import subprocess
import tempfile
from os import path

import appdirs
from lockfile import LockFile


def get_cache_dir_default():
	return appdirs.user_cache_dir("qdep")


def get_cache_dir(pkg_url, pkg_branch):
	cache_dir = os.getenv("QDEP_CACHE_DIR", get_cache_dir_default())
	cache_dir = path.join(cache_dir, hashlib.sha3_256(pkg_url.encode("UTF-8")).hexdigest(), pkg_branch)
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


def get_all_tags(pkg_url, branches=False, tags=True, allow_empty=False):
	ls_args = ["git", "ls-remote", "--refs"]
	if not branches and tags:
		ls_args.append("--tags")
	elif not tags and branches:
		ls_args.append("--heads")
	if not allow_empty:
		ls_args.append("--exit-code")
	elif not tags and not branches:
		return []  # Nothing to check for
	ls_args.append(pkg_url)

	ls_res = subprocess.run(ls_args, check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	ref_pattern = re.compile(r'[a-fA-F0-9]+\s+refs\/(?:tags|heads)\/([^\s]+)')
	tags = []
	for match in re.finditer(ref_pattern, ls_res.stdout):
		tags.append(match.group(1))
	return tags


def get_latest_tag(pkg_url, allow_empty=False):
	all_tags = get_all_tags(pkg_url, allow_empty=allow_empty)
	if len(all_tags) > 0:
		return all_tags[-1]
	else:
		return None


def get_sources(pkg_url, pkg_branch, pull=True, clone=True):

	if pkg_branch is None:
		pkg_branch = get_latest_tag(pkg_url)

	cache_dir = get_cache_dir(pkg_url, pkg_branch)

	locker = LockFile(cache_dir)
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


def eval_pro_file(pro_file, qmake, make, full_eval=False):
	packages = []

	with tempfile.TemporaryDirectory() as tmp_dir:
		if full_eval:
			print("Running {} on {}...".format(qmake, pro_file))
			subprocess.run([qmake, pro_file], cwd=tmp_dir, check=True, stdout=subprocess.DEVNULL)
			print("Running {} qmake_all...".format(make))
			subprocess.run([make, "qmake_all"], cwd=tmp_dir, check=True, stdout=subprocess.DEVNULL)
			print("Done! qmake finished successfully, all qdep sources have been downloaded.")
		else:
			print("Evaluating pro file {}...".format(pro_file))
			dump_name = path.join(tmp_dir, "qdep_dummy.pro")
			with open(dump_name, "w") as dump_file:
				dump_file.write("QDEP_DEPENDS = $$fromfile($$quote({}), QDEP_DEPENDS)\n".format(pro_file))
				dump_file.write("!write_file($$PWD/qdep_depends.txt, QDEP_DEPENDS):error(\"write error\")\n")
			subprocess.run([qmake, dump_name], cwd=tmp_dir, check=True, stdout=subprocess.DEVNULL)
			with open(path.join(tmp_dir, "qdep_depends.txt"), "r") as dep_file:
				for line in dep_file.readlines():
					packages.append(line.strip())
			print("Done! Extracted {} dependencies".format(len(packages)))

	return packages
