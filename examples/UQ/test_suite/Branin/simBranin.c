#include <math.h>
#include <stdio.h>
#include <stdlib.h>

main(int argc, char **argv)
{
   int    n, i;
   double *X, Y, a, b, c, d, e, f, pi=3.1415928;
   char   lineIn[100], stringPtr[100], equal[2];

   FILE  *fIn  = fopen(argv[1], "r");
   FILE  *fOut;
   if (fIn == NULL)
   {
      printf("Branin ERROR - cannot open in/out files.\n");
      exit(1);
   }
   fscanf(fIn, "%d",  &n);
   X = (double *) malloc(n * sizeof(double));
   for (i = 0; i < n; i++) fscanf(fIn, "%lg", &X[i]);
   fclose(fIn);

   a = 1; b = 5.1 / (4.0 * pi * pi);
   c = 5 / pi; d = 6; e = 10; f = 0.125 / pi;

   Y = e;
   Y += (a * pow(X[1] - b * X[0] * X[0] + c * X[0] - d, 2.0));
   Y += (e * (1 - f) * cos(X[0]));
   free(X);
   fOut = fopen(argv[2], "w");
   fprintf(fOut, "%24.16e\n", Y);
   fclose(fOut);
   return 0;
}
