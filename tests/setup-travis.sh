#!/bin/bash
set -e

currDir=$(dirname $0)

if [[ $TRAVIS_OS_NAME == "linux" ]]; then	
	# append post build script
	mv qtmodules-travis/ci/linux/build-docker.sh qtmodules-travis/ci/linux/build-docker.sh.bkp
	echo "$currDir/setup-docker.sh" > qtmodules-travis/ci/linux/build-docker.sh
	cat qtmodules-travis/ci/linux/build-docker.sh.bkp >> qtmodules-travis/ci/linux/build-docker.sh
	rm qtmodules-travis/ci/linux/build-docker.sh.bkp
	chmod a+x qtmodules-travis/ci/linux/build-docker.sh
else
	$currDir/setup-docker.sh
fi
