c=============================================================================
      program seeknew
c=============================================================================
c
c     A program (formerly known as find) to seek for periodic signals in data
c
c     Created: 97/11/21 (dunc@mpifr-bonn.mpg.de)
c
c     Modification history:
c
c     98/04/10 - (dunc) added acceleration capability (no longer need rbin)
c     98/04/30 - (dunc) source code overhauled. Now more user-friendly
c     98/11/20 - (dunc) added read and FFT capability for ".dis" files
c     99/07/08 - (dunc) added read spectrum file capability
c     01/02/15 - (dunc) added capability to read new data format ".tim" files
c     01/10/11 - (dunc) added -pmzap option and fixed call to zapit routine
c     02/03/01 - (dunc) added -pulse option to call Maura's single-pulse code
c     02/03/20 - (dunc) changed ordering of spectral zapping in dosearch.f
c     02/03/21 - (dunc) added -pzero option to pad with zeros if need be
c     02/03/21 - (dunc) make pmax a command-line parameter
c     05/04/07 - (dunc) changed name of program to SEEK! to appease RNM et al.
c     05/04/28 - (dunc) added ability to read masks for all 5 harmonic folds
c     11/06/03 - (bcj) added seeknew for GMGPS broken survey
c
c=============================================================================
      implicit none
      include 'seek.inc'

c Code Added for GMGPS BCJ 03-06-2011      
      include 'csampacc.inc'
      include 'csamp.inc'
      integer ninfile, nfl
      character*80 infile(80)
      common /newskinc/ infile, ninfile
      integer ifile
c Code Added for GMGPS BCJ 03-06-2011      

      logical dump,rspc,acsearch,tanalyse,pmzap,pulse,append,pzero
      character*80 sfile
      real accn,adot
      real*8 pmax
      integer llog, i, npf      
      call seekinnew(llog,dump,rspc,pmzap,sfile,pulse,append,pzero,
     &		  pmax,nofft,spthresh,ncandsmax,nsmax)

c Code Added for GMGPS BCJ 03-06-2011      
      ifile = 1
      write(*,*) ninfile
      do while(ifile .le. ninfile)
         if( ninfile .gt. 1 ) then
            filename = infile(ifile)
            if (index(filename,'.tim').gt.0) then
               lst=index(filename,'.tim')-1
            else
               stop 'file type not recognized! Type seek for help.'
            endif
         endif
         ifile = ifile + 1
         write(*,*) ifile
c Code Added for GMGPS BCJ 03-06-2011      

      accn=refac
      adot=refad
      call timstart(llog)                    ! fire up the ship's clock
      if (.not.rspc) call readdat(llog,pzero)! read in the time series 
      if (pulse) then
        call baseline(llog)
        call singlepulse(llog,append,spthresh,ncandsmax,nsmax)
      endif
      if (.not.nofft) then
      if (accn.ne.0.0) refac=accn
      if (adot.ne.0.0) refad=adot
      acsearch=accn.ne.0.0.or.adot.ne.0.0
      tanalyse=(index(filename,'.ser').gt.0.0)
     &     .or.(index(filename,'.tim').gt.0.0)
     &     .or.(index(filename,'.dis').gt.0.0)
      if (rspc) tanalyse=.false.
      if (tanalyse) then                     ! (time series analysis only)
         if (acsearch) call resample(llog)   ! re-sample time series
         call fftdata(llog)                  ! fft the data
      endif                                  ! (standard analysis follows)

c Code Added for GMGPS BCJ 03-06-2011      

      nfl=real(tsamp)*ntim/real(pmax)
      write(llog,*) 'Forming power spectrum. (Pmax=',pmax,' s!)'
      call accspec(npf, nfl, ifile)
      endif
      enddo
      i = 1
      do while( i .le. npf ) 
         samp(i) = sampacc(i)
         i = i + 1
      enddo
      call dosearchnew(llog,dump,rspc,pmzap,sfile,pmax)! search Fourier spectrum

c Code Added for GMGPS BCJ 03-06-2011      

      call timfinis(llog)                    ! stop the clock
      end
c=============================================================================
