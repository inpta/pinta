c==============================================================================
      program plotpulses
c==============================================================================
      implicit none
      character*80 stem,line,pgdev
      integer lun,lst,npulses,width,idx,fft,maxp,i,narg,sym,
     &	      nsnbins,ndms,maxdmhist
      parameter(maxp=100000000)
      real tsamp,dm(maxp),sn(maxp),mindm,maxdm,minsn,maxsn,mints,maxts,
     &     time(maxp),thresh,snmid(10000),maxsnhist,snhist(10000),
     &     maxdmhst,dmhist(10000),dmval(10000),peakdm
c==============================================================================
      narg=iargc()
      if (narg.lt.1) then
	 write(*,*)
	 write(*,*) 'plotpulses - PGPLOT results of single pulse search'
	 write(*,*)
         write(*,*) 'usage: plotpulses filestem -s snmin -p pgdev'
	 write(*,*)
	 write(*,*) 'snmin - minimum s/n to display (def=5)'
	 write(*,*) 'pgdev - pgplot device (def=/xs)'
	 write(*,*)
         stop
      endif
      call getarg(1,stem)
      lst=index(stem,' ')-1
      minsn=5
      pgdev='/xs'
      if (narg.gt.1) then	
         i=2
	 do while (i.le.narg)
           call getarg(i,line)
	   if (line.eq.'-s') then
		i=i+1
                call getarg(i,line)
                read(line,*) minsn
	   elseif (line.eq.'-p') then
		i=i+1
                call getarg(i,pgdev)
	   endif
	   i=i+1
  	 enddo 
      endif
      i=0
      lun=20
      mints=1.0e32
      maxts=-1.0e32
      mindm=1.0e32
      maxdm=-1.0e32
      maxsn=0.0
c==============================================================================
      open(lun,file=stem(1:lst)//'.pls',status='unknown')
      read(lun,'(a)') line
      read(line(7:),*) tsamp
      read(line(24:),*) thresh
      do while(.true.)
         i=i+1
         read(lun,*,err=1,end=1) dm(i),width,idx,sn(i),fft
         time(i)=idx*tsamp/1.0e6
         mints=min(time(i),mints)
         maxts=max(time(i),maxts)
         mindm=min(dm(i),mindm)
         maxdm=max(dm(i),maxdm)
         maxsn=max(sn(i),maxsn)
	 snhist(sn(i)-thresh)=snhist(sn(i)-thresh)+1
      enddo
 1    close(lun)
      
      npulses=i-1
      nsnbins = maxsn-thresh
      maxsnhist = 0
      do i = 1, nsnbins
         snmid(i) = thresh+(i-1)+0.5
         if (snhist(i).ne.0) then
            snhist(i) = log10(snhist(i))
         else
            snhist(i) =-0.5
         endif
	 if (snhist(i).gt.maxsnhist) maxsnhist = snhist(i)
      end do

      open(lun,file=stem(1:lst)//'.hst',status='unknown')

      i = 0
      do while(.true.)
      i=i+1
      read (lun,*,err=1,end=2) dmval(i), dmhist(i)
      enddo
 2    close(lun)

      ndms = i-1
      maxdmhist = 0
      do i = 1, ndms
         if (dmhist(i).gt.maxdmhist) then
	     maxdmhist = dmhist(i)
	     peakdm = dmval(i)
	 endif
      end do
      write(line,100) npulses,maxsn,peakdm
 100  format(i8,' events. max S/N =',f5.1,'. peak DM =',f7.1,
     &       ' (cm\\u-3\\d pc)')
c==============================================================================
      call pgbegin(0,pgdev,1,1)
      call pgscf(2)
      call pgswin(0.0,1.0,0.0,1.0)
      call pgtext(-0.02,1.0,'Results for '//stem(1:lst)
     &      //' '//line)
      call pgsvp(0.06, 0.31, 0.6, 0.87)
      call pgswin(thresh,maxsn,log10(0.5),1.1*maxsnhist)
      call pgsch(0.8)
      call pgbox('bcnst',0.0,0,'bclnst',0.0,0)
      call pgmtxt('B', 2.5, 0.5, 0.5, 'Signal-to-Noise')
      call pgmtxt('L', 1.8, 0.5, 0.5, 'Number of Pulses')
      call pgsch(1.0)
      call pgbin(nsnbins,snmid,snhist,1)
      call pgsvp(0.39, 0.64, 0.6, 0.87)
      call pgswin(mindm-0.5,maxdm+0.5,0.0,1.1*maxdmhist)
      call pgsch(0.8)
      call pgbox('bcnst',0.0,0,'bcnst',0.0,0)
      call pgmtxt('B', 2.5, 0.5, 0.5, 'DM (cm\\u-3\\d pc)')
      call pgmtxt('L', 1.8, 0.5, 0.5, 'Number of Pulses')
      call pgsch(1.0)
      call pgbin(ndms,dmval,dmhist,1)
      call pgsvp(0.72, 0.97, 0.6, 0.87)
      call pgswin(mindm-0.5,maxdm+0.5,minsn,maxsn)
      call pgsch(0.8)
      call pgbox('bcnst',0.0,0,'bcnst',0.0,0)
      call pgmtxt('B', 2.5, 0.5, 0.5, 'DM (cm\\u-3\\d pc)')
      call pgmtxt('L', 1.8, 0.5, 0.5, 'Signal-to-Noise')
      call pgpt(npulses,dm,sn,20)
      call pgsvp(0.06, 0.97, 0.08, 0.52)
      call pgswin(mints,maxts,mindm,maxdm)
      call pgsch(0.8)
      call pgbox('bcnst',0.0,0,'bcnst',0.0,0)
      call pgmtxt('B',2.5,0.5,0.5,'Time (s)')
      call pgmtxt('L',1.8,0.5,0.5,'DM (cm\\u-3\\d pc)')
      do i=1,npulses
         sym=20
         if (sn(i).gt.5) sym=21
         if (sn(i).gt.7) sym=22
         if (sn(i).gt.9) sym=23
         if (sn(i).gt.10) sym=24
	 sym = (sn(i)-minsn)*0.5+20+0.5
	 if (sym.gt.25) sym = 25
         if (sn(i).gt.minsn) call pgpt1(time(i),dm(i),sym)
      enddo
      call pgend
      end
c==============================================================================
