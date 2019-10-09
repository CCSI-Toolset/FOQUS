#include <math.h>
#include <stdio.h>
#include <stdlib.h>

main(int argc, char **argv)
{
   int    nInputs;
   double X1, X2, X3, X4, D1, D2, D3, D4, W1, W2, W3, W4, T1, T2, Y;
   double alpha=5, beta=1, delta=-10, gamma3, gamma4;
   FILE   *fIn  = fopen(argv[1], "r");
   FILE   *fOut;

   if (fIn == NULL)
   {
      printf("Simulator ERROR - cannot open in/out files.\n");
      exit(1);
   }
   fscanf(fIn, "%d", &nInputs);
   fscanf(fIn, "%lg", &D1);
   fscanf(fIn, "%lg", &D2);
   fscanf(fIn, "%lg", &D3);
   fscanf(fIn, "%lg", &D4);
   fscanf(fIn, "%lg", &X1);
   fscanf(fIn, "%lg", &X2);
   fscanf(fIn, "%lg", &X3);
   fscanf(fIn, "%lg", &X4);
   fscanf(fIn, "%lg", &W1);
   fscanf(fIn, "%lg", &W2);
   fscanf(fIn, "%lg", &W3);
   fscanf(fIn, "%lg", &W4);
   fclose(fIn);
   X1 = - W1;
   gamma3 = 1 + W3 * W3;
   gamma4 = 1 + W4 * W4;
   X2 = - (delta + beta * D2 * gamma4 + beta * gamma4 * W2) / (beta * gamma4);
   X3 = - (delta * W3 + D3 * gamma3 * gamma4 + gamma3 * gamma4 * W3) / (gamma3 * gamma4);
   T1 = delta * gamma3 + beta * delta * W3 * W3 + beta * gamma3 * gamma4 * W2;
   T2 = beta * gamma3 * gamma4 * W3 * W3 + beta * D2 * gamma3 * gamma4;
   T1 = T1 + T2;
   T2 = beta * D4 * gamma3 * gamma4;
   T1 = T1 - T2;
   T2 = beta * delta * gamma3 * gamma4 + beta * D3 * gamma3 * gamma4 * W3;
   X4 = (T1 + T2) / (beta * gamma3 * gamma4 * gamma4);

   Y = (X1 + W1) * (X1 + W1);
   Y = Y + beta * pow(X2 + W2 + D2, 2.0);
   Y = Y + (1 + W3 * W3) * pow(X3 + D3 + W3, 2.0);
   T1 = pow(D4 + X2 + W3 * X3 + X4 * (1 + W4 * W4), 2.0);
   Y = Y + 1.0/(1+W4*W4) * T1;
   Y = Y - 2.0 * delta * X4;
   Y = Y + alpha * pow(D1+W1, 2.0);
   Y = Y + (10 - alpha) * D1 * D1;
   Y = Y + (10 - beta) * D2 * D2;
   Y = Y + 3 * D3 * D3;
   Y = Y + D4 * D4 * sqrt(1+W3*W3+W4*W4);
   fOut = fopen(argv[2], "w");
   fprintf(fOut, " %24.16e\n", Y);
   fclose(fOut);   
}

