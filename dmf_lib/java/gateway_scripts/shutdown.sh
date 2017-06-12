#!/bin/bash

kill `ps -ef | grep -v grep | grep 'dmf_client' | head -n1 | awk '{print $2}'` &>/dev/null
