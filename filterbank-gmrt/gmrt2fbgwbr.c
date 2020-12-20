/* 
   gmrt2fb - converts GMRT search-mode data into "filterbank" data 
   adapted from f77 code gmrt2fb. This version produces identical
   16-bit data to the f77 version but also has a new 8-bit option
   which subtracts a mean from the data and writes the result as an
   unsigned character. The resulting output is centred on 128. This
   appears to be just as good as the 16-bit mode. drl-July-20-2005
*/
#include "filterbank.h"
void gmrt2fbgwbr(FILE *input, FILE *output, int nch) /* includefile*/
{
  double mean,sum,num;
  short junk,result[16384];
  unsigned short ur[16384];
  int c,r,opened;
  char string[80];
  unsigned char uc[16384];
  r=opened=0;
  c=0;
  sum=num=0.0;
  while (!ferror(input)) {
    if ( (fread(&junk,2,1,input)) != 1) return;
    result[c++]= ((junk));
    if (c==nch) {
      r++;
      if (r>10) {
	for (c=0;c<nch;c++) {
	  ur[c]=result[c];
	  uc[c]=128+((double)result[c]-mean);
	}
//	for(c=0; c<100 ; c++)
//	  {
//	    ur[c] = 0;
//	    uc[c]=0;
//	  }
//	for(c=nch-100; c<nch ; c++)
//	  {
//	    ur[c] = 0;
//	    uc[c]=0;
//	  }
//	ur[0]=ur[1]=ur[nch]=ur[511]=0;
//	uc[0]=uc[1]=uc[510]=uc[511]=0;
	if (obits==16) 
	  fwrite(ur,sizeof(short),nch,output);
	if (obits==8)
	  fwrite(uc,sizeof(char),nch,output);
      } else {
	/* for some reason, the first 10 samples were not
           used in the f77 code, so repeat that here but
           use these samples to calculate a mean 
           BCJ Modified 19-12-15 use these samples for ur, but not 
           for uc where calculate mean */
	for (c=0;c<nch;c++)  ur[c]=result[c];
//	for(c=0; c<100 ; c++)	    ur[c] = 0;
//	for(c=nch-100; c<nch ; c++)	    ur[c] = 0;
	if (obits==16) 
	  fwrite(ur,sizeof(short),nch,output);
	for (c=0;c<nch;c++) {
	  sum+=result[c];
	  num+=1.0;
	}
	mean=sum/num;
      }
      if (r%1024 == 0) {
	if (!opened) {
	  open_log("filterbank.monitor");
	  opened=1;
	}
	sprintf(string,"time:%.1fs",r*tsamp);
	update_log(string);
      }
      c=0;
    }
  }
}
