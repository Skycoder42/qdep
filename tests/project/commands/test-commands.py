#!/usr/bin/env python3

import sys
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET


is_local_run = False
tests_allowed = None
qdep_path = None
qmake_path = None
make_path = None


def exec_process(name, proc, args, keep_stdout=False, keep_stderr=False):
	print("Executing:", name, " ".join(args))

	if "QDEP_DEFAULT_PKG_FN" in os.environ:
		proc_env = os.environ.copy()
		proc_env.pop("QDEP_DEFAULT_PKG_FN")
	else:
		proc_env = os.environ

	sys.stdout.flush()
	run_res = subprocess.run([proc] + list(args), cwd=os.getcwd(), check=True, stdout=subprocess.PIPE if keep_stdout else None, stderr=subprocess.PIPE if keep_stderr else None, encoding="UTF-8", env=proc_env)

	if keep_stdout:
		stdout_data = str(run_res.stdout)
	else:
		stdout_data = None
	if keep_stderr:
		stderr_data = str(run_res.stderr)
	else:
		stderr_data = None
	return stdout_data, stderr_data


def exec_qdep(*args, keep_stdout=False, keep_stderr=False, trace=True):
	return exec_process("qdep", qdep_path, (["--trace"] if trace else []) + list(args), keep_stdout=keep_stdout, keep_stderr=keep_stderr)


def exec_qmake(*args, keep_stdout=False, keep_stderr=False):
	return exec_process("qmake", qmake_path, args, keep_stdout=keep_stdout, keep_stderr=keep_stderr)


def test_prfgen():
	exec_qdep("prfgen", "-d", os.getcwd())
	assert os.path.isfile("mkspecs/features/qdep.prf")
	with open("mkspecs/features/qdep.prf", "r") as prf_in:
		print("qdep.prf: ", prf_in.readline().strip())


def test_init():
	with open("test.pro", "w") as pro_file:
		pro_file.write("TEMPLATE = aux\n")
	exec_qdep("init", "test.pro")
	with open("test.pro", "a") as pro_file:
		pro_file.write("!qdep_build:error(\"qdep loaded but not activated!\")\n")
	exec_qmake()


def test_lupdate():
	with open("test.pri", "w") as pri_file:
		pri_file.write("SOURCES += $$PWD/test.cpp\n")
		pri_file.write("QDEP_TRANSLATIONS += $$PWD/test_de.ts\n")
	with open("test.cpp", "w") as cpp_file:
		cpp_file.write("#include <QCoreApplication>\n\n")
		cpp_file.write("void test() {\n")
		cpp_file.write("\tauto x = QCoreApplication::translate(\"GLOBAL\", \"Hello Tree\");\n")
		cpp_file.write("}\n")
	exec_qdep("lupdate", "--qmake", qmake_path, "--pri-file", os.path.abspath("test.pri"), "--", "-no-ui-lines")

	assert os.path.isfile("test.pri")
	root = ET.parse("test_de.ts").getroot()
	assert root[0][1][1].text == "Hello Tree"


def test_versions():
	def v_fetch(*args, strip=True):
		vs_sout, _e = exec_qdep("versions", *args, "Skycoder42/qpmx-sample-package", keep_stdout=True)
		if strip:
			vs_list = map(lambda s: s.strip(), vs_sout.strip().split("\n"))
			return list(vs_list)
		else:
			return vs_sout.strip().split(" ")

	v_res = v_fetch()
	assert v_res[0:5] == ["Tags:", "1.0.0", "1.0.1", "1.0.10", "1.0.11"]
	assert v_res[-1] == "1.2.0"

	v_res = v_fetch("-b", "--no-tags")
	assert v_res == ["Branches:", "master"]

	v_res = v_fetch("-b")
	assert v_res[0:8] == ["Branches:", "master", "", "Tags:", "1.0.0", "1.0.1", "1.0.10", "1.0.11"]
	assert v_res[-1] == "1.2.0"

	v_res = v_fetch("-b", "-s", strip=False)
	assert v_res[0:5] == ["master", "1.0.0", "1.0.1", "1.0.10", "1.0.11"]
	assert v_res[-1] == "1.2.0"

	v_res = v_fetch("-s", "--limit", "5", strip=False)
	assert v_res == ["1.0.7", "1.0.8", "1.0.9", "1.1.0", "1.2.0"]


