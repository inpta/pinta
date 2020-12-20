/*****************************************************************************
                             GLEANCANDS.C

  This program looks at the best file and eliminates 100 Hz and harmonic 
  candidates. It also compares candidates with a standard birdie file 
  and finally produces an output file with remaining valid candidates. 
  The program also produces DM curves for these.

  BCJ 22/03/2007
******************************************************************************/

#include <stdio.h>
#include <string.h>


int main(int argc, char *argv[])
{
int       i, ibird;
int       nbird;

float     birdie[500];

char      line[500];

FILE      *fbest, fbirdie;


  fbest = fopen( argv[1], "r" );
  if ( argc == 3 ) 
    {
      fbirdie = fopen( argv[1], "r" );
      while ( !feof(fbirdie) ) 
	{
	  fscanf( fbirdie, "%f", &birdie[i++]);
	}
      nbird = i;
      fclose(fbirdie);
    }

  while( !feof(fbest) )
    {
      fscanf( fbest, "%s", line );
      

read best file
skip text till first cand
if first cand not 100 Hz check 100 Hz flag
if not text if not harmonic if not birdie if not 100 Hz flag check against 
                     100 Hz if not write out
				     else write out
else skip text
till eof


  fclose( fbest);
  return(0);
} 
