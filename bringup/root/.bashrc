# ~/.bashrc: executed by bash(1) for non-login shells.
# see /usr/share/doc/bash/examples/startup-files (in the package bash-doc)
# for examples

# If not running interactively, don't do anything
case $- in
    *i*) ;;
      *) return;;
esac

# don't put duplicate lines or lines starting with space in the history.
# See bash(1) for more options
HISTCONTROL=ignoreboth

# append to the history file, don't overwrite it
shopt -s histappend

# for setting history length see HISTSIZE and HISTFILESIZE in bash(1)
HISTSIZE=1000
HISTFILESIZE=2000000

# http://blog.sanctum.geek.nz/better-bash-history/
#HISTTIMEFORMAT='%F %T '
HISTTIMEFORMAT="%d/%m/%y %T " # http://askubuntu.com/questions/391082/how-to-see-time-stamps-in-bash-history
shopt -s cmdhist
HISTIGNORE='ls:bg:fg:history' # phillip: this also disables up arrow for these commands
#PROMPT_COMMAND='history -a'
# http://askubuntu.com/questions/67283/is-it-possible-to-make-writing-to-bash-history-immediate
#export PROMPT_COMMAND="history -a; history -c; history -r; $PROMPT_COMMAND"

# check the window size after each command and, if necessary,
# update the values of LINES and COLUMNS.
shopt -s checkwinsize

# If set, the pattern "**" used in a pathname expansion context will
# match all files and zero or more directories and subdirectories.
#shopt -s globstar

# make less more friendly for non-text input files, see lesspipe(1)
#[ -x /usr/bin/lesspipe ] && eval "$(SHELL=/bin/sh lesspipe)"

# set a fancy prompt (non-color, unless we know we "want" color)
case "$TERM" in
    xterm-color) color_prompt=yes;;
esac

# uncomment for a colored prompt, if the terminal has the capability; turned
# off by default to not distract the user: the focus in a terminal window
# should be on the output of commands, not on the prompt
force_color_prompt=yes

if [ -n "$force_color_prompt" ]; then
    if [ -x /usr/bin/tput ] && tput setaf 1 >&/dev/null; then
	# We have color support; assume it's compliant with Ecma-48
	# (ISO/IEC-6429). (Lack of such support is extremely rare, and such
	# a case would tend to support setf rather than setaf.)
	color_prompt=yes
    else
	color_prompt=
    fi
fi

if [ "$color_prompt" = yes ]; then
    PS1='\[\033[01;92m\]\h\[\033[00m\]:\[\033[01;94m\]\W\[\033[00m\]\[\033[01;92m\]$\[\033[00m\] '
else
    PS1='\h:\W\$ '
fi
unset color_prompt force_color_prompt

# If this is an xterm set the title to user@host:dir
case "$TERM" in
xterm*|rxvt*)
    PS1="\[\e]0;\h: \W\a\]$PS1"
    ;;
*)
    ;;
esac

# enable color support of ls and also add handy aliases
if [ -x /usr/bin/dircolors ]; then
    test -r ~/.dircolors && eval "$(dircolors -b ~/.dircolors)" || eval "$(dircolors -b)"
    alias ls='ls --color=auto'
    alias dir='dir --color=auto'
    alias vdir='vdir --color=auto'
    # color not available on BusyBox
    #alias grep='grep --color=auto'
    #alias fgrep='fgrep --color=auto'
    #alias egrep='egrep --color=auto'
fi

# some more ls aliases
#alias ll='ls -l'
#alias la='ls -A'
#alias l='ls -CF'

# Alias definitions.
# You may want to put all your additions into a separate file like
# ~/.bash_aliases, instead of adding them here directly.
# See /usr/share/doc/bash-doc/examples in the bash-doc package.

if [ -f ~/.bash_aliases ]; then
    . ~/.bash_aliases
fi

# enable programmable completion features (you don't need to enable
# this, if it's already enabled in /etc/bash.bashrc and /etc/profile
# sources /etc/bash.bashrc).
if ! shopt -oq posix; then
  if [ -f /usr/share/bash-completion/bash_completion ]; then
    . /usr/share/bash-completion/bash_completion
  elif [ -f /etc/bash_completion ]; then
    . /etc/bash_completion
  fi
fi


# phillip

function trim() {
	awk '{gsub(/^ +| +$/,"")}1'
}

function uspgrep() {
	grep -ahP $*| trim | sort -u
}

function lse() {
	ls -gG --group-directories-first --time-style=long-iso -h -L $*
}

function lst() {
	tree -d -L 1 -sh $*
}

function lstx() { # eXtended
	tree --noreport --dirsfirst -D --timefmt='%m%d%y %H%I' -h -L 1 $*
}

function note() {
	notes=$HOME/notes
	if [ ! "$*" ]; then
		date=$(date +"%F %R%:::z: ")
		echo -n "$date" >> $notes
		#perl -i -pe 'chomp if eof' $notes
		wc=$(wc -l ~/notes | cut -d ' ' -f 1)
		nano +$(($wc + 1)),$((${#date} + 1)) $notes
	else
		out=$(date +"%F %R%:::z: ")$(echo "$*")
		echo "$out" >> $notes
		echo $out
	fi
}
