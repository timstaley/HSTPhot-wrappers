import math
import sys
import os
#import scipy
#from astLib import astWCS

from kapteyn import wcs
import pyfits

class FoundStar:
    pass

if (len(sys.argv) < 3 or len(sys.argv) > 4) :
    print "Usage: convert_hstphot_list list.txt ref_raw_data_image.fits [ref_drizzled_SCI_image.fits]"
    sys.exit(1)


#run distortion correction
hst_distort_location="~/software/hstphot1.1/distort"

list_filename=sys.argv[1]
raw_data_ref_image_filename=sys.argv[2]

HLA_astrometry_corrected_image_filename=""
if(len(sys.argv)==4):
    HLA_astrometry_corrected_image_filename=sys.argv[3]

####################################################################################################################
#Run the distortion correction program on the raw output from HSTphot
##Rotation of 0.28 degrees is prescribed by Holtzman1995 to adjust the pixel co-ords to the nominal WCS,
##This must be added as a command line parameter to distort.

rotation_suffix = ""
#rotation_suffix = str(0.28+135)

print "Running distortion correction (local / global)"
hst_distort_command = hst_distort_location +" "+ list_filename + " "+ "local_distorted_" + list_filename+" "+ "0 "+rotation_suffix
print hst_distort_command
os.system(hst_distort_command)

hst_distort_command = hst_distort_location +" "+ list_filename + " "+ "global_distorted_" + list_filename+" "+ "1 "+rotation_suffix
print hst_distort_command
os.system(hst_distort_command)


####################################################################################################################
##Load stars from local list
local_list_file = open("local_distorted_"+list_filename,'rb')
local_list_lines=local_list_file.readlines()

print len(local_list_lines)
local_pix_stars_list=[]
#
for i in range(0,len(local_list_lines)):
    if(local_list_lines[i][0]=='#'): continue

    tokens=local_list_lines[i].split()
    this_star=FoundStar()
    this_star.detector= int(tokens[0])
    this_star.x=        float(tokens[1])
    this_star.y=        float(tokens[2])
    this_star.chi=      float(tokens[3])
    this_star.signal=   float(tokens[4])
    this_star.sharpness=float(tokens[5])
    this_star.roundness=float(tokens[6])
#    this_star.major_axis=float(tokens[7])
    this_star.object_type=float(tokens[8])
#    this_star.filter_counts=float(tokens[9])
#    this_star.filter_bg=float(tokens[10])
    this_star.filter_flight_sys_mag=float(tokens[11])
#    this_star.filter_standard_mag=float(tokens[12])

    local_pix_stars_list+=[this_star]

##Load stars from global list:
global_list_file = open("global_distorted_"+list_filename,'rb')
global_list_lines=global_list_file.readlines()


global_pix_stars_list=[]
#
for i in range(0,len(global_list_lines)):
    if(global_list_lines[i][0]=='#'): continue
    tokens=global_list_lines[i].split()

    this_star=FoundStar()
    this_star.detector=-1
    this_star.x=            float(tokens[0])
    this_star.y=            float(tokens[1])
    this_star.chi=          float(tokens[2])
    this_star.signal=       float(tokens[3])
    this_star.sharpness=    float(tokens[4])
    this_star.roundness=    float(tokens[5])
    this_star.object_type=  float(tokens[8-1])
    this_star.filter_flight_sys_mag=float(tokens[11-1])

    global_pix_stars_list+=[this_star]


####################################################################################################################
##Calculate CRPIX new position in global transformed co-ordinates

raw_hdulist = pyfits.open(raw_data_ref_image_filename)
raw_header = raw_hdulist[0].header

raw_CRPIX1 = raw_header["CRPIX1"]
raw_CRPIX2 = raw_header["CRPIX2"]

#convert to global distorted coords

print "Raw crpix1", raw_CRPIX1
#modifiy the header so it uses the corrected CRPIX_vals

distortion_corrected_header=raw_header.copy()

import global_PC_distort

transformed_crpix = global_PC_distort.transform_to_global_pixel_coords(0, raw_CRPIX1,raw_CRPIX2 )
#transformed_crpix = global_PC_distort.transform_to_global_pixel_coords(0, raw_CRPIX1,raw_CRPIX2, 0.28*180/math.pi )


distortion_corrected_header["CRPIX1"]=transformed_crpix[0]
distortion_corrected_header["CRPIX2"]=transformed_crpix[1]

print "Raw crpix1", raw_header["CRPIX1"]
print "corrected crpix1", distortion_corrected_header["CRPIX1"]

#now load it as a pixel / WCS transformation
distortion_corrected_map  = (wcs.Projection(distortion_corrected_header)).sub(nsub=2)

##########################################################################


#Chip to chip adjustments are approximate alterations to the Holtzman 1995 solution as determined by eye, by comparison with drizzled mosaics from HLA in 2010
#NB the HLA mosaics presumably use the Anderson 2003 solution, hence the discrepancy.
#Ideally the distortion correction should be rewritten to match Anderson's, but this is a stop gap measure that produces aesthetically pleasing (And presumably, approximately correct) plots.

