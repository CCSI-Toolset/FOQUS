@echo off
mode con: cols=100
set PATH=%PATH%;%~dp0
cd %HOMEPATH%
echo.
echo TURBINE COMMAND LIST
echo.
echo turbine_job_script
echo turbine_application_list
echo turbine_simulation_list
echo turbine_simulation_update
echo turbine_simulation_create
echo turbine_simulation_get
echo turbine_session_list
echo turbine_session_create
echo turbine_session_append
echo turbine_session_kill
echo turbine_session_start
echo turbine_session_stop
echo turbine_session_status
echo turbine_session_stats
echo turbine_session_get_results
echo turbine_session_delete
echo turbine_session_graphs
echo turbine_consumer_log
echo turbine_consumer_list
echo. 
echo To get help type the command name with the -h option
echo for example:
echo turbine_job_script -h
echo.
echo.
cmd

