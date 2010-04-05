#!/usr/bin/env python
'''
Created on Mar 16, 2010

@author: bballantine
'''
import os, shutil
import __init__ as common


def write_sequence(ftable, dir, cams):
    for cam in cams:
        common.create_dir(os.path.join(dir, cam))
    file = open(os.path.join(dir, "ftable.txt"), 'w')
    for row in ftable:
        i = 0
        for item in row:
            file.write("/".join(item.filename().split("/")[-3:]) + " ")
            interimdir = os.path.join(dir, cams[i], item.filename().split("/")[-2])
            # create_dir makes sure we don't create it if already created
            common.create_dir(interimdir)
            shutil.copy(item.filename(), interimdir)
            i += 1
        file.write("\n")
    file.close()

if __name__ == '__main__':
    """
        - simplest example on how to call:
            ./sequence.py -b ~/work/darpa/data/finaltest01/out/ -d ~/tmp/seqout01 
                    -s 8486A360_2010_03_04-16:04:31.556.jpg -i 10
        
        NOTE:
            -s value must be a "keyframe" image, which is in the first dir listed 
                by common.list_cams.. which is currently the West image in 8486A360
            -i is the count of images in the sequence to write
    """
    parser = common.get_opts()
    opts,args=parser.parse_args()
    cams = common.list_cams(common.CAMS)
    ftable = common.create_frametable(opts.base, cams,
                                      opts.start_file, opts.image_count)
    common.create_dir(opts.dest)
    write_sequence(ftable, opts.dest, cams)