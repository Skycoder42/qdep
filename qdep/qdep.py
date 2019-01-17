from qdep.internal.common import *
from qdep.internal.prf import *


version = "1.0.0"


def prfgen(script_path, qmake="qmake", data_dir=None):
	if data_dir is not None:
		prf_path = data_dir
	else:
		qmake_res = sub_run([qmake, "-query", "QT_HOST_DATA"], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
		prf_path = str(qmake_res.stdout).strip()
	prf_path = path.join(prf_path, "mkspecs", "features", "qdep.prf")
	print("Generating PRF-File as: ", prf_path)
	os.makedirs(path.dirname(prf_path), exist_ok=True)
	with open(prf_path, "w") as prf_file:
		prf_file.write("# Generated by {}\n".format(script_path))
		prf_file.write("qdep_force|!isEmpty(OUT_PWD) {  # Used to detect if qdep was loaded from an indirect evaluation\n\n")
		prf_file.write("isEmpty(QDEP_PATH) {\n")
		prf_file.write("\tQDEP_PATH = {}\n".format(script_path))
		prf_file.write("\twin32: QDEP_PATH = $${QDEP_PATH}.exe\n")
		prf_file.write("}\n")
		prf_file.write("isEmpty(QDEP_VERSION): QDEP_VERSION = {}\n".format(version))
		prf_file.write(qdep_prf)
		prf_file.write("\n}\n")


def init(profile):
	with open(profile, "a") as pro_file:
		pro_file.write("\nQDEP_DEPENDS += \n\n")
		pro_file.write("!load(qdep):error(\"Failed to load qdep feature! Run 'qdep.py prfgen --qmake $$QMAKE_QMAKE' to create it.\")\n")


def lupdate(pri_path, qmake="qmake", lupdate_args=None):
	if lupdate_args is None:
		lupdate_args = []

	qmake_res = sub_run([qmake, "-query", "QT_HOST_BINS"], check=True, stdout=subprocess.PIPE, encoding="UTF-8")
	lupdate_path = path.join(str(qmake_res.stdout).strip(), "lupdate")
	with tempfile.TemporaryDirectory() as tmp_dir:
		tmp_pro_path = path.join(tmp_dir, "lupdate.pro")
		with open(tmp_pro_path, "w") as tmp_file:
			tmp_file.write("include({})\n".format(pri_path))
			tmp_file.write("TRANSLATIONS = $$QDEP_TRANSLATIONS\n")
		sub_run([lupdate_path] + lupdate_args + [tmp_pro_path], check=True)


def clear(no_confirm=False):
	def folder_size(path):
		total = 0
		for entry in os.scandir(path):
			if entry.is_file():
				total += entry.stat().st_size
			elif entry.is_dir():
				total += folder_size(entry.path)
		return total

	if not no_confirm:
		print("All caches sources will be removed and have to be downloaded again. Make sure no other qdep instance is currently running!")
		ok = input("Do you really want ro remove all cached sources? [y/N]").lower()
		if len(ok) == 0:
			return
		elif ok != "y" and ok != "yes":
			return

	cache_dir = os.getenv("QDEP_CACHE_DIR", get_cache_dir_default())
	cache_dir = path.join(cache_dir, "src")
	if path.exists(cache_dir):
		rm_size = folder_size(cache_dir)
		shutil.rmtree(cache_dir)
	else:
		rm_size = 0
	print("Removed {} bytes".format(rm_size))


def versions(package, tags=True, branches=False, short=False, limit=None):
	package_url, _v, _p = package_resolve(package)

	if tags:
		pkg_tags = get_all_tags(package_url, tags=True, branches=False, allow_empty=True)
		if limit is not None:
			pkg_tags = pkg_tags[-limit:]
	else:
		pkg_tags = []

	if branches:
		pkg_branches = get_all_tags(package_url, tags=False, branches=True, allow_empty=True)
		if limit is not None:
			pkg_branches = pkg_branches[-limit:]
	else:
		pkg_branches = []

	if short:
		print(" ".join(pkg_branches + pkg_tags))
	else:
		if branches:
			print("Branches:")
			if len(pkg_branches) > 0:
				for branch in pkg_branches:
					print("  " + branch)
			else:
				print(" -- No branches found --")

		if tags:
			if branches:
				print("")

			print("Tags:")
			if len(pkg_tags) > 0:
				for tag in pkg_tags:
					print("  " + tag)
			else:
				print(" -- No tags found --")


def query(package, check=True, print_versions=False, expand=False):
	pkg_url, pkg_version, pkg_path = package_resolve(package)
	if check:
		if pkg_version is None:
			pkg_version = get_latest_tag(pkg_url, allow_empty=True, allow_error=True)
			pkg_exists = pkg_version is not None
		else:
			pkg_exists = pkg_version in get_all_tags(pkg_url, branches=True, tags=True, allow_empty=True, allow_error=True)
	else:
		pkg_exists = False  # not knowing means false

	if expand:
		if pkg_version is None:
			raise Exception("Unable to determine package version")
		else:
			print("{}@{}{}".format(pkg_url, pkg_version, pkg_path))
	else:
		print("Input:", package)
		if pkg_version is not None:
			print("Expanded Name: {}@{}{}".format(pkg_url, pkg_version, pkg_path))
		else:
			print("Expanded Name:", None)
		print("URL:", pkg_url)
		print("Version:", pkg_version)
		print("Path:", pkg_path)
		if check:
			print("Exists:", pkg_exists)

		if print_versions:
			print("")
			versions(package, branches=True)


def get(*targets, extract=False, evaluate=False, recurse=True, qmake="qmake", make="make", cache_dir=None):
	if cache_dir is not None:
		os.environ["QDEP_CACHE_DIR"] = cache_dir

	# eval the pro files if needed
	if evaluate:
		# special case: since we only download sources, a simple qmake run is enough, no actual "evaluation" needed
		for pro_file in targets:
			eval_pro_depends(pro_file, qmake, make)
			print("Done! qmake finished successfully, all qdep sources for the project tree have been downloaded.")
		return
	elif extract:
		packages = []
		for pro_file in targets:
			print("Extracting dependencies from {}...".format(pro_file))
			packages = packages + extract_pro_depends(pro_file, qmake)
	else:
		packages = list(targets)

	# download the actual sources
	print("Found {} initial packages".format(len(packages)))
	pkg_hashes = set()
	for package in packages:
		pkg_url, pkg_version, pkg_path = package_resolve(package)
		p_hash = pkg_hash(pkg_url, pkg_path)
		if p_hash in pkg_hashes:
			continue

		print("Downloading sources for {}...".format(package))
		cache_dir, _b = get_sources(pkg_url, pkg_version)

		if recurse:
			print("Extracting dependencies from {}...".format(package))
			new_packages = extract_pro_depends(path.join(cache_dir, pkg_path[1:]), qmake)
			print("Found {} dependent packages".format(len(new_packages)))
			for pkg in new_packages:
				packages.append(pkg)

		pkg_hashes.add(p_hash)
	print("Done!")


def update(pro_file, evaluate=False, replace=False, qmake="qmake", make="make"):
	if evaluate:
		all_deps = invert_map(eval_pro_depends(pro_file, qmake, make, dump_depends=True))
		pkg_all, pkg_new = check_for_updates(all_deps.keys())
		update_files = set()
		for old_pkg, new_pkg in pkg_new.items():
			for dep in all_deps[old_pkg]:
				update_files.add(dep)
			all_deps[new_pkg] = (all_deps[new_pkg] if new_pkg in all_deps else []) + all_deps[old_pkg]
			all_deps.pop(old_pkg)
		all_deps = invert_map(all_deps)
		for upd_file in update_files:
			replace_or_print_update(upd_file, all_deps[upd_file], pkg_new, replace)
	else:
		print("Extracting dependencies from {}...".format(pro_file))
		packages = extract_pro_depends(pro_file, qmake)
		pkg_all, pkg_new = check_for_updates(packages)
		replace_or_print_update(pro_file, pkg_all, pkg_new, replace)
