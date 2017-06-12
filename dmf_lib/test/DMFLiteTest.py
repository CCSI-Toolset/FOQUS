import os
from PySide import QtCore
from datetime import datetime

MAX_RUN_TIME = 10000  # Max time to let script run (ms)
test_output = "dmf_lite_test.txt"
with open(test_output, 'w') as f:
    f.write('')
timers = {}
timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
state_q = []

def go(MainWin=MainWin):
    '''
        Process gui events so that gui can still function(ish) while
        script is running also add delay between calls to GUI stuff to
        make the execution fun to watch.  Also checks the stop flag and
        returns True keep going or False to stop.
    '''
    MainWin.app.processEvents()
    time.sleep(0.25)
    return not MainWin.helpDock.stop


def getButton(w, label):
    blist = w.buttons()
    print [b.text() for b in blist]
    for b in blist:
        if b.text().replace("&", "") == label:
            return b
    return None


def addTimer(name, cb, MainWin=MainWin, timers=timers):
    '''
        Using timers to push buttons on popups and modal dialogs and
        other things were I need an easy way to make things happen from
        a seperate thread.  Usually where something is blocking the main
        GUI loop.

        name: string name of timer
        cd is the timer call back function
    '''
    timers[name] = QtCore.QTimer(MainWin)
    timers[name].timeout.connect(cb)


def timersStop(timers=timers):
    '''
        Call stop for all timers to make sure they all stop
    '''
    for key, t in timers.iteritems():
        t.stop()


def enter_metadata_entry(self=self, MainWin=MainWin, timers=timers):
    w = MainWin.app.activeWindow()
    if 'saveMetadataDialog' in str(type(w)):
        w.changeLogEntryText.setText("DMF lite simple flowsheet test")
        w.continueButton.click()
        timers["enter_metadata_entry"].stop()


def save_dmflite(self=self, MainWin=MainWin, timers=timers):
    def tree_traveller(item):
        index = item.index()
        name = index.model().itemFromIndex(
            index.sibling(index.row(), 0)).text()
        kind = index.model().itemFromIndex(
            index.sibling(index.row(), 2)).text()
        if name == os.environ["USERNAME"]:
            tree_view.setCurrentIndex(index)
            w.filesystem.save_button.click()
            return
        if kind == "Folder" and item.hasChildren():
            for r in xrange(item.rowCount()):
                tree_traveller(item.child(r, 0))

    w = MainWin.app.activeWindow()
    w_type = str(type(w))
    if 'DMFBrowser' in w_type:
        tree_view = w.filesystem.tree_view
        for i in xrange(tree_view.model().rowCount()):
            tree_traveller(tree_view.model().item(i, 0))
        timers["save_dmflite"].stop()


def close_dmflite(self=self, MainWin=MainWin, timers=timers):
    w = MainWin.app.activeWindow()
    w_type = str(type(w))
    if 'SaveOverwriteFileDialog' in w_type:
        w.accept()  # Save as major version
    elif 'StatusDialog' in w_type:
        for c in w.children():
            if 'QLabel' in str(type(c)) and "Error" not in c.text():
                w.accept()
                timers["close_dmflite"].stop()


def save_session_opt(self=self, MainWin=MainWin, timers=timers):
    w = MainWin.app.activeWindow()
    w_type = str(type(w))
    if 'QMessageBox' in w_type:
        for b in w.buttons():
            if 'No' in b.text():
                b.click()
                timers["save_session_opt"].stop()


def select_from_dmf(
        self=self, MainWin=MainWin, timers=timers, timestamp=timestamp):

    def tree_traveller(item):
        index = item.index()
        name = index.model().itemFromIndex(
            index.sibling(index.row(), 0)).text()
        kind = index.model().itemFromIndex(
            index.sibling(index.row(), 2)).text()
        if name == "dmflitetest" + str(timestamp) + ".foqus":
            tree_view.setCurrentIndex(index)
            w.filesystem.open_button.click()
            return
        if kind == "Folder" and item.hasChildren():
            for r in xrange(item.rowCount()):
                tree_traveller(item.child(r, 0))

    w = MainWin.app.activeWindow()
    w_type = str(type(w))
    if 'DMFBrowser' in w_type:
        tree_view = w.filesystem.tree_view
        for i in xrange(tree_view.model().rowCount()):
            tree_traveller(tree_view.model().item(i, 0))
        timers["select_from_dmf"].stop()


def check(self=self, MainWin=MainWin, timers=timers,
          state_q=state_q, test_output=test_output):
    max_buffer_size = 10
    w = MainWin.app.activeWindow()
    w_type = str(type(w))
    w_id = str(w.winId())
    if len(set(state_q)) == 1 and len(state_q) >= max_buffer_size:
        w.close()
        timers["check"].stop()
        with open(test_output, 'a') as f:
            f.write("Error: Stuck in same state for too long.")
    else:
        if len(state_q) >= max_buffer_size:
            state_q.pop(0)
        state_q.append(w_id)


addTimer("check", check)
addTimer("enter_metadata_entry", enter_metadata_entry)
addTimer("save_dmflite", save_dmflite)
addTimer("close_dmflite", close_dmflite)
addTimer("save_session_opt", save_session_opt)
addTimer("select_from_dmf", select_from_dmf)

try:
    # Test save session
    while True:
        timers['check'].start(1000)

        # Make a test flowsheet
        MainWin.fsEditAction.trigger()
        if not go(): break
        # Add nodes
        MainWin.addNodeAction.trigger()
        if not go(): break
        node1 = "bfb"
        node2 = "cost"
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=-100, dbg_y=10, dbg_name=node1)
        MainWin.flowsheetEditor.sc.mousePressEvent(
            None, dbg_x=100, dbg_y=10, dbg_name=node2)

        # Add edges
        MainWin.addEdgeAction.trigger()
        MainWin.flowsheetEditor.sc.selectedNodes.append(unicode(node1))
        MainWin.flowsheetEditor.sc.selectedNodes.append(unicode(node2))
        MainWin.flowsheetEditor.sc.p.dat.flowsheet.addEdge(
            MainWin.flowsheetEditor.sc.selectedNodes[0],
            MainWin.flowsheetEditor.sc.selectedNodes[1])
        MainWin.flowsheetEditor.sc.selectedNodes[:] = []

        # Click home/session button
        MainWin.homeAction.trigger()

        # Enter metadata information
        MainWin.dashFrame.sessionNameEdit.setText(
            "dmflitetest" + str(timestamp))

        timers['enter_metadata_entry'].start(1000)
        timers['save_dmflite'].start(1000)
        timers['close_dmflite'].start(1000)

        MainWin.saveDMFLiteSessionAction.trigger()
        if not go():
            break

        # Test open session
        MainWin.homeAction.trigger()
        timers['save_session_opt'].start(1000)
        timers['select_from_dmf'].start(1000)

        MainWin.openDMFLiteSessionAction.trigger()
        if not go():
            break
        timersStop()
        break

except Exception as e:
    print "Exception stopping script"
    timersStop()
    with open(test_output, 'a') as f:
        f.write("Exception: {0}\n".format(e))
    raise(e)

timersStop()  # make sure all timers are stopped
