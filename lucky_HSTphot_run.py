import os.path
import sys
import glob
import os

from kapteyn import wcs
import pyfits

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

output_dir = "hstphot_catalogs/"
hstphot_location="~/software/hstphot1.1/hstphot"


if len(sys.argv) != 2:
    print "Usage: hstphot_ filestem (e.g. coadd_u33)"
    sys.exit(1)
#list the coadded files
search_stem=sys.argv[1]

if(search_stem.find("coadd")==-1):
    print "should supply path to coadd files"
    sys.exit()

files= glob.glob("./"+search_stem+"*")

filename_bases=[]

for file in files:
    if (file.endswith("c0f.fits")):
        filename_bases+=[file.rsplit('.',1)[0]]

working_dir = filename_bases[0].rsplit('/',1)[0]+"/"

#look up their relative shifts

original_filenames=[]
for filename_base in filename_bases:
    original_filenames.append( filename_base.split("coadd_for_WCS_matching_",1)[-1]+".fits" )

ref_filename = original_filenames[0]

centre_pixel = (400,400)
ref_sky_loc = get_img_WCS_posn(ref_filename, centre_pixel)
ref_pix_x, ref_pix_y = centre_pixel

print "Ref file: ", ref_filename," sky loc: " , ref_sky_loc

filename_to_offset_dict={}

for filename in original_filenames:
    this_file_centre_sky_posn = get_img_WCS_posn(filename, centre_pixel)
    this_file_centre_pixel_posn_in_ref_image = get_img_pixel_posn(ref_filename, this_file_centre_sky_posn)
    this_file_pix_x, this_file_pix_y = this_file_centre_pixel_posn_in_ref_image
#    this_file_pix_offset = (this_file_pix_x-ref_pix_x, this_file_pix_y-ref_pix_y)
    this_file_pix_offset = (-1*(this_file_pix_x-ref_pix_x), -1*(this_file_pix_y-ref_pix_y))
    
#    print file_pix_offset
    filename_to_offset_dict[filename]=this_file_pix_offset


# Run HSTphot

if(os.path.isdir(output_dir)==False):
    os.makedirs(output_dir)

hstphot_command=hstphot_location
hstphot_command+=" "+output_dir+"hstphot_sourcelist_refimage_"+ original_filenames[0].rsplit('.',1)[0] +".txt" #output
hstphot_command+=" 1.0 " #per image sigma threshold
#hstphot+=" "+str(2.5*n_frames)#total sigma threshold
hstphot_command+=" 1.5"#total sigma threshold
hstphot_command+=" -1 0 0 0 0 " #chip, x/y min/max    --- all chips
#hstphot+=" 0 0 800 0 800 " #chip, x/y min/max  --- chip 0 (PC) only.
#calculate options code
opt_code = 2 + 4 + 8 #+ 2048 #(refit sky=512),(turn off ap corr=8), turn off psf_residuals = 4 , (weight_centre=2048)
#opt_code = 2 +4 + 8 + 2048 #(local background determination=2),(turn off ap corr=8), turn off psf_residuals = 4 , (more weighting on psf centre=2048)
hstphot_command+=" "+str(opt_code)+ " " #options code

command = hstphot_command + " "

for filename in original_filenames:
        offset_x, offset_y = filename_to_offset_dict[filename]
        command+= working_dir+"coadd_for_WCS_matching_"+filename.rsplit('.',1)[0]           ##strip off file extension
        command+=" "+str(offset_x)+" "+str(offset_y)+" " #dx, dy

command +="\"\"" #no reference, refer to first image listed
print command

os.system(command)

