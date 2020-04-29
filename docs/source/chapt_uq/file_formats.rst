File Formats
============

Most UQ capabilities within FOQUS rely on PSUADE. As such, different UQ components require input files in PSUADE
formats. CSV (comma-separated values) files are also compatible. The specific requirements are explained in Sections
:ref:`_section_tutorial` and 6.


PSUADE Full File Format
-----------------------

The following is an example of the full PSUADE file format. Comments in red do not appear in the file and are only for
instructional purposes.
PSUADE_IO (Note : inputs not true inputs if pdf  ̃=U) :red: `Start data block`
5 2 6
1 1
 -9.5979899497487442e-01
  1.0552763819095490e-01
  2.1608040201005019e-01
 -2.1608040201005019e-10
 -2.5628140703517588e-01
 -1.6979984061153328e+00
 -7.8296928608517824e-01
2 1
-9.5477386934673336e-02
  8.5427135678391997e-02
 -9.7989949748743721e-01
 -4.8743718592964824e-01
  3.5175879396984966e-02
  9.7708275149071300e-01
  8.6655187317087226e-02
3 1
 -6.9849246231155782e-01
 -5.9798994974874375e-01
 -9.6984924623115576e-01
  2.5125628140703515e-02
  8.1909547738693478e-01
 -6.4229247835711212e-02
  2.8546752874255432e-01
4 1
  2.1608040201005019e-01
  7.2864321608040195e-01
  4.9748743718592969e-01
  5.6783919597989962e-01
  6.7839195979899491e-01
 -4.7115433927748318e-01
-3.5869634004753126e-01 51
  5.6783919597989962e-01
  5.4773869346733672e-01
5 inputs, 2 outputs, and 6 samples
Sample index, run value (0 if sample point has not been calculated.)
 Value to the first input of sample 1
 Value to the second input of sample 1
 Value to the third input of sample 1
 Value to the fourth input of sample 1
 Value to the fifth input of sample 1
 Value to the first output of sample 1 (9.99e+34 if undefined)
 Value to the second output of sample 1 (9.99e+34 if undefined)
Sample point 2. Run value is true (outputs calculated).
Sample point 3. Run value is true (outputs calculated).
Sample point 4. Run value is true (outputs calculated).
Sample point 5. Run value is true (outputs calculated).