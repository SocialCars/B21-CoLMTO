#!/usr/bin/env sh
echo "\`\`\`"
pylint colmto tests/* -f text -r y --rcfile=docs/pylint.rc
echo "\`\`\`"
