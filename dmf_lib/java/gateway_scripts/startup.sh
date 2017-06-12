#!/bin/bash
$JAVA_HOME/bin/java -Dfile.encoding=US-ASCII -jar "$DMF_HOME/dmf_lib/java/build/dmf_client.jar" &
pid=$!
#echo $pid