#!/bin/bash

# Build
./build.sh

# Tests
# snodas_unmasked
# ./test.sh ./test_json/nohrsc_snodas_unmasked.json
# prism_ppt_early
# ./test.sh ./mock_events/prism_ppt_early.json

# RTMA Rapid Update
./test.sh ./mock_events/ncep_rtma_ru_anl.json
