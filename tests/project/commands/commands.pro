TEMPLATE = aux

run_tests.target = run-tests
win32: run_tests.commands = python
run_tests.commands += $$PWD/test-commands.py $$QMAKE_QMAKE $(MAKE)
local_test_run: run_tests.commands += --testrun $$TEST_RUN_ARGS
QMAKE_EXTRA_TARGETS += run_tests
