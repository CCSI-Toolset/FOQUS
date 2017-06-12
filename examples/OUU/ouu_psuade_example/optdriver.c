#include <math.h>
#include <stdio.h>
#include <stdlib.h>

main(int argc, char **argv)
{
   int    nInputs, ii, lineLeng=1000, numfixed, cnt;
   double XX[12], value;
   double X1, X2, X3, X4, D1, D2, D3, D4, W1, W2, W3, W4, T1, T2, Y;
   double alpha=5, beta=1, delta=-10, gamma3, gamma4;
   char   line[1001], winput[1001], winput2[1001], winput3[1000], name[1000];
   FILE   *fIn  = fopen(argv[1], "r");
   FILE   *fOut;

   if (fIn == NULL)
   {
      printf("Simulator ERROR - cannot open in/out files.\n");
      exit(1);
   }
   fscanf(fIn, "%d", &nInputs);
   for (ii = 0; ii < nInputs; ii++) fscanf(fIn, "%lg", &XX[ii]);
   fgets(line, lineLeng, fIn);
   fgets(line, lineLeng, fIn);
   sscanf(line,"%s", winput);
   D1 = D2 = D3 = D4 = 1e35;
   X1 = X2 = X3 = X4 = 1e35;
   W1 = W2 = W3 = W4 = 1e35;
   if (!strcmp(winput, "num_fixed"))
   {
      sscanf(line,"%s %s %d", winput, winput2, &numfixed);
      for (ii = 0; ii < numfixed; ii++)
      {
         fgets(line, lineLeng, fIn);
         sscanf(line,"%s %s %s %s %lg",winput,winput2,name,winput3,&value);
         if (!strcmp(name,"D1")) D1 = value;
         if (!strcmp(name,"D2")) D2 = value;
         if (!strcmp(name,"D3")) D3 = value;
         if (!strcmp(name,"D4")) D4 = value;
         if (!strcmp(name,"X1")) X1 = value;
         if (!strcmp(name,"X2")) X2 = value;
         if (!strcmp(name,"X3")) X3 = value;
         if (!strcmp(name,"X4")) X4 = value;
         if (!strcmp(name,"W1")) W1 = value;
         if (!strcmp(name,"W2")) W2 = value;
         if (!strcmp(name,"W3")) W3 = value;
         if (!strcmp(name,"W4")) W4 = value;
      }
      cnt = 0;
      if (D1 == 1e35) D1 = XX[cnt++];
      if (D2 == 1e35) D2 = XX[cnt++];
      if (D3 == 1e35) D3 = XX[cnt++];
      if (D4 == 1e35) D4 = XX[cnt++];
      if (X1 == 1e35) X1 = XX[cnt++];
      if (X2 == 1e35) X2 = XX[cnt++];
      if (X3 == 1e35) X3 = XX[cnt++];
      if (X4 == 1e35) X4 = XX[cnt++];
      if (W1 == 1e35) W1 = XX[cnt++];
      if (W2 == 1e35) W2 = XX[cnt++];
      if (W3 == 1e35) W3 = XX[cnt++];
      if (W4 == 1e35) W4 = XX[cnt++];
   }
   else
   {
      D1 = XX[0]; D2 = XX[1]; D3 = XX[2]; D4 = XX[3];
      X1 = XX[4]; X2 = XX[5]; X3 = XX[6]; X4 = XX[7];
      W1 = XX[8]; W2 = XX[9]; W3 = XX[10]; W4 = XX[11];
   }
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

