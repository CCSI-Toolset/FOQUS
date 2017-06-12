#!/bin/bash

echo `ps ux | grep 'DMF_Browser.py \| foqus.py' | grep -v 'grep' | wc -l`