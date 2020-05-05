:orphan:

.. _full-format:

PSUADE Full Format
------------------
::

    PSUADE_IO (Note : inputs not true inputs if pdf  ̃=U) # Start data block
    5 2 6                                                # 5 inputs, 2 outputs, and 6 samples
    1 1                                                  # Sample index, run value (0 if sample point has not been calculated.)
      -9.5979899497487442e-01                            # Value to the first input of sample 1
      1.0552763819095490e-01                             # Value to the second input of sample 1
      2.1608040201005019e-01                             # Value to the third input of sample 1
      -2.1608040201005019e-10                            # Value to the fourth input of sample 1
      -2.5628140703517588e-01                            # Value to the fifth input of sample 1
      -1.6979984061153328e+00                            # Value to the first output of sample 1 (9.99e+34 if undefined)
      -7.8296928608517824e-01                            # Value to the second output of sample 1 (9.99e+34 if undefined)
    2 1                                                  # Sample point 2. Run value is true (outputs calculated)`
      -9.5477386934673336e-02
      8.5427135678391997e-02
      -9.7989949748743721e-01
      -4.8743718592964824e-01
      3.5175879396984966e-02
      9.7708275149071300e-01
      8.6655187317087226e-02
    3 1                                                  # Sample point 3. Run value is true (outputs calculated)
      -6.9849246231155782e-01
      -5.9798994974874375e-01
      -9.6984924623115576e-01
      2.5125628140703515e-02
      8.1909547738693478e-01
      -6.4229247835711212e-02
      2.8546752874255432e-01
    4 1                                                  # Sample point 4. Run value is true (outputs calculated)
      2.1608040201005019e-01
      7.2864321608040195e-01
      4.9748743718592969e-01
      5.6783919597989962e-01
      6.7839195979899491e-01
      -4.7115433927748318e-01
      -3.5869634004753126e-01
    5 1                                                  # Sample point 5. Run value is true (outputs calculated)
      5.6783919597989962e-01
      5.4773869346733672e-01
      -2.2613065326633164e-01
      3.8693467336683418e-01
      -1.7587939698492461e-01
      6.8926859881410230e-03
      -2.7551395275787588e-01
    6 0                                                  # Sample point 6. Run value is false (outputs not calculated)
      -7.2864321608040195e-01
      2.1608040201005019e-01
      8.3919597989949746e-01
      3.5175879396984966e-02
      2.3618090452261309e-01
      9.9999999999999997e+34                             # Output not calculated
      9.9999999999999997e+34                             # Output not calculated
    PSUADE_IO                                            # End data block
    PSUADE                                               # Start informational block
    INPUT                                                # Start input information block
      dimension = 5                                      # Number of inputs
      variable 1 A0 = -1.00000e+00 1.00000e+00           # Input name & range
      variable 2 A1 = -1.00000e+00 1.00000e+00
      variable 3 A2 = -1.00000e+00 1.00000e+00
      variable 4 A3 = -1.00000e+00 1.00000e+00
      variable 5 A4  =  -1.00000e+00   1.00000e+00
    END                                                  # End input information block
    OUTPUT                                               # Start output information block
      dimension = 2                                      # Number of outputs
      variable 1 Y1                                      # Output name
      variable 2 Y2
    END                                                  # End output information block
    METHOD                                               # Start sampling method information block
      sampling = LH                                      # Latin Hypercube sampling
      num_samples = 6                                    # Number of samples
    END                                                  # End sampling method block
    APPLICATION                                          # Start application block
      driver = NONE                                      # Name of driver program for calculating outputs (NONE for no driver)
    END                                                  # End application block
    ANALYSIS                                             # Start analysis method information block
      analyzer output_id = 1
      analyzer rstype = MARS                             # Default response surface type
      diagnostics 1
    END                                                  # End analysis method information block
    END                                                  # End information block
