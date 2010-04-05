#!/usr/bin/env python
'''
Created on Mar 15, 2010

@author: bballantine
'''
import sys, os, re
import Image, ImageDraw, ImageFont
import __init__ as common

def write_images(ftable, dir, size, num_cams, fontpath, startframe=0):
    """
    Get images in ftable and write to dir.
    
    Arguments:
    ftable     -- table of frameImages in form [[fi, fi, ..], [fi, fi, ..], ..]
                    where fi is a common.FrameImage object and
                    the inner lists are the the length of the number of cameras and
                    ftable's length is the number of frames
    dir        -- Where to store the composite images
    size       -- WxH size of images
    num_cams   -- Number of cameras used
    fontpath   -- Path to a font to use to write image name to composite
    startframe -- Index of frame to start with, defaults to 0
    """
    # after pasting images into container
    # we will cut everything in half
    horiz_padding = 20
    vert_padding = 50
    row_size = 3
    # calculate
    width,height = map(int, size.split('x'))
    num_rows = num_cams / row_size
    if (num_cams % row_size > 0): num_rows += 1
    width = width + horiz_padding
    height = height + vert_padding
    # calculate container width (don't want horiz-padding on far right)
    container_width = (row_size * width) - horiz_padding
    container_height = num_rows * height
    # load the font for later use
    font = get_font(fontpath)
    # now go through each row in frame table, creating composite 
    n = 0 # count of composite frames
    for frame in ftable:
        frame_imgs = []
        if (n < startframe):
            n+=1
            continue
        # create ImageS out of them and store in frame_imgs
        for frame_image in frame:
            try:
                frame_imgs.append(Image.open(frame_image.filename()))
            except IOError:
                sys.stdout.write("whoops")
        # create the container based on frame imgs mode
        container_img = Image.new(
                frame_imgs[0].mode, (container_width, container_height))
        # now paste the frame images into the container
        r = c = 0
        for img in frame_imgs:
            if (c == row_size):
                r += 1
                c = 0
            try:
                #lil hack
                if (r == 1 and c == 1):
                    c+=1
                container_img.paste(img, (c * width, r * height))
            except IOError:
                sys.stdout.write("little trouble, moving on-")
            sys.stdout.flush()
            c += 1     
        container_img.save(os.path.join(dir, "img_%0.5d.jpg") % n)
        # almost there.  now cut size in half to make it previewable
        container_img = container_img.resize((container_width/2, container_height/2))
        # finally, write the file name under each of the images
        # so we can easily find the images we care about
        # we do this after the resize so as not to distort the text
        draw = ImageDraw.Draw(container_img)
        w = width / 2
        h = height / 2
        r = c = 0
        for frame_image in frame:
            if (c == row_size):
                r += 1
                c = 0
            text = "/".join(frame_image.filename().split("/")[-2:])
            #lil hack
            if (r == 1 and c == 1):
                c+=1
            draw.text(((c * w), (r * h) + h - (vert_padding/2)), text, font=font, fill="pink")
            c+=1
        # fyew! write it out
        container_img.save(os.path.join(dir, "img_%0.5d.jpg") % n)
        sys.stdout.write(str(n) + "-")
        sys.stdout.flush()
        n+=1


def get_font(fontpath):
    """Helper to find and return specified or default ImageFont."""
    if (fontpath):
        print "Found Font!"
        return ImageFont.truetype(fontpath, 14)
    else:
        return ImageFont.load_default()

def order_for_composite(cams):
    """ 
    Order cameras for rendering, returns list. 
    Order: NW, N, NE, W, E, SE, S, SW 
    """
    return list(cams[c] for c in\
                ['NW', 'N', 'NE', 'W', 'E', 'SE', 'S', 'SW'])

def get_more_opts(parser):
    """ Gets options specific to this module """
    parser.add_option("-S", "--size", default="960x720")
    parser.add_option("-F", "--font", 
                      help="Path to a font to use")
    parser.add_option("-N", "--start_frame_n",
                      help="start generating at frame N", 
                      type="int", default=0)
    sizere = re.compile(r'^([0-9]{2,4})x([0-9]{2,4})$')
    opts,args=parser.parse_args()
    if not sizere.match( opts.size ):
        parser.error("Invalid format for size.  Use WIDTHxHEIGHT" )
    return opts,args 

if __name__ == '__main__':
    """
    Create a series of composite image frames.
    - simplest example on how to call:
        ./composite.py -b ~/work/darpa/data/finaltest01/out/ -F FreeMonoBold.ttf -d ~/tmp/finalout01
    """
    parser = common.get_opts()
    opts, args = get_more_opts(parser)
    cams = order_for_composite(common.CAMS)
    ftable = common.create_frametable(opts.base, cams,
                                          opts.start_file, opts.image_count)
    common.create_dir(opts.dest)
    write_images(ftable, opts.dest, opts.size, 
                 len(cams), opts.font, opts.start_frame_n) 


