.. _tutorial.fs.remote.turbine:

Using a Remote Turbine Instance
===============================

A remote Turbine instance may be used instead of TurbineLite.
TurbineLite, used by default, runs simulations (e.g., Aspen Plus) on the
user’s local machine. The remote Turbine gateway has several potential
advantages over TurbineLite, while the main disadvantage is the effort
required for installation and configuration. Some reasons to run a
remote Turbine instance are:

-  Simulations can be run in parallel. The Turbine gateway can
   distribute simulations to multiple machines configured to run FOQUS
   flowsheet consumers. FOQUS consumers are basically additional
   instances of FOQUS running on remote systems which can run a FOQUS
   flowsheet.

-  Simulations can be run on machines other than the user’s, so as not
   to tie-up the user’s machine running simulations.

The steps below demonstrate how to set up FOQUS to run flowsheets
remotely (see Figure `[fig.remote.settings] <#fig.remote.settings>`__).

#. Obtain a user name, password, and URL from the site’s Turbine
   administrator.

#. Open FOQUS.

#. Click **Settings** at the top right of the Home window (Figure
   `[fig.remote.settings1] <#fig.remote.settings1>`__).

#. Select “Remote” from the **FOQUS Flowsheet Run Method** drop-down
   list. A message box will appear. The user will be warned that the
   models that have been uploaded to Turbine Local may not be available
   in Turbine Remote Gateway, which means that the user may need to
   upload the models into Turbine again (please see Step 7).

#. Click the **Turbine** tab; this displays the Turbine settings shown
   in Figure `[fig.remote.settings] <#fig.remote.settings>`__.

.. figure:: ../figs/settings_turbine_01.svg
   :alt: Run Method Settings
   :name: fig.remote.settings1

   Run Method Settings

6. Create a Turbine configuration file; this contains your password in
   plain text, so it is very important that if you are allowed to choose
   your own password, you choose one that is not used for any other
   purpose.

   #. Click **New/Edit** next to the **Turbine Configuration (remote)**
      field. The Turbine Configuration window displays (see Figure
      `[fig.remote.settings] <#fig.remote.settings>`__).

   #. Select “Cluster/Cloud” from the **Turbine Gateway Version**
      drop-down list in the Turbine Configuration window.

   #. Enter the Turbine URL in the **Address** field.

   #. Enter the **User** name and **Password**.

   #. Click **Save as** and enter a new file name.

   #. Set the remote Turbine configuration file. Click **Browse** next
      to the **Turbine Configuration (remote)** field. Select the file
      created in Step 6e.

.. figure:: ../figs/remoteSetting.svg
   :alt: Remote Turbine Settings
   :name: fig.remote.settings

   Remote Turbine Settings

At this point the remote gateway is ready to use. The last step is to
ensure that all simulations referenced by flowsheets to be run are
uploaded to the remote Turbine gateway.

7. Upload any necessary simulations to Turbine (see Section
   `[overview.turbine.upload] <#overview.turbine.upload>`__ and the
   tutorial in Section
   `[tutorial.sim.flowsheet] <#tutorial.sim.flowsheet>`__)

Once all settings are specified there is no apparent difference between
running flowsheets locally or on a remote Turbine gateway, and FOQUS can
readily be switched between the two.
