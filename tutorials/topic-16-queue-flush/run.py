#!/usr/bin/env cs_python

# Copyright 2025 Cerebras Systems.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import argparse
import numpy as np

from cerebras.sdk.runtime.sdkruntimepybind import SdkRuntime, MemcpyDataType, MemcpyOrder # pylint: disable=no-name-in-module

# Read arguments
parser = argparse.ArgumentParser()
parser.add_argument('--name', help="the test compile output dir")
parser.add_argument('--cmaddr', help="IP:port for CS system")
args = parser.parse_args()

# Construct a runner using SdkRuntime
runner = SdkRuntime(args.name, cmaddr=args.cmaddr)
sym_launch = runner.get_id('launch')
sym_result1 = runner.get_id('result1')
sym_result2 = runner.get_id('result2')
print(f"sym_launch = {sym_launch}")
print(f"sym_result1 = {sym_result1}")
print(f"sym_result2 = {sym_result2}")

# Load and run the program
runner.load()
runner.run()

runner.launch("launch", nonblock=True)

# Copy result1 and result2 back from PE (1, 0)
# If `queue_flush.exit(oq)` is not called, T29 of mempcy_d2h will trigger `foo`
# and the kernel will stall.
size = 15
filter_size = 2
result1 = np.zeros([size], dtype=np.uint32)
runner.memcpy_d2h(result1, sym_result1, 1, 0, 1, 1, size, streaming=False,
  order=MemcpyOrder.ROW_MAJOR, data_type=MemcpyDataType.MEMCPY_32BIT, nonblock=False)

result2 = np.zeros([size], dtype=np.uint32)
runner.memcpy_d2h(result2, sym_result2, 1, 0, 1, 1, size, streaming=False,
  order=MemcpyOrder.ROW_MAJOR, data_type=MemcpyDataType.MEMCPY_32BIT, nonblock=False)

# Stop the program
runner.stop()

result1_expected = np.ones(size, dtype=np.uint32) * 42
result2_expected = np.ones(size, dtype=np.uint32) * 0
result2_expected[0:filter_size] = 43

print(f"result1 = {result1}")
print(f"result2 = {result2}")

np.testing.assert_allclose(result1, result1_expected, atol=0.0, rtol=0)
np.testing.assert_allclose(result2, result2_expected, atol=0.0, rtol=0)
print("SUCCESS!")