def test_query():
	def q_fetch(*args, package="Skycoder42/qpmx-sample-package", keep_stderr=False):
		qry_sout, _e = exec_qdep("query", *args, package, keep_stdout=True, keep_stderr=keep_stderr)
		qry_list = map(lambda s: s.strip(), qry_sout.strip().split("\n"))
		return list(qry_list)

	q_res = q_fetch()
	assert q_res == [
		"Input: Skycoder42/qpmx-sample-package",
		"Expanded Name: https://github.com/Skycoder42/qpmx-sample-package.git@1.2.0/qpmx-sample-package.pri",
		"URL: https://github.com/Skycoder42/qpmx-sample-package.git",
		"Version: 1.2.0",
		"Path: /qpmx-sample-package.pri",
		"Exists: True"
	]

	q_res = q_fetch("--expand")
	assert q_res == ["https://github.com/Skycoder42/qpmx-sample-package.git@1.2.0/qpmx-sample-package.pri"]

	q_res = q_fetch("--no-check")
	assert q_res == [
		"Input: Skycoder42/qpmx-sample-package",
		"Expanded Name: None",
		"URL: https://github.com/Skycoder42/qpmx-sample-package.git",
		"Version: None",
		"Path: /qpmx-sample-package.pri"
	]

	q_res = q_fetch("--no-check", package="Skycoder42/qpmx-sample-package@1.2.0")
	assert q_res == [
		"Input: Skycoder42/qpmx-sample-package@1.2.0",
		"Expanded Name: https://github.com/Skycoder42/qpmx-sample-package.git@1.2.0/qpmx-sample-package.pri",
		"URL: https://github.com/Skycoder42/qpmx-sample-package.git",
		"Version: 1.2.0",
		"Path: /qpmx-sample-package.pri"
	]

	q_res = q_fetch("--versions")
	assert q_res[0:15] == [
		"Input: Skycoder42/qpmx-sample-package",
		"Expanded Name: https://github.com/Skycoder42/qpmx-sample-package.git@1.2.0/qpmx-sample-package.pri",
		"URL: https://github.com/Skycoder42/qpmx-sample-package.git",
		"Version: 1.2.0",
		"Path: /qpmx-sample-package.pri",
		"Exists: True",
		"",
		"Branches:", "master", "", "Tags:", "1.0.0", "1.0.1", "1.0.10", "1.0.11"
	]

	q_res = q_fetch(package="Skycoder42/qpmx-sample-package@9.9.9")
	assert q_res == [
		"Input: Skycoder42/qpmx-sample-package@9.9.9",
		"Expanded Name: https://github.com/Skycoder42/qpmx-sample-package.git@9.9.9/qpmx-sample-package.pri",
		"URL: https://github.com/Skycoder42/qpmx-sample-package.git",
		"Version: 9.9.9",
		"Path: /qpmx-sample-package.pri",
		"Exists: False"
	]

	q_res = q_fetch(package="file:///invalid/path/.git", keep_stderr=True)
	assert q_res == [
		"Input: file:///invalid/path/.git",
		"Expanded Name: None",
		"URL: file:///invalid/path/.git",
		"Version: None",
		"Path: /path.pri",
		"Exists: False"
	]


def test_get():
	def g_fetch(*args):
		sout, serr = exec_qdep("get", "--qmake", qmake_path, "--make", make_path, "--dir", os.getcwd(), *args, keep_stdout=True, keep_stderr=True)

		sout = sout.strip()
		if len(sout) == 0:
			sout = []
		else:
			sout = list(map(lambda s: s.strip(), sout.strip().split("\n")))

		serr = serr.strip()
		if len(serr) == 0:
			serr = []
		else:
			serr = list(map(lambda s: s.strip(), serr.strip().split("\n")))

		return sout, serr

	sout, serr = g_fetch("Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri")
	assert len(sout) == 5
	assert len(serr) == 1

	sout, serr = g_fetch("--no-recurse", "Skycoder42/qdep@master/tests/packages/basic/package2/package2.pri")
	assert len(sout) == 3
	assert len(serr) == 0

	sout, serr = g_fetch("Skycoder42/qdep@master/tests/packages/basic/package2/package2.pri")
	assert len(sout) == 14
	assert len(serr) == 0

	with open("extract.pro", "w") as pro_file:
		pro_file.write("QDEP_DEPENDS = Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri\n\n")
	exec_qdep("init", os.path.abspath("extract.pro"))
	sout, serr = g_fetch("--extract", os.path.abspath("extract.pro"))
	assert len(sout) == 6
	assert len(serr) == 0

	with open("eval.pro", "w") as pro_file:
		pro_file.write("TEMPLATE = subdirs\n")
		pro_file.write("SUBDIRS += sub_eval\n")
	os.mkdir("sub_eval")
	with open("sub_eval/sub_eval.pro", "w") as pro_file:
		pro_file.write("TEMPLATE = aux\n")
		pro_file.write("QDEP_DEPENDS = Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri\n\n")
	exec_qdep("init", os.path.abspath("sub_eval/sub_eval.pro"))
	sout, serr = g_fetch("--eval", os.path.abspath("eval.pro"))
	print("qmake/make error output:\n\t", "\n\t".join(serr))
	assert len(sout) == 3


