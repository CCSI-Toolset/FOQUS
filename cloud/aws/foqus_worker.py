"""foqus_worker.py
* The AWS Cloud FOQUS worker to start FOQUS
This is mostly for testing.
Joshua Boverhof, Lawrence Berkeley National Lab

See LICENSE.md for license and copyright details.
"""
import boto3,optparse
import sys,json,signal,os,errno,uuid,threading,time
from os.path import expanduser
#import adodbapi
#import adodbapi.apibase
import urllib2
import logging
import logging.config
#from foqus_lib.framework.sim.turbineLiteDB import turbineLiteDB
#from foqus_lib.framework.sim.turbineLiteDB import keepAliveTimer as KeepAliveTimer
from foqus_lib.framework.session.session import session as Session
from turbine.commands import turbine_simulation_script
#adodbapi.adodbapi.defaultCursorLocation = adodbapi.adUseServer
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_log = logging.getLogger()
_instanceid = None
HOME = expanduser("~")
workingDirectory = None
DEBUG = False
"""
def turbine_lite_bd():
    DatabasePath = "C:\\Program Files (x86)\\Turbine\\Lite\\Data\\TurbineCompactDatabase.sdf"
    prov = 'Provider=Microsoft.SQLSERVER.CE.OLEDB.4.0;'
    data = 'Data Source={0};'.format(DatabasePath)
    conn_str = " ".join([prov, data])
    conn=adodbapi.connect(conn_str, autocommit=True)
    curs = conn.cursor()
    return conn, curs
"""

def signal_handler(signal, frame):
    """
    A signal handler to cause a siginal to raise a keyboardinterupt exception.
    Used to override a default signal like SIGINT so the FOQUS consumer process
    can shutdown cleanly. The FOQUS consumer catches the keyboardinterupt
    exception as one (slighlty unreliable) way to shut down.  Seems ctrl-c
    causes keyboard interupt exception and SIGINT signal, hense need to change
    SIGINT handler.
    """
    raise KeyboardInterrupt()


def getfilenames(jid):
    global workingDirectory
    workingDirectory = os.path.join(HOME, "foqus_jobs", str(jid))
    _log.info('Working Directory: %s', workingDirectory)
    try: os.makedirs(workingDirectory)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise
    sfile = os.path.join(workingDirectory, "session.foqus")
    # result session file to keep on record
    rfile = os.path.join(workingDirectory, "results_session.foqus")
    # Input values files
    vfile = os.path.join(workingDirectory, "input_values.json")
    # Output values file
    ofile = os.path.join(workingDirectory, "output.json")
    return sfile,rfile,vfile,ofile


def pull_job(VisibilityTimeout):
    """ SQS Job Body Contain Job description, for example:
    [{"Initialize":false,
    "Input":{},
    "Reset":false,
    "Simulation":"BFB_v11_FBS_01_26_2018",
    "Visible":false,
    "Id":"8a3033b4-6de2-409c-8552-904889929704"}]
    """
    sqs = boto3.client('sqs', region_name='us-east-1')
    queue_url = 'https://sqs.us-east-1.amazonaws.com/754323349409/FOQUS-Job-Queue'
    # Receive message from SQS queue
    response = sqs.receive_message(
        QueueUrl=queue_url,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=VisibilityTimeout,
        WaitTimeSeconds=0
    )
    if not response.get("Messages", None):
        _log.info("Job Queue is Empty")
        return

    message = response['Messages'][0]
    receipt_handle = message['ReceiptHandle']
    body = json.loads(message['Body'])
    job_desc = json.loads(body['Message'])
    print('Job Desription: ' + body['Message'])

    sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
    with open(vfile,'w') as fd:
        json.dump(dict(input=job_desc['Input']), fd)

    #configContent = db.get_configuration_file(job_desc['Simulation'])
    #with open(sfile,'w') as fd:
    #    json.dump(dict(input=job_desc['Input']), fd)
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'foqus-simulations'
    l = s3.list_objects(Bucket=bucket_name, Prefix='anonymous/%s' %job_desc['Simulation'])
    # BFB_OUU_MultVar_04.09.2018.foqus
    if not l.has_key('Contents'):
        _log.info("S3 Simulation:  No keys match %s" %'anonymous/%s' %job_desc['Simulation'])
        return

    foqus_keys = filter(lambda i: i['Key'].endswith('.foqus'), l['Contents'])
    if len(foqus_keys) == 0:
        _log.info("S3 Simulation:  No keys match %s" %'anonymous/%s/*.foqus' %job_desc['Simulation'])
        return
    if len(foqus_keys) > 1:
        _log.error("S3 Simulations:  Multiple  %s" %str(foqus_keys))
        return

    _log.info("S3: Download Key %s", foqus_keys[0])
    s3.download_file(bucket_name, foqus_keys[0]['Key'], sfile)

    # WRITE CURRENT JOB TO FILE
    with open(os.path.join(workingDirectory, 'current_foqus.json'), 'w') as fd:
        json.dump(job_desc, fd)

    run_foqus(job_desc)

    """
    print('Received and DEBUGd message: %s' % message)
    signal.signal(signal.SIGINT, signal_handler)
    #Register consumer TurbineLite DB
    db = turbineLiteDB()
    db.dbFile = os.path.join(
        dat.foqusSettings.turbLiteHome,
        "Data/TurbineCompactDatabase.sdf")
    logging.getLogger("foqus." + __name__)\
        .info("TurbineLite Database:\n   {0}".format(db.dbFile))
    #add 'foqus' app to TurbineLite DB if not already there
    db.add_new_application('foqus')
    """
    #register the consumer in the database
    db.consumer_register()
    if not DEBUG:
        # DELETE received message from queue
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )



