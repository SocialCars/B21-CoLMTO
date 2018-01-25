# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
#SPHINXBUILD   = sphinx-build
SPHINXBUILD   = python3 -c "import sys,sphinx,os;sys.path.insert(0, os.path.abspath('source'));import conf;os.environ['SUMO_HOME'] = os.path.abspath('../sumo');sys.exit(sphinx.main(sys.argv))"
SPHINXPROJ    = CooperativeLaneManagementandTrafficflowOptimisation
SOURCEDIR     = source
BUILDDIR      = build
SUMO_HOME     = ./sumo
# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)