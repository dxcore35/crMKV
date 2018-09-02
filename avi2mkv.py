#!/usr/bin/env python
#
#    Copyright 2012, Jose Ignacio Galarza <igalarzab@gmail.com>.
#    This file is part of avi2mkv.
#
#    avi2mkv is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    avi2mkv is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with avi2mkv.  If not, see <http://www.gnu.org/licenses/>.

import glob
import logging
import os
import subprocess
import sys
import shutil
import tkinter
from tkinter import filedialog

from optparse import OptionParser

# Global information
__uname__ = 'all2mkv'
__long_name__ = 'Convert all movies into MKV+ add all subtitles'
__version__ = '0.1'
__author__ = 'Denis Sandor'
__email__ = 'dxcore35@gmail.com'
__url__ = 'http://x'
__license__ = 'MIT'

# Colors (ANSI)
RED = '31'
GREEN = '32'
ORANGE = '33'


def show_authors(*args, **kwargs):
    # //// Show authors

    print('%s v%s, %s' % (__uname__, __version__, __long_name__))
    print('%s <%s>' % (__author__, __email__))
    print(__license__)
    sys.exit(0)


def write_text(text, desc=sys.stdout, color=None):
    # Write the text with color, if tty

    if color is not None and desc.isatty():
        desc.write('\x1b[%sm%s\x1b[0m' % (color, text))
    else:
        desc.write(text)

    desc.flush()


def shell_arguments():
    """
    Configure optparse
    """
    usage = "usage: %prog [options] file1 file2 ..."
    parser = OptionParser(usage=usage, version="%prog " + __version__)

    # Print information
    parser.add_option(
            '-d', '--debug',
            action='store_true',
            dest='debug',
            help='be extra verbose',
            default=False
    )

    parser.add_option(
            '-a', '--authors',
            action='callback',
            callback=show_authors,
            help='show authors'
    )

    return parser


def check_mkvmerge():
    # /// Check if mkvmerge is installed

    try:
        subprocess.check_call(['mkvmerge', '-V'], stdout=subprocess.PIPE)
    except OSError:
        return False

    return True


def GetAllMovies(path):
    import os, sys

    file_paths = []
    counter = 0

    for folder, subs, files in os.walk(path):
        for filename in files:
            if not filename.startswith('.'):

                if filename.find('.mkv') is not -1:
                    file_paths.append(os.path.abspath(os.path.join(folder, filename)))
                elif filename.find('.avi') is not -1:
                    file_paths.append(os.path.abspath(os.path.join(folder, filename)))
                elif filename.find('.mp4') is not -1:
                    file_paths.append(os.path.abspath(os.path.join(folder, filename)))
                elif filename.find('.m4v') is not -1:
                    file_paths.append(os.path.abspath(os.path.join(folder, filename)))

    return file_paths


def analyze_path(path): #  CONVERT MOVIE (convert / update file format)
    

    for movies in GetAllMovies(path):
        absolute_path = movies

        if os.path.isfile(absolute_path):
            convert_video(absolute_path)

    return True


def language_short(lang): # //// Get the language code from the language name
    

    values = dict(SK='Slovak', ENG='English', DE='German',CZ='Czech')
    tmp_lng = values.get(lang.lower(), None)

    if tmp_lng is None:
        tmp_lng = values.get(lang, None)

    return tmp_lng


def language_coding(lang): # //// Get the language coding from the language short name
    
    values = dict(sk='CP1250', eng='UTF-8', de='UTF-8', cz='CP1250')
    tmp_lng = values.get(lang.lower(), None)

    if tmp_lng is None:
        tmp_lng = values.get(lang, None)

    return tmp_lng


def find_subtitles(path): # //// Find all the subtitles of the video
    

    files = glob.glob(path + '*.srt')
    languages = []

    for filename in files:
        language = filename[len(path):-4].strip().strip('.')

        if not language:
            language = 'No language element found (sufix: SK,ENG,CZ...) so setting english as default language.'
            languages.append([language_short("ENG"), "ENG", filename])
        else:  
            languages.append([language_short(language), language, filename])
        
        logging.info("Found a subtitle with the name '%s'", language)

    return languages


def create_command(input_filename, output_filename, subtitles, type): # //// Create the mkvmerge command

    command = ['mkvmerge']
    command.append('-o')               # Append the output file
    command.append(output_filename)
    command.append(input_filename)     # Append the input file

    # ////  Handle all subtitles
    for subtitle in subtitles:
        command.append('--language')
        command.append('0:%s' % subtitle[0])
        command.append('--sub-charset')
        command.append('0:%s' % language_coding(subtitle[1]))
        command.append('--track-name')
        command.append('0:%s' % subtitle[1])
        command.append(subtitle[2])

    logging.info(command)
    return command


def convert_video(path): #  Update the found videos to matroska if there are subtitles

    REMOVE_INPUT = False                                                           # REMOVE INPUT FILE

    main_dir = os.path.dirname(path) + "/"
    converted_dir = main_dir + "converted/"     # DEFAULT OUTPUT DIRECTORY FOR OK MKVs
    withoutsub_dir = main_dir + "no_subtitles/"
    error_dir = main_dir + "wrong_formatting/"

    if not os.path.exists(converted_dir):
        os.makedirs(converted_dir)

    logging.info("Trying to update / convert %s", path)
    path_without_ext = os.path.splitext(path)[0]
    file_name = os.path.basename(path_without_ext)
    output_filename = converted_dir + file_name + '_.mkv'
    subs = find_subtitles(path_without_ext)

    write_text('[SUB]:' + str(subs) + '\n', sys.stdout, ORANGE)

    if len(subs) is not 0:

        command = create_command(path, output_filename, subs, 'update')
        c = subprocess.call(command, stdout=subprocess.PIPE)

        if c == 0:
            write_text('[DONE]:' + file_name + '\n', sys.stdout, GREEN)
            if not os.path.dirname(path_without_ext) == main_dir:
                shutil.rmtree(os.path.dirname(path_without_ext))

        else:
            write_text('[ERRR]:' + file_name + '\n', sys.stdout, RED)
            
            if not os.path.exists(error_dir):
                os.makedirs(error_dir)
    else:

        command = create_command(path, output_filename, subs, 'update')
        c = subprocess.call(command, stdout=subprocess.PIPE)
        write_text('[SKIP]:' + file_name+ '\n', sys.stdout, ORANGE)

        if not os.path.exists(withoutsub_dir):
            os.makedirs(withoutsub_dir)

        #shutil.move(os.path.dirname(path_without_ext), withoutsub_dir)

    return c == 0


def main(): #  Entry point

    arg_parser = shell_arguments()
    (options, paths) = arg_parser.parse_args()

    if not paths:
        root = tkinter.Tk()
        root.withdraw()
        path = filedialog.askdirectory(parent=root,initialdir="/",title='Please select a directory')

    # Configure the logging module
    if options.debug:
        level = logging.INFO
    else:
        level = logging.WARNING

    logging.basicConfig(
            level=level,
            format='%(asctime)s %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
    )

    if not check_mkvmerge():
        print('mkvtoolnix is not installed in your system')
        print('You need the mkvmerge command to run this script')
        sys.exit(-1)

    #for path in paths:
    logging.info('Looking for all the avi/mp4/mkv files in %s', path)
    analyze_path(path)

if __name__ == '__main__':
    main()

# vim: ai ts=4 sts=4 et sw=4