def run_foqus(job_desc):
    """
    job_desc: {"Initialize":false,
        "Input":{"BFBRGN.Cr":1,"BFBRGN.Dt":9.041,"BFBRGN.Lb":8.886,
            "BFBRGNTop.Cr":1,"BFBRGNTop.Dt":9.195,"BFBRGNTop.Lb":7.1926,
            "BFBadsB.Cr":1,"BFBadsB.Dt":11.897,"BFBadsB.Lb":2.085,
            "BFBadsB.dx":0.0127,"BFBadsM.Cr":1,"BFBadsM.Dt":15,"BFBadsM.Lb":1.972,
            "BFBadsM.dx":0.06695,"BFBadsT.Cr":1,"BFBadsT.Dt":15,"BFBadsT.Lb":2.203,
            "BFBadsT.dx":0.062397,"GHXfg.A_exch":16358,"GHXfg.GasIn.P":1.01325,
            "GHXfg.GasIn.T":54,"Kd":100,"MinStepSize":0.001,"RunMode":"Steady State",
            "Script":"Run_Steady","Snapshot":"","TimeSeries":[0],"TimeUnits":"Hours",
            "dp":0.00015,"fg_flow":100377,"homotopy":0,"printlevel":0},
        "Reset":false,
        "Simulation":"BFB_v11_FBS_01_26_2018",
        "Visible":false,
        "Id":"8a3033b4-6de2-409c-8552-904889929704"}
    """
    exit_code = 0
    sfile,rfile,vfile,ofile = getfilenames(job_desc['Id'])
    # Session file to run
    load_gui = False
    dat = Session(useCurrentWorkingDir=True)
    #Make ctrl-c do nothing but and SIGINT donothing but interupt
    #the loop
    #signal.signal(signal.SIGINT, signal_handler)

    #Register consumer TurbineLite DB
    db = TurbineLiteDB()
    #db.dbFile = os.path.join(dat.foqusSettings.turbLiteHome,
    #                "Data/TurbineCompactDatabase.sdf")
    #logging.getLogger("foqus." + __name__).info(
    #    "TurbineLite Database:\n   {0}".format(db.dbFile))
    #add 'foqus' app to TurbineLite DB if not already there
    #db.add_new_application('foqus')
    #register the consumer in the database
    db.consumer_register()
    #print("consumer_uuid: {0}".format(consumer_uuid))
    #write the time to the turbineLite db about every minute
    kat = _KeepAliveTimer(db, freq=60)
    kat.start()

    guid = job_desc['Id']
    jid = None
    simId = job_desc['Simulation']

    # Run the job
    db.add_message("consumer={0}, starting job {1}"\
        .format(db.consumer_id, jid), guid)

    db.job_change_status(guid, "setup")

    configContent = db.get_configuration_file(simId)

    logging.getLogger("foqus." + __name__)\
        .info("Job {0} is submitted".format(jid))

    #db.jobConsumerID(guid, consumer_uuid)
    db.job_prepare(guid, jid, configContent)

    # Load the session file
    dat.load(sfile, stopConsumers=True)
    dat.loadFlowsheetValues(vfile)
    '''
    "flowsheet"
        "nodes": {
          "BFB": {
            "browser_conf": null,
            "modelName": "BFB_v11_FBS_01_26_2018",
            "pythonCode": "#run steady state init\nself.options[\"Script\"].value = \"Run_Steady\"\nself.runModel()\nif self.calcError != -1:\n    raise(Exception(\"Steady state homotopy failed\"))\n#Run optimization\nself.options[\"Script\"].value = \"Init_Opt\"\nself.runModel()\nif self.calcError != -1:\n    raise(Exception(\"Optimization failed\"))\n# Update the x and f dicts from the node output\n# f gets copied to the node outputs so need this \n# for now x doesn't get copied back\nx, f = self.getValues()",
            "calcError": 0,
            "turbSession": "9c9dff4f-48b9-482a-99be-1bfe879350f5",
            "dmf_sim_ids": null,
            "scriptMode": "total",
            "turbApp": [
              "ACM",
              "aspenfile"
            ],
            "synced": true,
            "modelType": 2,
            "y": 0,
            "x": -200,
            "z": 0,
            "options": {...}
    '''
    # dat.flowsheet.nodes.
    s3 = boto3.client('s3', region_name='us-east-1')
    bucket_name = 'foqus-simulations'
    l = s3.list_objects(Bucket=bucket_name, Prefix='anonymous/%s' %job_desc['Simulation'])
    if not l.has_key('Contents'):
        _log.info("S3 Simulation:  No keys match %s" %'anonymous/%s' %job_desc['Simulation'])
        return

    _log.debug("FLOWSHEET NODES")
    for nkey in dat.flowsheet.nodes:
        if dat.flowsheet.nodes[nkey].turbApp is None:
            continue
        assert len(dat.flowsheet.nodes[nkey].turbApp) == 2, \
            'DAT Flowsheet nodes turbApp is %s' %dat.flowsheet.nodes[nkey].turbApp
        node = dat.flowsheet.nodes[nkey]
        model_name = node.modelName
        sinter_filename = 'anonymous/%s/%s/%s.json' %(job_desc['Simulation'],nkey, model_name)
        s3_key_list = map(lambda i: i['Key'] , l['Contents'])
        assert sinter_filename in s3_key_list, 'missing sinter configuration "%s" not in %s' %(sinter_filename, str(s3_key_list))
        simulation_name = job_desc.get('Simulation')
        #sim_list = node.gr.turbConfig.getSimulationList()
        sim_list = turbine_simulation_script.main_list([node.gr.turbConfig.getFile()])

        print("==="*20)
        print(sim_list)
        print("==="*20)
        sim_d = filter(lambda i: i['Name'] == model_name, sim_list)
        assert len(sim_d) < 2, 'Expecting 0 or 1 entries for simulation %s' %simulation_name
        if len(sim_d) == 0:
            sim_d = None
        else:
            sim_d = sim_d[0]

        if dat.flowsheet.nodes[nkey].turbApp[0] == 'ACM':
            model_filename = 'anonymous/%s/%s/%s.acmf' %(simulation_name,nkey, model_name)
            assert model_filename in s3_key_list, 'missing sinter configuration "%s"' %sinter_filename
        else:
            raise NotImplementedError, 'Flowsheet Node model type: "%s"' %(str(dat.flowsheet.nodes[nkey].turbApp))

        prefix = 'anonymous/%s/%s/' %(job_desc['Simulation'],nkey)
        entry_list = filter(lambda i: i['Key'] != prefix and i['Key'].startswith(prefix), l['Contents'])
        sinter_local_filename = None
        update_required = False
        for entry in entry_list:
            _log.debug("ENTRY: %s", entry)
            key = entry['Key']
            etag = entry.get('ETag', "").strip('"')
            file_name = key.split('/')[-1]
            file_path = os.path.join(workingDirectory, file_name)
            # Upload to TurbineLite
            # if ends with json or acmf
            si_metadata = []
            if key.endswith('.json'):
                _log.debug('CONFIGURATION FILE')
                sinter_local_filename = file_path
                if sim_d:
                    si_metadata = filter(lambda i: i['Name'] == 'configuration', sim_d["StagedInputs"])
            elif key.endswith('.acmf'):
                _log.debug('ACMF FILE')
                if sim_d:
                    si_metadata = filter(lambda i: i['Name'] == 'aspenfile', sim_d["StagedInputs"])
            else:
                raise NotImplementedError, 'Not allowing File "%s" to be staged in' %key

            assert len(si_metadata) < 2, 'Turbine Error:  Too many entries for "%s", "%s"' %(simulation_name, file_name)

            # NOTE: Multipart uploads have different ETags ( end with -2  or something )
            #     THus the has comparison will fail
            #     FOr now ignore it, but fixing this check is performance optimization.
            #
            if len(si_metadata) == 1:
                file_hash = si_metadata[0]['MD5Sum']
                if file_hash.lower() != etag.lower():
                    _log.debug("Compare %s:  %s != %s" %(file_name, etag, file_hash))
                    _log.debug('s3 download(%s): %s' %(workingDirectory, key))
                    s3.download_file(bucket_name, key, file_path)
                    update_required = True
                else:
                    _log.debug("MATCH")
                    s3.download_file(bucket_name, key, file_path)
            else:
                _log.debug("Add to Turbine Simulation(%s) File: %s" %(simulation_name, file_name))
                s3.download_file(bucket_name, key, file_path)
                update_required = True

        assert sinter_local_filename is not None, 'missing sinter configuration file'

        if model_name not in map(lambda i: i['Name'], sim_list):
            _log.debug('Adding Simulation "%s"' %model_name)
            node.gr.turbConfig.uploadSimulation(model_name, sinter_local_filename, update=False)
        elif update_required:
            # NOTE: Requires the configuration file on update, so must download_file it above...
            _log.debug('Updating Simulation "%s"' %model_name)
            node.gr.turbConfig.uploadSimulation(model_name, sinter_local_filename, update=True)
        else:
            _log.debug('No Update Required for Simulation "%s"' %model_name)

    db.job_change_status(guid, "running")
    gt = dat.flowsheet.runAsThread()
    terminate = False
    while gt.isAlive():
        gt.join(10)
        status = db.consumer_status()
        if status == 'terminate':
            terminate = True
            db.job_change_status(guid, "error")
            gt.terminate()
            break
    if terminate:
        return
    if gt.res[0]:
        dat.flowsheet.loadValues(gt.res[0])
    else:
        dat.flowsheet.errorStat = 19
    dat.saveFlowsheetValues(ofile)
    db.job_save_output(guid, workingDirectory)
    dat.save(
        filename = rfile,
        updateCurrentFile = False,
        changeLogMsg = "Saved Turbine Run",
        bkp = False,
        indent = 0)
    if dat.flowsheet.errorStat == 0:
        db.job_change_status(guid, "success")
        db.add_message(
            "consumer={0}, job {1} finished, success"\
                .format(db.consumer_id, jid), guid)
    else:
        db.job_change_status(guid, "error")
        db.add_message(
            "consumer={0}, job {1} finished, error"\
                .format(db.consumer_id, jid), guid)
    logging.getLogger("foqus." + __name__)\
        .info("Job {0} finished"\
        .format(jid))

    #stop all Turbine consumers
    dat.flowsheet.turbConfig.stopAllConsumers()
    dat.flowsheet.turbConfig.closeTurbineLiteDB()
    sys.exit(exit_code)


