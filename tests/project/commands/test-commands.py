#!/usr/bin/env python3

import sys
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET


qdep_path = None
qmake_path = "qmake"


def exec_process(name, proc, args, keep_stdout=False, keep_stderr=False):
	print("Executing:", name, " ".join(args))
	sys.stdout.flush()
	run_res = subprocess.run([proc] + args, cwd=os.getcwd(), check=True, stdout=subprocess.PIPE if keep_stdout else None, stderr=subprocess.PIPE if keep_stderr else None, encoding="UTF-8")
	if keep_stdout:
		stdout_data = str(run_res.stdout)
	else:
		stdout_data = None
	if keep_stderr:
		stderr_data = str(run_res.stderr)
	else:
		stderr_data = None
	return stdout_data, stderr_data


def exec_qdep(args=[], keep_stdout=False, keep_stderr=False, trace=True):
	return exec_process("qdep", qdep_path, (["--trace"] if trace else []) + args, keep_stdout=keep_stdout, keep_stderr=keep_stderr)


def exec_qmake(args=[], keep_stdout=False, keep_stderr=False):
	return exec_process("qmake", qmake_path, args, keep_stdout=keep_stdout, keep_stderr=keep_stderr)


def test_prfgen():
	exec_qdep(["prfgen", "-d", os.getcwd()])
	assert os.path.isfile("mkspecs/features/qdep.prf")
	with open("mkspecs/features/qdep.prf", "r") as prf_in:
		print("qdep.prf: ", prf_in.readline().strip())


def test_init():
	with open("test.pro", "w") as pro_file:
		pro_file.write("TEMPLATE = aux\n")
	exec_qdep(["init", "test.pro"])
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
	exec_qdep(["lupdate", "--qmake", qmake_path, "--pri-file", os.path.abspath("test.pri"), "--", "-no-ui-lines"])

	assert os.path.isfile("test.pri")
	root = ET.parse("test_de.ts").getroot()
	assert root[0][1][1].text == "Hello Tree"


def test_versions():
	def v_fetch(args, strip=True):
		vs_sout, _e = exec_qdep(["versions"] + args + ["https://github.com/Skycoder42/qpmx-sample-package.git"], keep_stdout=True)
		if strip:
			vs_list = map(lambda s: s.strip(), vs_sout.strip().split("\n"))
			return list(vs_list)
		else:
			return vs_sout.strip().split(" ")

	v_res = v_fetch([])
	assert v_res[0:5] == ["Tags:", "1.0.0", "1.0.1", "1.0.10", "1.0.11"]
	assert v_res[-1] == "1.2.0"

	v_res = v_fetch(["-b", "--no-tags"])
	assert v_res == ["Branches:", "master"]

	v_res = v_fetch(["-b"])
	assert v_res[0:8] == ["Branches:", "master", "", "Tags:", "1.0.0", "1.0.1", "1.0.10", "1.0.11"]
	assert v_res[-1] == "1.2.0"

	v_res = v_fetch(["-b", "-s"], strip=False)
	assert v_res[0:5] == ["master", "1.0.0", "1.0.1", "1.0.10", "1.0.11"]
	assert v_res[-1] == "1.2.0"

	v_res = v_fetch(["-s", "--limit", "5"], strip=False)
	assert v_res == ["1.0.7", "1.0.8", "1.0.9", "1.1.0", "1.2.0"]


def test_clear():  # TODO implement later
	pass


def test_run(name, test_fn):
	print("\n*** Running test:", name)
	os.makedirs(name)
	os.chdir(name)

	test_fn()

	os.chdir("..")
	print("*** SUCCESS")


if __name__ == '__main__':
	if len(sys.argv) > 1:
		qmake_path = sys.argv[1]

	if len(sys.argv) > 2:
		qdep_path = os.path.join(os.path.dirname(__file__), "..", "..", "testentry.py")
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
	test_run("clear", test_clear)
