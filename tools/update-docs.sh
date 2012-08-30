#!/usr/bin/env bash
#
# Update the node docs under docs/
#

if [[ -n "$TRACE" ]]; then
    export PS4='${BASH_SOURCE}:${LINENO}: ${FUNCNAME[0]:+${FUNCNAME[0]}(): }'
    set -o xtrace
fi
set -o errexit
set -o pipefail


#---- globals

TOP=$(unset CDPATH; cd $(dirname $0)/../; pwd)



#---- support functions

function fatal
{
    echo "$(basename $0): fatal error: $*"
    exit 1
}



#---- mainline

tmp_dir=$TOP/tmp
mkdir -p $tmp_dir

node_dir=$tmp_dir/node
if [[ ! -d $node_dir ]]; then
    git clone https://github.com/joyent/node.git $node_dir
else
    (cd $node_dir \
        && git checkout master \
        && git fetch origin \
        && git pull --rebase origin master)
fi


# v0.6
micro_ver6=$(cd $node_dir && git tag -l | grep '^v0\.6' \
    | cut -d. -f3 | sort -n | tail -1)
ver6=v0.6.$micro_ver6
(cd $node_dir && git checkout $ver6)
cp -r $node_dir/doc/api/* doc/api6/
rm doc/api6/index.markdown doc/api6/_toc.markdown doc/api6/all.markdown
git add doc/api6

# v0.8
micro_ver8=$(cd $node_dir && git tag -l | grep '^v0\.8' \
    | cut -d. -f3 | sort -n | tail -1)
ver8=v0.8.$micro_ver8
(cd $node_dir && git checkout $ver8)
cp -r $node_dir/doc/api/* doc/api8/
rm doc/api8/index.markdown doc/api8/_toc.markdown doc/api8/all.markdown
git add doc/api8

# reset
(cd $node_dir && git checkout master)


updates6=$(git status --porcelain doc/api6)
updates8=$(git status --porcelain doc/api8)

if [[ -n "$updates6" || -n "$updates8" ]]; then
    echo $ver6 >doc/versions
    echo $ver8 >>doc/versions
fi

echo ""
echo '* * *'
if [[ -z "$updates6" && -z "$updates8" ]]; then
    echo "no updates"
elif [[ -n "$updates6" && -n "$updates8" ]]; then
    echo "Suggested CHANGES.md addition:"
    echo ""
    echo "    - Update docs to $ver6, $ver8."
    echo ""
    echo "Suggested commit:"
    echo ""
    echo "    git commit CHANGES.md doc -m 'update docs to $ver6, $ver8'"
elif [[ -n "$updates6" && -z "$updates8" ]]; then
    echo "Suggested CHANGES.md addition:"
    echo ""
    echo "    - Update docs to $ver6."
    echo ""
    echo "Suggested commit:"
    echo ""
    echo "    git commit CHANGES.md doc -m 'update docs to $ver6'"
elif [[ -z "$updates6" && -n "$updates8" ]]; then
    echo "Suggested CHANGES.md addition:"
    echo ""
    echo "    - Update docs to $ver8."
    echo ""
    echo "Suggested commit:"
    echo ""
    echo "    git commit CHANGES.md doc -m 'update docs to $ver8'"
fi
