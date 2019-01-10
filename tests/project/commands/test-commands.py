#!/usr/bin/env python3

import sys
import os
import shutil
import subprocess


qdep_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "qdep.py")
qmake_path = "qmake"


def exec_qdep(args=[]):
	subprocess.run([qdep_path] + args, cwd=os.getcwd(), check=True)


def exec_qmake(args=[]):
	subprocess.run([qmake_path] + args, cwd=os.getcwd(), check=True)


def test_prfgen():
	exec_qdep(["prfgen", "-d", os.getcwd()])
	assert os.path.isfile("mkspecs/features/qdep.prf")


def test_init():
	with open("test.pro", "w") as pro_file:
		pro_file.write("TEMPLATE = aux\n")
	exec_qdep(["init", "test.pro"])
	with open("test.pro", "a") as pro_file:
		pro_file.write("qdep_build:message(\"qdep loaded successfully!\")\n")
		pro_file.write("else:error(\"qdep loaded but not activated!\")\n")
	exec_qmake()


def test_run(name, test_fn):
	print("*** Running test:", name)
	os.makedirs(name)
	os.chdir(name)

	sys.stdout.flush()
	test_fn()

	os.chdir("..")
	print("*** SUCCESS")


if __name__ == '__main__':
	if len(sys.argv) > 0:
		qmake_path = sys.argv[1]

	cwd = os.path.join(os.getcwd(), "tests")
	if os.path.exists(cwd):
		shutil.rmtree(cwd)
	os.makedirs(cwd)
	os.chdir(cwd)

	test_run("prfgen", test_prfgen)
	test_run("init", test_init)
