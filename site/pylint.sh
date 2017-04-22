echo '```'
pylint colmto tests/* run.py -f text -r y --import-graph=colmto-imports.png
echo '```'
