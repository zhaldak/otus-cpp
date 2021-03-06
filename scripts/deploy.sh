#!/bin/bash

set -e

BINTRAY_USER='zhaldak'
BINTRAY_REPO='otus-cpp'
#BINTRAY_API_KEY=''


function usage()
{
	echo "Usage: $0 <PROJ_NAME> <PROJ_BUILD_DIR>"
}

function LogE()
{
	echo -e "\e[91mERROR:\e[0m$@"
}


PROJ_NAME="${1}"
PROJ_BUILD_DIR="${2}"

if [ $# -ne 2 ] ; then
	LogE "Unexpected number of arguments: exp=2, act=$#"
	usage
	exit 1
fi

if [ ! -d "${PROJ_BUILD_DIR}" ] ; then
	LogE "PROJ_BUILD_DIR=[${PROJ_BUILD_DIR}] is not directory"
	usage
	exit 2
fi

cd "${PROJ_BUILD_DIR}"
pwd; ls -la
PROJ_VERSION=$(grep --color=never -w 'CMAKE_PROJECT_VERSION:STATIC' CMakeCache.txt | cut -d= -f2)
PROJ_DEB=$(ls --color=never *.deb)
curl -T "${PROJ_DEB}" -u ${BINTRAY_USER}:${BINTRAY_API_KEY} \
	"https://api.bintray.com/content/${BINTRAY_USER}/${BINTRAY_REPO}/${PROJ_NAME}/${PROJ_VERSION}/${PROJ_DEB};deb_distribution=trusty;deb_component=main;deb_architecture=amd64;publish=1"
exit 0

