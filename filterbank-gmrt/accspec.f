c==========================================================================
      subroutine accspec(npf, nfl, ifile)
c==========================================================================
      implicit none
c
c     Accumalates the power spectrum from the real and imaginary
c     parts ffted array series(ntim) (see seek.inc) to nsampacc
c
c c Code Added for GMGPS BCJ 03-06-2011  full new sub

      include 'seek.inc'
      include 'csampacc.inc'
      integer npf, nfl, ifile
      integer i,j
      real arl,ail,a1,a2,ar,ai,anf

      anf=series(2)**2
      arl=0.0
      ail=0.0
      do i=1,2*nfl
         series(i)=0.0
      enddo

      npf=ntim/2
      do j=1,npf-1
        ar=series(2*j+1)
        ai=series(2*j+2)
        a1=ar**2+ai**2
        a2=((ar-arl)**2+(ai-ail)**2)/2.
        if( ifile .eq. 1 ) then 
           sampacc(j)=sqrt(max(a1,a2))
        else
           sampacc(j)= sampacc(j) + sqrt(max(a1,a2))
        endif
        arl=ar
        ail=ai
      enddo
      sampacc(npf)=0.0

      end
c==========================================================================
