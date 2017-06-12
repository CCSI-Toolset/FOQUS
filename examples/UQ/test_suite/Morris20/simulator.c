#include <math.h>
#include <stdio.h>
#include <stdlib.h>

#define PABS(X) (((X) > 0) ? X : -(X))

main(int argc, char **argv)
{
   int    count, i, j, k, m;
   double X[20], Y, W[20];
   FILE   *fIn  = fopen(argv[1], "r");
   FILE   *fOut = fopen(argv[2], "w");

   if (fIn == NULL || fOut == NULL)
   {
      printf("Simulator ERROR - cannot open in/out files.\n");
      exit(1);
   }
   fscanf(fIn, "%d", &count);
   if (count != 20)
   {
      printf("Simulator ERROR - wrong nInputs.\n");
      exit(1);
   }
   for (i = 0; i < 20; i++) fscanf(fIn, "%lg", &X[i]);
   for (i = 0; i < 20; i++) W[i] = 2.0 * (X[i] - 0.5);
   W[2] = 2.0 * (1.1 * X[2]/(X[2] + 0.1) - 0.5);
   W[4] = 2.0 * (1.1 * X[4]/(X[4] + 0.1) - 0.5);
   W[6] = 2.0 * (1.1 * X[6]/(X[6] + 0.1) - 0.5);
   Y = 1.0;
   for (i = 0; i < 10; i++) Y += 20.0 * W[i];
   for (i = 10; i < 20; i++) Y += (((double)rand())/((double)RAND_MAX)) * W[i];
   for (i = 0; i < 20; i++)
      for (j = i+1; j < 20; j++) 
         if (j < 6) Y -= 15.0 * W[i] * W[j];
         else       Y += (((double)rand())/((double)RAND_MAX)) * W[i] * W[j];
   for (i = 0; i < 20; i++)
      for (j = i+1; j < 20; j++)
         for (k = j+1; k < 20; k++)
            if (k < 5) Y -= 10.0 * W[i] * W[j] * W[k];
   for (i = 0; i < 20; i++)
      for (j = i+1; j < 20; j++)
         for (k = j+1; k < 20; k++)
            for (m = k+1; m < 20; m++)
               if (m < 4) Y += 5.0 * W[i] * W[j] * W[k] * W[m];
   fprintf(fOut, "%24.16e\n", Y);
   fprintf(fOut, "%24.16e\n", 2*Y);
   fprintf(fOut, "%24.16e\n", 5*Y);
   fprintf(fOut, "%24.16e\n", 10*Y);
   fclose(fIn);   
   fclose(fOut);   
}

