#!/bin/bash

# Convert all "received" snapshots to "approved" snapshots for approvaltests output:
# this makes it easy to bulk-accept expected changes, but use with caution and be sure
# to inspect your new snapshots for correctness.

find . -type f -name "*.received.*" -exec sh -c 'for f; do mv "$f" "$(echo "$f" | sed "s/received/approved/")"; done' _ {} +
