summary_file=pinta_summary.txt
echo "" >> $summary_file
echo "pinta Output Summary" >> $summary_file
echo "Generated using pdmp" >> $summary_file
echo "User : " `whoami` >> $summary_file
echo "Time : " `date -Iseconds` >> $summary_file
echo "FILENAME    MJD    DM    S/N" >> $summary_file
awk '{print $8, $1, $4, $7}' pdmp.per >> $summary_file

