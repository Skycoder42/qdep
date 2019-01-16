from qdep.internal.common import *


def dephash(*packages, project=False, pkgpath=False):
	for package in packages:
		pkg_url, pkg_branch, pkg_path = package_resolve(package, project=project)
		if pkgpath:
			print(pkg_hash(pkg_url, pkg_path) + ";" + pkg_path)
		else:
			print(pkg_hash(pkg_url, pkg_path))


def pkgresolve(package, latest_version=None, project=False, pull=True, clone=True):
	ov_map = get_override_map()

	pkg_url, pkg_branch, pkg_path = package_resolve(package, pkg_version=latest_version, project=project)
	needs_cache = pkg_branch is None
	if pkg_url in ov_map:
		pkg_base = ov_map[pkg_url]
	else:
		pkg_base, pkg_branch = get_sources(pkg_url, pkg_branch, pull=pull, clone=clone)
	print(pkg_hash(pkg_url, pkg_path))
	print(pkg_branch)
	print(pkg_base)
	print(pkg_path)
	print(needs_cache)


def hookgen(prefix, header, resources=None, hooks=None):
	if resources is None:
		resources = []
	if hooks is None:
		hooks = []

	inc_guard = path.basename(header).replace(".", "_").upper()
	with open(header, "w") as out_file:
		out_file.write("#ifndef {}\n".format(inc_guard))
		out_file.write("#define {}\n\n".format(inc_guard))

		for hook in hooks:
			out_file.write("void {}();\n".format(hook))

		out_file.write("\ninline void qdep_{}_init() {{\n".format(prefix))
		out_file.write("\t// resources\n")
		for resource in resources:  # ignore the first argument, as it is always the current pro file (to ensure this rule is always run
			out_file.write("\tQ_INIT_RESOURCE({});\n".format(path.splitext(path.basename(resource))[0]))
		out_file.write("\t// hooks\n")
		for hook in hooks:
			out_file.write("\t{}();\n".format(hook))
		out_file.write("}\n\n")

		out_file.write("#endif //{}\n".format(inc_guard))


def hookimp(outfile, headers=None, hooks=None):
	if headers is None:
		headers = []
	if hooks is None:
		hooks = []

	with open(outfile, "w") as out_file:
		targets = []
		target_regex = re.compile(r".*qdep_(.*)_hooks\.h$")

		out_file.write("#include <QtCore/QCoreApplication>\n")
		for header in headers:
			abs_path = path.abspath(header)
			out_file.write("#include \"{}\"\n".format(abs_path))
			targets.append(re.match(target_regex, header).group(1))

		out_file.write("\n")
		for hook in hooks:
			out_file.write("void {}();\n".format(hook))

		out_file.write("\nnamespace {\n\n")
		out_file.write("void __qdep_startup_hooks() {\n")
		for target in targets:
			out_file.write("\tqdep_{}_init();\n".format(target))
		for hook in hooks:
			out_file.write("\t::{}();\n".format(hook))
		out_file.write("}\n\n")
		out_file.write("}\n")
		out_file.write("Q_COREAPP_STARTUP_FUNCTION(__qdep_startup_hooks)\n")


def lconvert(tsfile, outfile, *combine_files, lconvert_args=None):
	if lconvert_args is None:
		lconvert_args = ["lconvert"]

	# sort combine args into a map of the languages
	sub_map = dict()
	for sub_arg in combine_files:
		sub_base = path.splitext(path.basename(sub_arg))[0]
		sub_args = sub_base.split("_")[1:]
		for arg_cnt in range(len(sub_args)):
			suffix = "_".join(sub_args[arg_cnt:])
			if suffix not in sub_map:
				sub_map[suffix] = []
			sub_map[suffix].append(sub_arg)

	# find the qm files to combine with the input
	target_base = path.splitext(path.basename(tsfile))[0]
	ts_args = target_base.split("_")[1:]
	combine_list = []
	for arg_cnt in range(len(ts_args) - 1, -1, -1):
		suffix = "_".join(ts_args[arg_cnt:])
		if suffix in sub_map:
			combine_list = combine_list + sub_map[suffix]
	combine_list.append(tsfile)

	# run lconvert
	sub_run(lconvert_args + ["-if", "ts", "-i"] + combine_list + ["-of", "ts", "-o", outfile], check=True)


def prolink(prodir, pkghash, pkgpath, link=None):
	link_target = path.join(prodir, ".qdep", pkghash, "src")
	pro_target = path.join(link_target, pkgpath[1:])

	# skip mode -> only print the path
	if link is None:
		print(pro_target)
		return

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
		os.symlink(link, link_target, target_is_directory=True)
	except OSError:
		# symlink is not possible, copy instead
		print("Project WARNING: Failed to symlink project dependecy. Performing deep copy instead", file=sys.stderr)
		shutil.copytree(link, link_target, symlinks=True, ignore_dangling_symlinks=True)

	print(pro_target)