WF_to_PC_pix = 2.187 #approximate pixel size ratio

#chip_adjustments_x=[0,  0, 0, 0]
#chip_adjustments_y=[0,  0, 0, 0]

chip_adjustments_x=[0,  0.6*WF_to_PC_pix, 1.3*WF_to_PC_pix, 0]
chip_adjustments_y=[0,  1.8*WF_to_PC_pix, 2.37*WF_to_PC_pix, 1*WF_to_PC_pix]
####################################################################################
#Ok, now calculate shift in sky coordinates as read from header of astrometry adjusted drizzle file

astrometry_correction_delta_CRVAL=(0,0)
if(HLA_astrometry_corrected_image_filename!=""):
    HLA_hdulist = pyfits.open(HLA_astrometry_corrected_image_filename)
    HLA_header = HLA_hdulist[1].header

    current_CRVAL = (float(HLA_header["CRVAL1"]), float(HLA_header["CRVAL2"]))
    original_CRVAL = (float(HLA_header["O_CRVAL1"]), float(HLA_header["O_CRVAL2"]))

    astrometry_correction_delta_CRVAL= (current_CRVAL[0]-original_CRVAL[0], current_CRVAL[1]-original_CRVAL[1])
    
    pass

####################################################################################
#Apply adjustment for chipnum in pixel space, then transform to sky-coords,
#then apply adjustment for CRVAL shift as determined from HLA mosaic with updated astrometry

counter=0

global_WCS_stars_good_lists=[[],[],[],[]] ##4 empty lists, will hold tuples of sky co-ords
global_WCS_stars_reject_lists=[[],[],[],[]] ##4 empty lists

for star_num in range(len(global_pix_stars_list)):
    star = global_pix_stars_list[star_num]
    chip_num = local_pix_stars_list[star_num].detector

    if(global_pix_stars_list[star_num].chi !=  local_pix_stars_list[star_num].chi):
        print "List mismatch!"
        sys.exit()
        
    pixel_position = star.x  +chip_adjustments_x[chip_num] , star.y + chip_adjustments_y[chip_num]
    original_sky_position = distortion_corrected_map.toworld(pixel_position)
    corrected_sky_position = (original_sky_position[0]+astrometry_correction_delta_CRVAL[0], original_sky_position[1]+astrometry_correction_delta_CRVAL[1])


#            if(1): ##pass all markers
#            if( (star.signal>50 and star.chi<1.5 and star.roundness<0.5) ): #or (star.signal>35 and star.chi<1) ): #over 12 images
    if(  star.filter_flight_sys_mag<20):
#    if(  star.chi<5 and star.sharpness>-0.5 and star.sharpness<0.5 and star.filter_flight_sys_mag<18):
        global_WCS_stars_good_lists[chip_num].append(corrected_sky_position)
    else:
        global_WCS_stars_reject_lists[chip_num].append(corrected_sky_position)
    print counter, "of", len(global_pix_stars_list),"(detector",chip_num,");"
    counter+=1

##############################################################################################
#Output region files:


def output_ds9_region_file(output_filename, list_of_FK5_tuples, colour="green"):
    region_file = open(output_filename, 'w')
    file_header="# Region file format: DS9 version 4.1"+"\n"
    file_header+="# Filename:"+"\n"
    file_header+="global color="+colour+" dashlist=8 3 width=1 font=\"helvetica 10 normal\" select=1 highlite=1 dash=0"+"\n"
    file_header+="fk5"+"\n"
    region_file.write(file_header)
    for star_WCS_coords in list_of_FK5_tuples:
        output_line = "point("+str(star_WCS_coords[0])+","+str(star_WCS_coords[1])+") # point=x" +"\n"
        region_file.write(output_line)
    pass
pass


output_filename_base = "WCS_"+list_filename.rsplit('.',1)[0]
#reject_output_filename_base = "WCS_"+list_filename.rsplit('.',1)[0]+"_fail"


all_global_WCS_stars_good_list=[]
all_global_WCS_stars_reject_list=[]

for chip_index in range(len(global_WCS_stars_good_lists)):
    chip_list=global_WCS_stars_good_lists[chip_index]
    output_ds9_region_file(output_filename_base+"_chip"+str(chip_index)+"_pass.reg", chip_list, "green")
    all_global_WCS_stars_good_list.extend(chip_list)

output_ds9_region_file(output_filename_base+"_all_pass.reg", all_global_WCS_stars_good_list, "green")

for chip_index in range(len(global_WCS_stars_reject_lists)):
    chip_list=global_WCS_stars_reject_lists[chip_index]
    output_ds9_region_file(output_filename_base+"_chip"+str(chip_index)+"_fail.reg", chip_list, "red")
    all_global_WCS_stars_reject_list.extend(chip_list)

output_ds9_region_file(output_filename_base+"_all_fail.reg", all_global_WCS_stars_reject_list, "red")


print "Output",len(all_global_WCS_stars_good_list),"selected stars"
print "Output",len(all_global_WCS_stars_reject_list),"rejected stars"