class TurbineLiteDB:
    """
    """
    def __init__(self, close_after=True):
        self._sns = boto3.client('sns', region_name='us-east-1')
        topic = self._sns.create_topic(Name='FOQUS-Update-Topic')
        self._topic_arn = topic['TopicArn']
        self.consumer_id = str(uuid.uuid4())

    def _sns_notification(self, obj):
        self._sns.publish(Message=json.dumps([obj]), TopicArn=self._topic_arn)

    def __del__(self):
        _log.info("%s.delete", self.__class__)
    def connectionString(self):
        _log.info("%s.connectionString", self.__class__)
    def getConnection(self, rc=0):
        _log.info("%s.getConnection", self.__class__)
    def closeConnection(self):
        _log.info("%s.closeConnection", self.__class__)
    def add_new_application(self, applicationName, rc=0):
        _log.info("%s.add_new_application", self.__class__)
    def add_message(self, msg, jobid, rc=0):
        _log.info("%s.add_message", self.__class__)
    def consumer_keepalive(self, rc=0):
        _log.info("%s.consumer_keepalive", self.__class__)
        self._sns_notification(dict(resource='consumer', event='running', rc=rc, consumer=self.consumer_id))
    def consumer_status(self):
        _log.info("%s.consumer_status", self.__class__)
        #assert status in ['up','down','terminate'], ''
        #self._sns_notification(dict(resource='consumer', event=status, rc=rc, consumer=self.consumer_id))
        return 'up'
    def consumer_id(self, pid, rc=0):
        _log.info("%s.consumer_id", self.__class__)
    def consumer_register(self, rc=0):
        _log.info("%s.consumer_register", self.__class__)
        self._sns_notification(dict(resource='consumer', instanceid=_instanceid, event='running', rc=rc, consumer=self.consumer_id))
    def get_job_id(self, simName=None, sessionID=None, consumerID=None, state='submit', rc=0):
        _log.info("%s.get_job_id", self.__class__)
        return guid, jid, simId, reset

    def jobConsumerID(self, jid, cid=None, rc=0):
        _log.info("%s.jobConsumerID", self.__class__)
    def get_configuration_file(self, simulationId, rc=0):
        _log.info("%s.get_configuration_file", self.__class__)
    def job_prepare(self, jobGuid, jobId, configFile, rc=0):
        _log.info("%s.job_prepare", self.__class__)
    def job_change_status(self, jobGuid, status, rc=0):
        _log.info("%s.job_change_status", self.__class__)
        self._sns_notification(dict(resource='job', event='status',
            rc=rc, status=status, jobid=jobGuid, instanceid=_instanceid, consumer=self.consumer_id))
    def job_save_output(self, jobGuid, workingDir, rc=0):
        _log.info("%s.job_save_output", self.__class__)
        with open(os.path.join(workingDir, "output.json")) as outfile:
            output = json.load(outfile)
        scrub_empty_string_values_for_dynamo(output)
        _log.debug("%s.job_save_output:  %s", self.__class__, json.dumps(output))
        time.sleep(5)
        self._sns_notification(dict(resource='job',
            event='output', jobid=jobGuid, value=output, rc=rc))


