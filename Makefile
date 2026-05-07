.PHONY: run lint

run:
	python3 app/desktop_manager.py

lint:
	python3 -m py_compile app/desktop_manager.py tools/*.py