def test_update():
	def u_run(*args, strip_eval=False):
		sout, _e = exec_qdep("update", "--qmake", qmake_path, "--make", make_path, *args, keep_stdout=strip_eval)
		if strip_eval:
			return list(map(lambda s: s.strip(), sout.strip().split("\n")))
		else:
			return None

	with open("normal.pro", "w") as pro_file:
		pro_file.write("QDEP_DEPENDS += Skycoder42/qpmx-sample-package@1.0.0/qpmx-sample-package.prc\n")
		pro_file.write("QDEP_DEPENDS += Skycoder42/qpmx-sample-package\n")
		pro_file.write("QDEP_DEPENDS += Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri\n\n")
	exec_qdep("init", os.path.abspath("normal.pro"))
	u_res = u_run(os.path.abspath("normal.pro"), strip_eval=True)
	assert len(u_res) == 7
	assert u_res[1] == "Found a new version for package Skycoder42/qpmx-sample-package: 1.0.0 -> 1.2.0"
	assert u_res[4:] == [
		"QDEP_DEPENDS = Skycoder42/qpmx-sample-package@1.2.0/qpmx-sample-package.prc \\",
		"Skycoder42/qpmx-sample-package \\",
		"Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri"
	]

	u_run("--replace", os.path.abspath("normal.pro"))
	with open("normal.pro", "a") as pro_file:
		pro_file.write("write_file($$PWD/normal.txt, QDEP_DEPENDS)\n")
	exec_qmake("normal.pro")
	with open("normal.txt", "r") as txt_file:
		txt_lines = txt_file.readlines()
	assert txt_lines == [
		"Skycoder42/qpmx-sample-package@1.2.0/qpmx-sample-package.prc\n",
		"Skycoder42/qpmx-sample-package\n",
		"Skycoder42/qdep@master/tests/packages/basic/package1/package1.pri\n"
	]

	u_run("--eval", os.path.abspath("normal.pro"))


def test_clear():  # TODO implement later
	pass


def test_run(name, test_fn, **kwargs):
	if tests_allowed is not None and name not in tests_allowed:
		print("\n*** Skipping test:", name)
		return

	print("\n*** Running test:", name)
	os.makedirs(name)
	os.chdir(name)

	test_fn(**kwargs)

	os.chdir("..")
	print("*** SUCCESS")


if __name__ == '__main__':
	assert len(sys.argv) > 2
	qmake_path = sys.argv[1]
	make_path = sys.argv[2]

	if len(sys.argv) > 3:
		is_local_run = True
		qdep_path = os.path.join(os.path.dirname(__file__), "..", "..", "testentry.py")
		tests_allowed = sys.argv[4:]
		if len(tests_allowed) == 0:
			tests_allowed = None
	else:
		qdep_path = shutil.which("qdep")
		if qdep_path is None:
			print("Failed to find qdep. Current path is:", os.environ["PATH"], file=sys.stderr)
			sys.exit(1)

	print("qdep path:", qdep_path)
	print("qmake path:", qmake_path)

	cwd = os.path.join(os.getcwd(), "tests")
	if os.path.exists(cwd):
		shutil.rmtree(cwd)
	os.makedirs(cwd)
	os.chdir(cwd)

	test_run("prfgen", test_prfgen)
	test_run("init", test_init)
	test_run("lupdate", test_lupdate)
	test_run("versions", test_versions)
	test_run("query", test_query)
	test_run("get", test_get)
	test_run("update", test_update)
	test_run("clear", test_clear)
