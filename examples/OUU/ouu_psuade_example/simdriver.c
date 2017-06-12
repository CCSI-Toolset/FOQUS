#include <math.h>
#include <stdio.h>
#include <stdlib.h>

main(int argc, char **argv)
{
   int    ii, nInputs, nSamp;
   double X1, X2, D, W1, W2, W3, T1, Y;
   FILE   *fIn  = fopen(argv[1], "r");
   FILE   *fOut;

   if (fIn == NULL)
   {
      printf("Simulator ERROR - cannot open in/out files.\n");
      exit(1);
   }
   fscanf(fIn, "%d", &nSamp);
   fscanf(fIn, "%d", &nInputs);
   fOut = fopen(argv[2], "w");
   for (ii = 0; ii < nSamp; ii++)
   {
      fscanf(fIn, "%lg", &D);
      fscanf(fIn, "%lg", &X1);
      fscanf(fIn, "%lg", &X2);
      fscanf(fIn, "%lg", &W1);
      fscanf(fIn, "%lg", &W2);
      fscanf(fIn, "%lg", &W3);
      X1 = D - 0.5 * (3 * W1 + W3);
      T1 = 1 + W1 * W1;
      X2 = D - W2 - 0.5 * (W2 + W3) / T1;
      Y = pow(X1 - D + W1, 2.0) + (1 + W1 * W1) * pow(X2 - D + W2, 2.0) +
          (W1 + W3) * X1 + (W2 + W3) * X2 + pow(W2*W2+(2+W3*W3)*D, 2.0);
      fprintf(fOut, " %24.16e\n", Y);
   }
   fclose(fIn);
   fclose(fOut);   
}

