#!/usr/bin/env sh
printf "# Radon\n\n"
printf "## Cyclomatic Complexity\n\n"
printf "| File | Type | R:C | Module | CC  |\n|:---- |:---- |:---:|:------ |:--- |\n"
radon cc --show-closures -x F --total-average -s colmto | sed \
-e "s/^    /||/g" \
-e "/^||/ s/ - /|/g" \
-e "/^||/ s/ /|/g" \
-e "/^||/ s/|(/ (/g" \
-e "/^||/ s/$/|/" \
-e "/^[a-zA-Z]/ s/^/|\`/" \
-e "/^|\`[a-zA-Z]/ s/$/\`|||||/" \
-e "/^||/ s/|[[:alnum:]\.\_]\{2\}[[:alnum:]\.\_]*|/|\`&\`|/g" \
-e "/^||/ s/|\`|/|\`/" \
-e "/^||/ s/|\`|/\`|/" \
-e "/|\`Average[[:print:]]*\`|/ s/|//g"
printf "\n\n## Maintainability Index\n\n"
printf "\`\`\`\n"
radon mi -x F -s colmto
printf "\`\`\`\n\n"
