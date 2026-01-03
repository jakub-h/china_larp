#!/usr/bin/env bash

# Fail on error and unset variables.
set -eu -o pipefail

CWD=$(readlink -e "$(dirname "$0")")
cd "$CWD"/.. || exit $?

# shellcheck disable=SC1091
source ./docker/common.sh

docker_run_args=(
	--rm
	-it
	-p 5000:5000
	--mount "type=bind,source=$(pwd -P),target=/mnt/workspace"
	-w /mnt/workspace
	"${IMAGE_TAG}"
	"$@"
)

if [ "$#" -eq 0 ]; then
	docker run "${docker_run_args[@]}" python app.py || exit $?
else
	docker run "${docker_run_args[@]}" || exit $?
fi
