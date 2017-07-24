#!/usr/bin/env sh
echo "\`\`\`"
pylint colmto tests/* -f text -r y --import-graph=colmto-imports.png
echo "\`\`\`"
