import sys
import os
#import scipy
#from astLib import astWCS

class FoundStar:
    pass

if len(sys.argv) != 4:
    print "Usage: convert_hstphot_list catalog.txt outputfilestem global_mode"
    sys.exit(1)

list_filename=sys.argv[1]
output_filestem=sys.argv[2]
global_mode=(int(sys.argv[3])!=0)

print "Expecting global coords?", global_mode

list_file = open(list_filename,'rb')
lines=list_file.readlines()


print len(lines)
stars=[]

mode_index_offset=0
if(global_mode):
    mode_index_offset=1 #if the catalog has been converted to global co-ordinates then the first column (chip number) has been cut out

for i in range(0,len(lines)):
    if(lines[i][0]=='#'): continue

    tokens=lines[i].split()
    this_star=FoundStar()
    if(global_mode==False):
        this_star.detector=int(tokens[0])
    this_star.x=float(tokens[1-mode_index_offset])
    this_star.y=float(tokens[2-mode_index_offset])
    this_star.chi=float(tokens[3-mode_index_offset])
    this_star.signal=float(tokens[4-mode_index_offset])
    this_star.sharpness=float(tokens[5-mode_index_offset])
    this_star.roundness=float(tokens[6-mode_index_offset])
    this_star.filter_flight_sys_mag=float(tokens[11-mode_index_offset])
    stars+=[this_star]

#if(os.path.isfile(output_filename)):
#    print "Output already exists, will not overwrite, exiting"
#    sys.exit(0)

counter=0
good_count=0
reject_count=0

if(global_mode==False):
    for i in range(0,4):
        good_output_filename = output_filestem+"_CCD_"+str(i)+"_pass.reg"
        good_region_file = open(good_output_filename, 'w')
        reject_output_filename = output_filestem+"_CCD_"+str(i)+"_fail.reg"
        reject_region_file = open(reject_output_filename, 'w')

        common_file_header="# Region file format: DS9 version 4.1"+"\n"
        common_file_header+="# Filename:"+"\n"

        good_file_header=common_file_header;
        good_file_header+="global color=green dashlist=8 3 width=1 font=\"helvetica 10 normal\" select=1 highlite=1 dash=0"+"\n"
        good_file_header+="image"+"\n"
        good_region_file.write(good_file_header)

        reject_file_header=common_file_header
        reject_file_header+="global color=red dashlist=8 3 width=1 font=\"helvetica 10 normal\" select=1 highlite=1 dash=0"+"\n"
        reject_file_header+="image"+"\n"
        reject_region_file.write(reject_file_header)

        for star in stars:
            if(star.detector==i):
                outline = "point("+str(star.x)+","+str(star.y)+") # point=x" +"\n"
    #            if(1): ##pass all markers
    #            if( (star.signal>50 and star.chi<1.5 and star.roundness<0.5) ): #or (star.signal>35 and star.chi<1) ): #over 12 images
                if( star.chi<3 and star.sharpness>-0.5 and star.sharpness<0.5 and star.filter_flight_sys_mag<18):
                    good_region_file.write(outline)
                    good_count+=1
                else:
                    reject_region_file.write(outline)
                    reject_count+=1
                print counter, "of", len(stars),"(detector",i,";"
                counter+=1

        good_region_file.close()
        reject_region_file.close()



elif(global_mode==True):
    good_output_filename = output_filestem+"_global_pass.reg"
    good_region_file = open(good_output_filename, 'w')
    reject_output_filename = output_filestem+"_global_fail.reg"
    reject_region_file = open(reject_output_filename, 'w')

    common_file_header="# Region file format: DS9 version 4.1"+"\n"
    common_file_header+="# Filename:"+"\n"

    good_file_header=common_file_header;
    good_file_header+="global color=green dashlist=8 3 width=1 font=\"helvetica 10 normal\" select=1 highlite=1 dash=0"+"\n"
    good_file_header+="image"+"\n"
    good_region_file.write(good_file_header)

    reject_file_header=common_file_header
    reject_file_header+="global color=red dashlist=8 3 width=1 font=\"helvetica 10 normal\" select=1 highlite=1 dash=0"+"\n"
    reject_file_header+="image"+"\n"
    reject_region_file.write(reject_file_header)

    for star in stars:
        outline = "point("+str(star.x)+","+str(star.y)+") # point=x" +"\n"
#            if(1): ##pass all markers
#            if( (star.signal>50 and star.chi<1.5 and star.roundness<0.5) ): #or (star.signal>35 and star.chi<1) ): #over 12 images
        if( star.chi<3 and star.sharpness>-0.5 and star.sharpness<0.5 ):
            good_region_file.write(outline)
            good_count+=1
        else:
            reject_region_file.write(outline)
            reject_count+=1
        print counter, "of", len(stars),"(detector",i,";"
        counter+=1

    good_region_file.close()
    reject_region_file.close()
    
    
print "Output",good_count,"selected stars"
print "Output",reject_count,"rejected stars"

    