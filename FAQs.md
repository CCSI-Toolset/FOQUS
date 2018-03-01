# FOQUS Frequently Asked Questions (FAQs)

## When installing FOQUS, I get the error "Download error on https://pypi.python.org/simple/: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed". What should I do?

Note the library that is causing the SSL error. Try `pip --trusted-host pypi.python.org install -U xxx` where `xxx` is the library name. Then try your install command again. If the same error occurs with a different library, repeat as needed until all libraries are successfully installed. If you still have trouble, contact the FOQUS developers.


## FOQUS can’t find PSUADE, what should I do?

FOQUS looks for PSUADE using the PSUADE path. To find out which PSUADE file FOQUS is using, go to the “Settings” button at the top of the Home window.
Make sure the path in the PSUADE EXE entry matches the path of your PSUADE executable in your system.


## When setting up the variables in the Optimization Under Uncertainty (OUU) module, I want to load my own sample for Uncertainty Quantification (UQ) variables Z3 and/or Z4. How should I proceed?

Under the UQ Setup tab, select load existing sample for Z4 (or Z3 if applicable).
Click the 'Browse' button and find the correct sample file. Make sure your file is in the correct format.
