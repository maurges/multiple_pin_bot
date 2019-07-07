TESTDIR = test
TESTFILES = handlers_test

.PHONY: test
test:
	python3 -m unittest $(addprefix $(TESTDIR).,$(TESTFILES))
