#!/usr/bin/env bash
#
# Update the node docs under doc/
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


# v0.8
micro_ver8=$(cd $node_dir && git tag -l | grep '^v0\.8' \
    | cut -d. -f3 | sort -n | tail -1)
ver8=v0.8.$micro_ver8
(cd $node_dir && git checkout $ver8)
cp -r $node_dir/doc/api/* doc/api8/
mkdir -p doc/api8/
rm doc/api8/index.markdown doc/api8/_toc.markdown doc/api8/all.markdown
git add doc/api8

# v0.10
micro_ver10=$(cd $node_dir && git tag -l | grep '^v0\.10' \
    | cut -d. -f3 | sort -n | tail -1)
ver10=v0.10.$micro_ver10
(cd $node_dir && git checkout $ver10)
mkdir -p doc/api10/
cp -r $node_dir/doc/api/* doc/api10/
rm doc/api10/index.markdown doc/api10/_toc.markdown doc/api10/all.markdown
git add doc/api10

# reset
(cd $node_dir && git checkout master)


updates8=$(git status --porcelain doc/api8)
updates10=$(git status --porcelain doc/api10)

if [[ -n "$updates8" || -n "$updates10" ]]; then
    echo $ver8 >doc/versions
    echo $ver10 >>doc/versions
fi

echo ""
echo '* * *'
if [[ -z "$updates8" && -z "$updates10" ]]; then
    echo "no updates"
elif [[ -n "$updates8" && -n "$updates10" ]]; then
    echo "Suggested CHANGES.md addition:"
    echo ""
    echo "    - Update docs to $ver8, $ver10."
    echo ""
    echo "Suggested commit:"
    echo ""
    echo "    git commit CHANGES.md doc -m 'update docs to $ver8, $ver10'"
elif [[ -n "$updates8" && -z "$updates10" ]]; then
    echo "Suggested CHANGES.md addition:"
    echo ""
    echo "    - Update docs to $ver8."
    echo ""
    echo "Suggested commit:"
    echo ""
    echo "    git commit CHANGES.md doc -m 'update docs to $ver8'"
elif [[ -z "$updates8" && -n "$updates10" ]]; then
    echo "Suggested CHANGES.md addition:"
    echo ""
    echo "    - Update docs to $ver10."
    echo ""
    echo "Suggested commit:"
    echo ""
    echo "    git commit CHANGES.md doc -m 'update docs to $ver10'"
fi
