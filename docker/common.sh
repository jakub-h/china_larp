#!/usr/bin/env bash

# Fail on error and unset variables.
set -eu -o pipefail

# Default image tag for this repo (also used by docker/run.sh)
IMAGE_TAG="${IMAGE_TAG:-china_larp}"