def scrub_empty_string_values_for_dynamo(db):
    """ DynamoDB throws expection if there is an empty string in dict
    ValidationException: ExpressionAttributeValues contains invalid value:
    One or more parameter values were invalid: An AttributeValue may not contain an empty string for key :o
    """
    if type(db) is not dict: return
    for k,v in db.items():
        if v in  ("",u""): db[k] = "NULL"
        else: scrub_empty_string_values_for_dynamo(v)

class _KeepAliveTimer(threading.Thread):
    def __init__(self, turbineDB, freq=60):
        threading.Thread.__init__(self)
        self.stop = threading.Event() # flag to stop thread
        self.freq = freq
        self.db = turbineDB
        self.daemon = True

    def terminate(self):
        self.stop.set()

    def run(self):
        i = 0
        while not self.stop.isSet():
            time.sleep(1)
            i += 1
            if i >= self.freq:
                self.db.consumer_keepalive()
                i = 0


def main():
    """
    """
    global DEBUG,_instanceid
    op = optparse.OptionParser(usage="USAGE: %prog [options]",
            description=main.__doc__)
    op.add_option("-d", "--debug",
                  action="store_true", dest="debug",
                  help="DEBUG: Dont delete SQS Queue Message")
    (options, args) = op.parse_args()
    #if len(args) != 1: usage()
    #command = args[0]
    DEBUG = options.debug

    """
    conn,curs = turbine_lite_bd()
    sqlstr = SELECT * FROM Jobs
    curs.execute(sqlstr)
    jobs_all = curs.fetchall()
    for item in jobs_all:
        print(item)
    conn.close()
    """
    _log.debug("starting")
    VisibilityTimeout = 300
    if DEBUG:
        VisibilityTimeout = 0
        _instanceid = 'testing'
    else:
        _instanceid = urllib2.urlopen('http://169.254.169.254/latest/meta-data/instance-id').read()

    pull_job(VisibilityTimeout=VisibilityTimeout)


if __name__ == '__main__':
    main()
