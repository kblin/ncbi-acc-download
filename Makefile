unit:
	py.test -v

coverage:
	py.test --cov=ncbi_acc_download --cov-report term-missing --cov-report html
