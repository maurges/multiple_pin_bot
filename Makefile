TESTDIR = test
TESTFILES = handlers_test varlock_test

.PHONY: test
test:
	python3 -m unittest $(addprefix $(TESTDIR).,$(TESTFILES))

redis-test:
	python3 -m unittest test/handler_redis_test.py
