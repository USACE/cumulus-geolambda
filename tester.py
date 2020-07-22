"""Run the lambda_function with mock data and debug if necessary.
Use "import pdb; pdb.set_trace()" to set a breakpoint
Reference: https://www.stackery.io/blog/iterating-debugging-aws-lambda-functions/
This script was created to be run in a docker container created by build-and-debug.sh
One can modify lambda_function.py and run it again without rebuilding.
If you modify code in another module, then you have to rebuild.
TODO: Investigate if it's ppssible to setup testing environment so that you can modify
other modules and run it again without rebuilding.
"""

import sys
sys.path.insert(1, '/var/task/python/lambda')
import lambda_function
import json

# snodas_unmasked
#mock_data = r"mock_events/nohrsc_snodas_unmasked.json"
#prism_ppt_early
mock_data = r"mock_events/prism_ppt_early.json"
# prism_tmax_early
#mock_data = r"mock_events/prism_tmax_early.json"
# prism_tmin_early
#mock_data = r"mock_events/prism_tmin_early.json"

with open(mock_data, 'r') as json_file:
    message = json.load(json_file)


#import pdb; pdb.set_trace()
lambda_function.lambda_handler(message)
