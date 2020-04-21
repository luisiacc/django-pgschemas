# Makefile for django-pgschemas

.PHONY: test
test:
	poetry run dpgs_sandbox/manage.py test tests

.PHONY: coverage
coverage:
	poetry run coverage run dpgs_sandbox/manage.py test tests

.PHONY: coverage-html
coverage-html:
	poetry run coverage run dpgs_sandbox/manage.py test tests && coverage html
