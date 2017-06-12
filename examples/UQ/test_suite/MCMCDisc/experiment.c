#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <sys/time.h>

double getClock();

main(int argc, char **argv)
{
   int    ii, ntime;
   double X1, X2, Y, dtime;
   FILE   *fp;

   fp = fopen("expdata","w");
   if (fp == NULL)
   {
      printf("ERROR - cannot write to expdata file.\n");
      exit(1);
   }
   dtime = getClock();
   ntime = (int) (dtime * 1.0E6);
   ntime = ntime % 10000;
   dtime = getClock();
   ntime = ntime * 10000 + (int) (dtime * 1.0E6);
   srand48((long) ntime);
   fprintf(fp, "PSUADE_BEGIN\n");
   fprintf(fp, "21 1 1 1\n");
   X2 = 0.9;
   X1 = 0.6;
   for (ii = 0; ii < 21; ii++) 
   {
      Y = X1 + X2 + X1 * X2;
      fprintf(fp, "%d %e %e 0.05\n", ii+1, X1, Y);
      X1 = X1 + 0.3/20;
   }
   fprintf(fp, "PSUADE_END\n");
   fclose(fp);
}

double getClock()
{
   double time_i;
   double time_d;
   struct timeval tp;
   struct timezone tzp;
   gettimeofday(&tp,&tzp);
   time_i = tp.tv_sec % 10;
   time_d = (double) time_i;
   time_i = tp.tv_usec;
   time_d = time_d + (double) time_i / 1000000.0;
   return(time_d);
}


