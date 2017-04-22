echo '```'
pylint colmto tests/* run.py -f text --import-graph=colmto-imports.png
echo '```'
