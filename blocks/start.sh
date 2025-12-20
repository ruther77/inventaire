#!/bin/sh
echo "Starting Next.js..." > /tmp/next.log
exec node node_modules/next/dist/bin/next dev -H 0.0.0.0 2>&1 | tee -a /tmp/next.log &
PID=$!
sleep 30
cat /tmp/next.log
wait $PID
