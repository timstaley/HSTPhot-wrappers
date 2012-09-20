import sys
import glob
import os

from shutil import copyfile

from kapteyn import wcs
import pyfits

#repeat_run=False

def get_img_hdr_filter_string(fits_filename):
    temp_hdulist = pyfits.open(fits_filename)
    temp_header = temp_hdulist[0].header
    return temp_header["FILTNAM1"]
pass

def get_img_WCS_map(fits_filename):
    hdulist = pyfits.open(fits_filename)
    header = hdulist[0].header
    proj = wcs.Projection(header)
    return proj.sub(nsub=2)
pass

def get_img_WCS_posn(fits_filename, pixel_tuple):
    wcs_map = get_img_WCS_map(fits_filename)
    sky_loc = wcs_map.toworld(pixel_tuple)
    return sky_loc
pass

def get_img_pixel_posn(fits_filename, sky_tuple):
    map=get_img_WCS_map(fits_filename)
    pix_loc = map.topixel( sky_tuple )
    return pix_loc
pass



#################################################################

hst_mask_location="~/software/hstphot1.1/mask"
hst_calcsky="~/software/dolphot/dolphot1.1/calcsky"
hst_getsky="~/software/dolphot/hstphot1.1/getsky"
hst_crmask_location="~/software/hstphot1.1/crmask"
hst_coadd_location="~/software/hstphot1.1/coadd"
hst_hotpix_location="~/software/hstphot1.1/hotpixels"

if len(sys.argv) != 2:
    print "Usage: prep_files filestem (e.g. u33)"
    sys.exit(1)
##########################################
# List the relevant files. Build a list of the filestems which represent the *_c0f.fits / *_c1f.fits pairs
search_stem=sys.argv[1]
files= glob.glob("./"+search_stem+"*")
original_filestems=[]

for file in files:
    if (file.endswith("c0f.fits")):
        original_filestems+=[file.rsplit('_',1)[0].strip('./')]

original_filestems.sort()

##########################################
# Determine the pixel shift offsets between the exposures
print "Found ", len(original_filestems),"file pairs:"
print original_filestems
print "proceeding to sort into pointings"
print "...\n"


ref_filename = original_filestems[0]+"_c0f.fits"

centre_pixel = (400,400)
ref_sky_loc = get_img_WCS_posn(ref_filename, centre_pixel)

ref_pix_x, ref_pix_y = centre_pixel

print "Ref file: ", ref_filename," sky loc: " , ref_sky_loc

offset_dict={}


for filestem in original_filestems:
    this_file_centre_sky_posn = get_img_WCS_posn(filestem +"_c0f.fits", centre_pixel)
    this_file_centre_pixel_posn_in_ref_image = get_img_pixel_posn(ref_filename, this_file_centre_sky_posn)
    this_file_pix_x, this_file_pix_y = this_file_centre_pixel_posn_in_ref_image
#    this_file_pix_offset = (this_file_pix_x-ref_pix_x, this_file_pix_y-ref_pix_y)
    this_file_pix_offset = (-1*(this_file_pix_x-ref_pix_x), -1*(this_file_pix_y-ref_pix_y))
#    print file_pix_offset

    if( (this_file_pix_offset in offset_dict) == False):
        offset_dict[this_file_pix_offset]=[filestem]
    else:
        offset_dict[this_file_pix_offset].append(filestem)
    

print "Found ", len(offset_dict.keys()),"offsets, grouping is:"
for offset in offset_dict.keys():
    print "Offset: ", offset
    relevant_filestems = offset_dict[offset]
    for filestem in relevant_filestems:
        print filestem, "(",get_img_hdr_filter_string(filestem+"_c0f.fits"),")"

    print "   "

large_offsets_bail = False
for offset in offset_dict.keys():
    if(abs(offset[0])>1000 or abs(offset[1])>1000):
        print "Encountered a large offset:", offset, "(",offset_dict[offset],"), will exit "
        large_offsets_bail=True

if(large_offsets_bail):
    sys.exit()


##########################################
# Determine filters present
filters={}
for filestem in original_filestems:
    filter_string = get_img_hdr_filter_string(filestem+"_c0f.fits")
    if(filter_string not in filters):
        filters[filter_string]=1
    else:
        filters[filter_string]+=1

print "Filters present, with frame counts:"
for key, value in filters.iteritems():
    print "Filter:\"" , key, "\"  -count:",value

##########################################
# Copy the files to a directory before we do anything to them, so we can still access the original files with WCS information intact

print "Making a copy of the files..."
working_dir_name = "hstphot_working_files/"
if(os.path.isdir(working_dir_name)==False):
    os.makedirs(working_dir_name)
working_dir_filestems=[]
for filestem in original_filestems:
    copyfile(filestem+"_c0f.fits", working_dir_name+filestem+"_c0f.fits")
    copyfile(filestem+"_c1f.fits", working_dir_name+filestem+"_c1f.fits")
    working_dir_filestems.append( working_dir_name+filestem)

