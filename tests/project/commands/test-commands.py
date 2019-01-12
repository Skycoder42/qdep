#!/usr/bin/env python3

import sys
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET


qdep_path = None
qmake_path = "qmake"


def exec_qdep(args=[]):
	print("Executing: qdep", " ".join(args))
	sys.stdout.flush()
	subprocess.run([qdep_path] + args, cwd=os.getcwd(), check=True)


def exec_qmake(args=[]):
	print("Executing: qmake", " ".join(args))
	sys.stdout.flush()
	subprocess.run([qmake_path] + args, cwd=os.getcwd(), check=True)


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



def test_run(name, test_fn):
	print("*** Running test:", name)
	os.makedirs(name)
	os.chdir(name)

	test_fn()

	os.chdir("..")
	print("*** SUCCESS")


if __name__ == '__main__':
	if len(sys.argv) > 0:
		qmake_path = sys.argv[1]

	if len(sys.argv) > 1:
		qdep_path = os.path.join(os.path.dirname(__file__), "..", "..", "testentry.py")
	else:
		qdep_path = shutil.which("qdep")
		assert qdep_path is not None

	cwd = os.path.join(os.getcwd(), "tests")
	if os.path.exists(cwd):
		shutil.rmtree(cwd)
	os.makedirs(cwd)
	os.chdir(cwd)

	test_run("prfgen", test_prfgen)
	test_run("init", test_init)
	test_run("lupdate", test_lupdate)
