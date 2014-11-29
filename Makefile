test:
	siege -d1 -r10 -c25  "http://localhost:8888/thread"
run:
	python app.py
