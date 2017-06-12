#include <math.h>
#include <stdio.h>
#include <stdlib.h>

main(int argc, char **argv)
{
   int    i, j, nInputs;
   double X[4], Y[4], F, AB[2], error, dtemp;
   FILE   *fIn  = fopen(argv[1], "r");
   FILE   *fOut;
                                                                                
   if (fIn == NULL)
   {
      printf("Simulator ERROR - cannot open in/out files.\n");
      exit(1);
   }
   fscanf(fIn, "%d", &nInputs);
   for (i = 0; i < nInputs; i++) fscanf(fIn, "%lg", &AB[i]);
   X[0] = 1/10.0; Y[0] = 0.0325;
   X[1] = 1/3.0; Y[1] = 1/6.0;
   X[2] = 2/3.0; Y[2] = 1/2.0;
   X[3] = 1/1.0; Y[3] = 1.0;
                                                                                
   fOut = fopen(argv[2], "w");
   for (i = 0; i < 4; i++)
   {
      dtemp = AB[0] * X[i] + AB[1] * X[i] * X[i];
      error = Y[i] - dtemp;
      fprintf(fOut, " %24.16e\n", error);
   }
   fclose(fOut);
}

