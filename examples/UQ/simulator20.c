/******** 
% Copyright (c) 2012, Lawrence Livermore National Security, LLC.
% Produced at the Lawrence Livermore National Laboratory
% Written by Thomas Epperly <epperly2@llnl.gov>, James Leek <leek2@llnl.gov>,
%            Brenda Ng <ng30@llnl.gov>, Jeremy Ou <ou3@llnl.gov>, and
%            Charles Tong <tong10@llnl.gov>.
% LLNL-CODE-579212
% All rights reserved.
% 
% See LICENSE.md for license and copyright details.
***/
        
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <winsock.h>

#ifndef _WIN32
#include <sys/time.h>
#endif

double getClock();

int main(int argc, char **argv)
{
   int    nInputs, i, ntime, kk, jj, indices[20], nSelected;
   double X[20], Y, Z, dtime;
   char   lineIn[500], pString[100], name[100];
   FILE   *fp;
   FILE   *fIn  = fopen(argv[1], "r");
   FILE   *fOut;

   if (argc == 1)
   {
       printf("A simulator that implements a 20-to-1 random function.\n");
       printf("Usage: ./simulator <infile> <outfile>\n");
       exit(1);
   }
   if (fIn == NULL)
   {
      printf("Simulator ERROR - cannot open in/out files.\n");
      exit(1);
   }

   fscanf(fIn, "%d", &nInputs);

   /* compare against database */
   for (i = 0; i < 20; i++) indices[i] = 0;
   fp = fopen("selectedVars", "r");
   fgets(lineIn, 400, fp);  // skip PSUADE
   fgets(lineIn, 400, fp);  // skip INPUT
   fgets(lineIn, 400, fp);  // skip dimension = %d
   sscanf(lineIn, "%s %s %d", pString, name, &nSelected);
   for (i = 0; i < nInputs; i++)
   {
      fgets(lineIn, 400, fp);
      sscanf(lineIn, "%s %d %s", pString, &kk, name);
      if (!strcmp(name, "A0")) indices[0] = 1;
      if (!strcmp(name, "A1")) indices[1] = 1;
      if (!strcmp(name, "A2")) indices[2] = 1;
      if (!strcmp(name, "A3")) indices[3] = 1;
      if (!strcmp(name, "A4")) indices[4] = 1;
      if (!strcmp(name, "A5")) indices[5] = 1;
      if (!strcmp(name, "A6")) indices[6] = 1;
      if (!strcmp(name, "A7")) indices[7] = 1;
      if (!strcmp(name, "A8")) indices[8] = 1;
      if (!strcmp(name, "A9")) indices[9] = 1;
      if (!strcmp(name, "B0")) indices[10] = 1;
      if (!strcmp(name, "B1")) indices[11] = 1;
      if (!strcmp(name, "B2")) indices[12] = 1;
      if (!strcmp(name, "B3")) indices[13] = 1;
      if (!strcmp(name, "B4")) indices[14] = 1;
      if (!strcmp(name, "B5")) indices[15] = 1;
      if (!strcmp(name, "B6")) indices[16] = 1;
      if (!strcmp(name, "B7")) indices[17] = 1;
      if (!strcmp(name, "B8")) indices[18] = 1;
      if (!strcmp(name, "B9")) indices[19] = 1;
   } 
   fclose(fp);

   for (i = 0; i < 20; i++)
   {
       if (indices[i] == 1)
           fscanf(fIn, "%lg", &X[i]);
       else
           X[i] = 0.0;
   }
   fclose(fIn);   
   
   dtime = getClock();
   ntime = (int) (dtime * 1.0E6);
   ntime = ntime % 10000;
   dtime = getClock();
   ntime = ntime * 10000 + (int) (dtime * 1.0E6);
#ifdef _WIN32
   srand((long)ntime);
#else
   srand48((long) ntime);
#endif
   
   Y = 0.0;
   for (i = 0; i < 19; i++)
   {
       Z = 0.0;
       if (indices[i] == 1) {
           // generalized RosenBrock's function
           Z = 100*pow(pow(X[i],2)-X[i+1],2)+pow(1-X[i],2);
           if (i > 6)
               Z *= 0.000001;
           Y += Z;
       }
   }
#ifdef _WIN32
   Y += 0.00001 * (rand() / (RAND_MAX + 1.0));
#else
   Y += 0.00001 * drand48();
#endif

   fOut = fopen(argv[2], "w");
   fprintf(fOut, "%24.16e\n", Y);
   fclose(fOut);

   return 0;
}

double getClock()
{
#ifdef _WIN32
	SYSTEMTIME      beg;
	double time_d;

	GetLocalTime(&beg);
	time_d = (float)(beg.wSecond % 10) + beg.wMilliseconds / 1000.0;

#else
   double time_i;
   double time_d;
   struct timeval tp;
   struct timezone tzp; 
   gettimeofday(&tp,&tzp);
   time_i = tp.tv_sec % 10;
   time_d = (double) time_i; 
   time_i = tp.tv_usec;
   time_d = time_d + (double) time_i / 1000000.0;
#endif

   return(time_d);
}


