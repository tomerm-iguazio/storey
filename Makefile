# Copyright 2020 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
.PHONY: all
all:
	$(error please pick a target)

# We only want to format and lint checked in python files
CHECKED_IN_PYTHON_FILES := $(shell git ls-files | grep '\.py$$')

# Fallback
ifeq ($(CHECKED_IN_PYTHON_FILES),)
CHECKED_IN_PYTHON_FILES := .
endif

FLAKE8_OPTIONS := --max-line-length 120 --extend-ignore E203,W503
BLACK_OPTIONS := --line-length 120
ISORT_OPTIONS := --profile black

.PHONY: fmt
fmt:
	@echo "Running black fmt..."
	@python -m black $(BLACK_OPTIONS) $(CHECKED_IN_PYTHON_FILES)
	@echo "Running isort..."
	@python -m isort $(ISORT_OPTIONS) $(CHECKED_IN_PYTHON_FILES)

.PHONY: lint
lint: flake8 fmt-check

.PHONY: fmt-check
fmt-check:
	@echo "Running black check..."
	@python -m black $(BLACK_OPTIONS) --check --diff $(CHECKED_IN_PYTHON_FILES)
	@echo "Running isort check..."
	@python -m isort --check --diff $(ISORT_OPTIONS) $(CHECKED_IN_PYTHON_FILES)

.PHONY: flake8
flake8:
	@echo "Running flake8 lint..."
	@python -m flake8 $(FLAKE8_OPTIONS) $(CHECKED_IN_PYTHON_FILES)


.PHONY: if-bash
Coverage=False
if-bash:
	@case "$(Coverage)" in \
		-r) \
			echo "Performing clean with -r flag";; \
		-s) \
			echo "Performing clean with -s flag";; \
	esac

.PHONY: test

Coverage=False
test:
	find storey -name '*.pyc' -exec rm {} \;
	find tests -name '*.pyc' -exec rm {} \;



	@if [ "$(Coverage)" = "True" ]; then \
		rm -rf coverage_reports; \
		rm -f unit_tests.coverage; \
		COVERAGE_FILE=unit_tests.coverage coverage run --rcfile=tests.coveragerc -m pytest ./tests/test_utils.py::test_ds_get_path_utils  --ignore=integration -rf -v; \
		COVERAGE_FILE=unit_tests.coverage coverage report --rcfile=tests.coveragerc; \
		echo "in ignore integration"; \
	else \
		python -m pytest --ignore=integration -rf -v ./tests/test_utils.py::test_get_path_utils; \
		echo "no coverage"; \
	fi

#COVERAGE_FILE=unit_tests.coverage coverage run --rcfile=tests.coveragerc --source=. -m pytest --ignore=integration -rf -v; \
COVERAGE_FILE=unit_tests.coverage coverage run --rcfile=tests.coveragerc --source=. -m pytest --ignore=integration -rf -v;
#python -m pytest --ignore=integration -rf -v . \

.PHONY: bench
bench:
	find bench -name '*.pyc' -exec rm {} \;
	python -m pytest --benchmark-json bench-results.json -rf -v bench/*.py

.PHONY: integration
integration:
	find storey -name '*.pyc' -exec rm {} \;
	find tests -name '*.pyc' -exec rm {} \;
	find integration -name '*.pyc' -exec rm {} \;

	@if [ "$(Coverage)" = "True" ]; then \
		rm -rf coverage_reports; \
		rm -f integration.coverage; \
		COVERAGE_FILE=integration.coverage coverage run --rcfile=tests.coveragerc -m pytest -rf -v integration/test_aggregation_integration.py::test_aggregate_and_query_with_different_sliding_windows; \
		echo "coverage integration report:"; \
		COVERAGE_FILE=integration.coverage coverage report --rcfile=tests.coveragerc; \
	else \
		python -m pytest -rf -v integration/test_aggregation_integration.py::test_aggregate_and_query_with_different_sliding_windows || echo "continue"; \
	fi

#python -m pytest -rf -v integration; \
#python -m pytest -rf -v integration/test_aggregation_integration.py::test_aggregate_and_query_with_different_sliding_windows; \

.PHONY: env
env:
	python -m pip install -r requirements.txt

.PHONY: dev-env
dev-env: env
	python -m pip install -r dev-requirements.txt

.PHONY: docs-env
docs-env:
	python -m pip install -r docs/requirements.txt

.PHONY: dist
dist: dev-env
	python -m build --sdist --wheel --outdir dist/ .

.PHONY: set-version
set-version:
	python set-version.py

.PHONY: docs
docs: # Build html docs
	rm -f docs/external/*.md
	cd docs && make html

#  .PHONY: coverage TODO make sure all deleted


# .PHONY: full-coverage-unit-tests TODO make sure all deleted

#  .PHONY: coverage-integration TODO make sure all deleted


.PHONY: coverage-combine
coverage-combine:
	rm -f combined.coverage;
	find storey -name '*.pyc' -exec rm {} \;
	find tests -name '*.pyc' -exec rm {} \;
	find integration -name '*.pyc' -exec rm {} \;
	COVERAGE_FILE=combined.coverage coverage combine --keep integration.coverage unit_tests.coverage;
	echo "coverage full report:";
	COVERAGE_FILE=combined.coverage coverage report --rcfile=tests.coveragerc -i;

.PHONY: full-coverage
full-coverage:
	make test Coverage=True;
	make integration Coverage=True;
	make coverage-combine