##########################################
# Run mask on the file pairs in the working directory

for filestem in working_dir_filestems:
    print "Masking",filestem
    command=hst_mask_location + " " +filestem+"_c0f.fits "+filestem+"_c1f.fits "
    print command
    os.system(command)
print "\n======================================\n"
##########################################
#Delete the .old files mask leaves lying around, since we already made a backup
for filestem in working_dir_filestems:
    os.remove(filestem+"_c0f.fits.old")


##########################################
#Run getsky (calcsky)
print "Running calcsky on raw images for use by crmask"

calcsky_counter=1
for filestem in working_dir_filestems:
    print "Running getsky on ", filestem,"(file ", calcsky_counter,"of", len(working_dir_filestems),")"
    calcsky_counter+=1
#    command=hst_calcsky + " " +filestem+"_c0f" + " 15 35 8 -2 2" #inner/outer radius, stepsize, sigma low/high
    command=hst_getsky + " " +filestem+"_c0f" 
    print command
    os.system(command)

#    command = "FITS_decapitate " +filestem+"_c0f"+".sky.fits " + filestem+"_c0f"+".sky" #switch to getsky format
#    print command
#    os.system(command)
#    print " "
print "\n======================================\n"
##########################################
# Run CRmask on each filter dataset, complete with offsets:
hst_crmask_command=hst_crmask_location+" 1" #reg factor
hst_crmask_command+=" 3.0" #sigma threshold
hst_crmask_command+=" 0" #use min value

command=hst_crmask_command + " "

offset_counter=1
for current_working_filter in filters.keys():
    for offset in offset_dict.keys():
        print "Listing files for crmask matching offset number ", offset_counter, "of", len(offset_dict.keys())
        offset_counter+=1
        offset_x, offset_y=offset
        relevant_filestems = offset_dict[offset]
        for filestem in relevant_filestems:
            if (get_img_hdr_filter_string(working_dir_name+filestem+"_c0f.fits") == current_working_filter):
                command+= working_dir_name+filestem+"_c0f" + " 0 0 0 " #scale minscale maxscale (all=0 for single colour dataset)
                command+= str(offset_x)+" " +str(offset_y) +" "#dx, dy

    print "Running crmask for filter:",current_working_filter
    print command
    print "*** Run 1 ***"
    os.system(command)
    print "*** Run 2 ***"
    os.system(command)
    print "*** Run 3 ***"
    os.system(command)

print "\n======================================\n"

##########################################
#Run coadd

coadded_pointings=[]
offset_counter=1
for current_working_filter in filters.keys():
    for offset in offset_dict.keys():
        print "Running coadd for offset", offset_counter, "of", len(offset_dict.keys())
        offset_counter+=1
        command = hst_coadd_location+" "
        relevant_filestems = offset_dict[offset]
        n_files_matching_filter_and_offset=0

        for filestem in relevant_filestems:
            if (get_img_hdr_filter_string(working_dir_name+filestem+"_c0f.fits") == current_working_filter):
                command+= working_dir_name+filestem+"_c0f.fits" + " " #populate_file_list
                n_files_matching_filter_and_offset+=1

        coadd_output_filename = working_dir_name+"coadd_for_WCS_matching_"+relevant_filestems[0]+"_c0f.fits " #encode the first filename so we know where to look up the WCS
        command+= coadd_output_filename
        if(n_files_matching_filter_and_offset>0):
            coadded_pointings.append(coadd_output_filename);
            print "Running coadd for offset:",offset," and filter:", current_working_filter
            print command
            os.system(command)
            print " ---------------- "


print "Created", len(coadded_pointings), "coadded images"
print "\n======================================\n"

##########################################
#Run calcsky again on the coadds
print "Running calcsky on", len(coadded_pointings), "coadded images\n...\n"
calcsky_counter=1
for coadd_file in coadded_pointings:
    print "Running calcsky on ", coadd_file ,"(file ", calcsky_counter,"of", len(coadded_pointings),")"
    calcsky_counter+=1
    filename_base = coadd_file.rsplit(".fits",1)[0]
#    command=hst_calcsky + " " +filename_base + " 15 35 8 -2 2" #inner/outer radius, stepsize, sigma low/high
    command=hst_getsky + " " +filename_base 
    print command
    os.system(command)

#    command = "FITS_decapitate " +filename_base+".sky.fits " + filename_base+".sky" #switch to getsky format
#    os.system(command)

print "\n======================================\n"

##########################################
#Run hotpix
print "Running hotpix on", len(coadded_pointings), "coadded images\n...\n"
for coadd_file in coadded_pointings:
    print "Running hotpix on ", coadd_file
    command=hst_hotpix_location + " " +coadd_file.rsplit(".fits",1)[0];
    print command
    os.system(command)
    os.system(command) #running twice is recommended

print "\n======================================\n"
