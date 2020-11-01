#!/bin/bash

set -e

BINTRAY_USER='kadze009'
BINTRAY_REPO='otus-cpp'
#BINTRAY_API_KEY=''


function usage()
{
	echo "Usage: $0 <PROJ_NAME> <PROJ_DIR>"
}

function LogE()
{
	echo -e "\e[91mERROR:\e[0m$@"
}


PROJ_NAME="${1}"
PROJ_DIR="${2}"

if [ $# -ne 2 ] ; then
	LogE "Unexpected number of arguments: exp=2, act=$#"
	usage
	exit 1
fi

if [ ! -d "${PROJ_DIR}" ] ; then
	LogE "PROJ_DIR=[${PROJ_DIR}] is not directory"
	usage
	exit 2
fi

pwd; ls -la
cd "${PROJ_DIR}"
pwd; ls -la
PROJ_VERSION=$(grep --color=never -w 'CMAKE_PROJECT_VERSION:STATIC' CMakeCache.txt | cut -d= -f2)
PROJ_DEB=$(ls --color=never *.deb)
curl -T "${PROJ_DEB}" -u ${BINTRAY_USER}:${BINTRAY_API_KEY} \
	"https://api.bintray.com/content/${BINTRAY_USER}/${BINTRAY_REPO}/${PROJ_NAME}/${PROJ_VERSION}/${PROJ_DEB};deb_distribution=trusty;deb_component=main;deb_architecture=amd64;publish=1"
exit 0

