#!/bin/zsh

# Colors
PINK='\033[1;38;2;255;175;215m'
GREEN='\033[1;38;2;95;255;95m'
CYAN='\033[1;38;2;0;215;215m'
BLUE='\033[1;38;2;0;215;215m'
RED='\033[1;31m'
BOLD='\033[1m'
RESET='\033[0m'

CONFIG_DIR="maps"
CATEGORIES=("easy" "medium" "hard" "challenger")
MAIN_SCRIPT="fly-in.py"
typeset -A map

printf "${PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${PINK}        MAP SELECTOR MENU       ${RESET}\n"
printf "${PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n\n"

i=1
for cat in "${CATEGORIES[@]}"; do
    files=($CONFIG_DIR/$cat/*.txt(N))
    [[ ${#files[@]} -eq 0 ]] && continue
    
    printf "${CYAN}${BOLD}%s${RESET}\n" "${(U)cat}"
    for f in "${files[@]}"; do
        name=$(basename "$f" .txt | sed -E 's/^[0-9]+_//;s/_/ /g')
        printf "    ${BLUE}%2d)${RESET} %s\n" $i "$name"
        map[$i]="$f"
        ((i++))
    done
    printf "\n"
done

printf "${PINK}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${RESET}\n"
printf "${GREEN} Select map (1-%d) or 0 to exit: ${RESET}" $((i-1))

read sel < /dev/tty

if [[ "$sel" == "0" ]]; then
    exit 0
elif [[ -n "${map[$sel]}" ]]; then
    clear
    printf "${GREEN}${BOLD}Launching: ${map[$sel]}${RESET}\n"
    python3 "$MAIN_SCRIPT" "${map[$sel]}" #| cat -n #--visual 
else
    printf "\n${RED}[ERROR]${RESET} Invalid choice: %s\n" "$sel"
    exit 1
fi
