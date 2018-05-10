import boto3,optparse
import sys,json,signal,os,errno,uuid
from os.path import expanduser
#import adodbapi
#import adodbapi.apibase
import logging
import logging.config
#from foqus_lib.framework.sim.turbineLiteDB import turbineLiteDB
from foqus_lib.framework.sim.turbineLiteDB import keepAliveTimer as KeepAliveTimer
from foqus_lib.framework.session.session import session as Session
#adodbapi.adodbapi.defaultCursorLocation = adodbapi.adUseServer
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
_log = logging.getLogger()
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
    #register the consumer in the database
    consumer_uuid = db.consumer_register()
    print("consumer_uuid: {0}".format(consumer_uuid))
    """

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
    consumer_uuid = db.consumer_register()
    print("consumer_uuid: {0}".format(consumer_uuid))
    #write the time to the turbineLite db about every minute
    #kat = KeepAliveTimer(db, consumer_uuid, freq = 60)
    #kat.start()

    guid = job_desc['Id']
    jid = None
    simId = job_desc['Simulation']

    # Run the job
    db.add_message("consumer={0}, starting job {1}"\
        .format(consumer_uuid, jid), guid)
    db.job_change_status(guid, "setup")

    configContent = db.get_configuration_file(simId)

    logging.getLogger("foqus." + __name__)\
        .info("Job {0} is submitted".format(jid))

    db.jobConsumerID(guid, consumer_uuid)
    db.job_prepare(guid, jid, configContent)

    # Load the session file
    dat.load(sfile, stopConsumers=True)
    dat.loadFlowsheetValues(vfile)
    db.job_change_status(guid, "running")
    gt = dat.flowsheet.runAsThread()
    terminate = False
    while gt.isAlive():
        gt.join(10)
        status = db.consumer_status(consumer_uuid)
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
                .format(consumer_uuid, jid), guid)
    else:
        db.job_change_status(guid, "error")
        db.add_message(
            "consumer={0}, job {1} finished, error"\
                .format(consumer_uuid, jid), guid)
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
        self._sns = boto3.client('sns')
        topic = self._sns.create_topic(Name='FOQUS-Update-Topic')
        self._topic_arn = topic['TopicArn']
        self._consumer_id = str(uuid.uuid4())

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
    def consumer_keepalive(self, uid, rc=0):
        _log.info("%s.consumer_keepalive", self.__class__)
        self._sns_notification(dict(resource='consumer', event='keepalive', rc=rc, consumer=uid))
    def consumer_status(self, uid, status=None, rc=0):
        _log.info("%s.consumer_status", self.__class__)
        self._sns_notification(dict(resource='consumer', event='status', rc=rc, status=status, consumer=uid))
    def consumer_id(self, pid, rc=0):
        _log.info("%s.consumer_id", self.__class__)
    def consumer_register(self, rc=0):
        _log.info("%s.consumer_register", self.__class__)
        self._sns_notification(dict(resource='consumer', event='status',
            rc=rc, status="up", consumer=self._consumer_id))
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
            rc=rc, status=status, jobid=jobGuid, consumer=self._consumer_id))
    def job_save_output(self, jobGuid, workingDir, rc=0):
        _log.info("%s.job_save_output", self.__class__)
        with open(os.path.join(workingDir, "output.json")) as outfile:
            output = json.load(outfile)
        self._sns_notification(dict(resource='job',
            event='result', value=output, rc=rc))


def main():
    """
    """
    global DEBUG
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
        print item
    conn.close()
    """
    _log.debug("starting")
    VisibilityTimeout = 300
    if DEBUG:
        VisibilityTimeout = 0

    pull_job(VisibilityTimeout=VisibilityTimeout)


if __name__ == '__main__':
    main()
