#!/bin/bash

# Build
./build.sh

# Tests: Product Processing

# snodas_unmasked
# ./test.sh ./mock_events/nohrsc_snodas_unmasked.json

# prism_ppt_early
# ./test.sh ./mock_events/prism_ppt_early.json

# RTMA Rapid Update
# ./test.sh ./mock_events/ncep_rtma_ru_anl.json

# NCEP MRMS GaugeCorr QPE 01H
# ./test.sh ./mock_events/ncep_mrms_gaugecorr_qpe_01h.json

# NCEP MRMSv12 01H QPE Pass 1
# ./test.sh ./mock_events/ncep_mrms_v12_MultiSensor_QPE_01H_Pass1.json

# NCEP MRMSv12 01H QPE Pass 2
./test.sh ./mock_events/ncep_mrms_v12_MultiSensor_QPE_01H_Pass2.json

# WPC QPF 2.5KM 
# ./test.sh ./mock_events/wpc_qpf_2p5km.json
