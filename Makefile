BOOTSTRAP_URL=http://downloads.buildout.org/2/bootstrap.py

.PHONY: default clean very-clean

# Runs buildout
default: bin/buildout
	rm -f bin/development
	python bin/buildout

develop: bootstrap.py bin/buildout
	rm -f bin/production
	python bin/buildout install development developpy var-directory beanstalkd

# Runs bootstrap
bin/buildout: bootstrap.py
	mkdir -p var/
	python bootstrap.py

# Gets bootstrap
bootstrap.py:
	wget $(BOOTSTRAP_URL)

# Destroys existing test database and creates a new one
db:
	rm -f var/db/*.db
	python bin/django syncdb --noinput
	python bin/django migrate
	python bin/django loaddata webserver/fixtures/*_dev_data.yaml

test: bin/buildout
	python bin/buildout install simple-django
	python bin/nosey

clean:
	find ./ -name *.pyc -delete
	find ./ -name *.~ -delete
