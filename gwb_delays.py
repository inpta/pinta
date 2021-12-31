import numpy as np
import astropy.time as astrotime

def check_mjd(start_date, end_date, mjd):
    start_mjd = astrotime.Time(start_date).mjd
    end_mjd = astrotime.Time(end_date).mjd
    return start_mjd <= mjd < end_mjd

def check_bw(bw_category, bw):
    if bw_category == "ANY":
        return True
    elif bw_category == "200|400":
        return bw in [200,400]
    elif bw_category == "<=100":
        return bw <= 100
    else:
        raise ValueError("Invalid bw_category found.")

def check_cd(cd_category, cd):
    if cd_category not in ["ANY", '0', '1']:
        raise ValueError("Invalid cd_category found.")
    return (cd_category == "ANY") or (cd == bool(int(cd_category)))

def check_delay_category(delay_info, item):
    start_date, end_date, bw_category, cd_category = delay_info[:-1]
   
    return (    check_mjd(start_date, end_date, float(item.timestamp)) 
            and check_bw(bw_category, item.bandwidth)
            and check_cd(cd_category, item.cohded)
           )   

class GWBDelays:
    def __init__(self, delays_file):
        self.delays_info = np.genfromtxt(delays_file, dtype=str)
    
    def get_delay(self, item):
        for delay_info in self.delays_info:
            if check_delay_category(delay_info, item):
                delay = delay_info[-1]
                if delay == "ERR":
                    raise ValueError("No GWB delay found for the given item.")
                else:
                    print("[INFO] GWB delay (s) is", delay)
                    return float(delay)
        raise ValueError("No GWB delay found for the given item (*).")
        
        
        
        
