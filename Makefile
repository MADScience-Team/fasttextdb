all:
	$(MAKE) -C fasttextdb

clean:
	-rm *.pyc
	-rm -r __pycache__
	$(MAKE) -C fasttextdb clean
