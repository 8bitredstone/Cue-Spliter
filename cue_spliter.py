# take information from cue file 
# and use that information to seperate out each track from a single file
import sys
import os

# args:
    # folder directory Ex. C:\Users\Tim\Desktop
    # cue file Ex. artist - album.cue
# returns:
    # list of cue file titles
    # list of cue file time indices
    # artist name
    # audio file name
def read_cue(folder_directory, cue_file):
    indices, titles = [], []
    artist_name, audio_file = "", ""
    with open(folder_directory+cue_file, 'r') as file:
        for line in file:
            line = line.lstrip().rstrip()
            # check length to avoid possible index error
            if len(line) >= 5:
                # get first 5 characters of line
                prefix = line[0:5]
                '''
                TITLE
                   "CD-Text metadata; applies to the whole disc or 
                    a specific track, depending on the context"
                https://en.wikipedia.org/wiki/Cue_sheet_(computing)
                '''
                if prefix == "TITLE":
                    # remove beginning keep title without "" at start and end
                    titles.append(line[7:-1])
                '''
                INDEX
                   "Indicates an index (position) within the current FILE. 
                    The position is specified in mm:ss:ff (minute-second-frame) format. 
                    There are 75 such frames per second of audio. 
                    In the context of cue sheets, "frames" refer to CD sectors..."
                https://en.wikipedia.org/wiki/Cue_sheet_(computing)
                '''
                if prefix == "INDEX":
                    # get hours from minutes
                    hours = str(int(line[-8:-6])//60)+':'
                    if len(hours) == 2:
                        hours = '0'+hours
                    # need to make sure minutes do not exceed 60 else ffmpeg has a fit
                    minutes = str(int(line[-8:-6])%60)
                    if len(minutes) == 1:
                        minutes = '0'+minutes
                    seconds = line[-6:-3]
                    #print(line[-2:])
                    milliseconds = str(int(line[-2:])/75)
                    # millisecond calculation output 0.00000....
                    # thus need to exclude starting 0
                    # ffmpeg format HH:MM:SS.milliseconds
                    indices.append(hours+minutes+seconds+milliseconds[1:])
                
                # get album artist name
                # only grabbed once so we do not get the individual track artists
                if prefix == "PERFO" and artist_name == "":
                    artist_name = line[11:-1]
                
                # get audio file
                if prefix == "FILE " and audio_file == "":
                    remove_end = 2
                    while True:
                        if line[-remove_end] != ' ':
                            remove_end += 1
                        else:
                            remove_end += 1
                            if line[-remove_end] != '"':
                                remove_end -= 1
                            break
                    audio_file = line[6:-(remove_end)]
    return indices, titles, artist_name, audio_file

# arg: file name Ex. guy.jpg
# returns: file extension Ex. .jpg
def get_file_extension(file_name):
    # minimum file extension length is 1 character long + period, thus at least 4
    extension_length = 2
    print(file_name)
    while True:
        if file_name[-extension_length] != '.':
            extension_length += 1
        else:
            return file_name[-extension_length:]

# arg: list of strings
# returns: list of strings without (", |, /, \, :, ?, <, >, *)
def remove_invalid_characters(titles):
    # replace invalid file characters for windows
    file_names = titles.copy()
    for index in range(0, len(file_names)):
        # this method sucks but it does not really matter
        file_names[index] = file_names[index].replace('"',"'")
        file_names[index] = file_names[index].replace('|','-')
        file_names[index] = file_names[index].replace('/','-')
        file_names[index] = file_names[index].replace('\\','-')
        file_names[index] = file_names[index].replace(':','')
        file_names[index] = file_names[index].replace('?','')
        file_names[index] = file_names[index].replace('<','[')
        file_names[index] = file_names[index].replace('>',']')
        file_names[index] = file_names[index].replace('*','')
        # remove any extra trailing or leading space created
        file_names[index].lstrip().rstrip()
    return file_names

# arg: integer for number of tracks
# returns: list of number prefixes with proper amount of leading zeros Ex. ['01', '02']
def get_number_prefixes(number_of_tracks):
    number_of_digits = len(str(number_of_tracks))
    number_prefixes = []
    # add 1 because range weirdness
    for track_number in range(1, number_of_tracks+1):
        str_track_number = str(track_number)
        while True:
            if len(str_track_number) != number_of_digits:
                str_track_number = '0' + str_track_number
            else:
                break
        number_prefixes.append(str_track_number)
    return number_prefixes


def main():
    # test for expected number of args
    if len(sys.argv) != 3:
        print("Usage: "+sys.argv[0]+" <folder_directory> <cue_file>")
        return 0
    
    # accept args
    folder_directory = sys.argv[1].replace('\\','/')
    # check for convenience forward slash in folder directory
    if folder_directory[-1] != '/':
        # add convenience slash
        folder_directory = folder_directory+'/'
    cue_file = sys.argv[2]
    # check that cue file has extension
    if cue_file[-4:] != ".cue":
        # if missing add file extension before checking if real file
        cue_file = cue_file + ".cue"
    
    # check if valid folder and cue file
    try:
        os.chdir(folder_directory[0:-1])
        file = open(cue_file, 'r')
        # pointless rename, only done to see if it cannot find the file
    except:
        print("ERROR...\nInvalid Arguments")
        return 1
    else:
        file.close()
        pass

    # first returned title is the album title
    indices, titles, artist_name, audio_file = read_cue(folder_directory, cue_file)
    file_names = remove_invalid_characters(titles)
    print(audio_file)
    file_extension = get_file_extension(audio_file)
    number_of_tracks = len(indices)
    number_prefixes = get_number_prefixes(number_of_tracks)

    # check if valid audio file
    try:
        # pointless rename, only done to see if it cannot find the file
        os.rename(audio_file, audio_file)
    except:
        # prompt user for file
        audio_file = input("Cannot Locate Audio File\nEnter audio file name: ")
        try:
            os.rename(audio_file, audio_file)
        except:
            print("ERROR...\nInvalid Input")
        else:
            pass
    else:
        pass
    # make a directory to store the files in
    try: 
        os.mkdir(file_names[0])
    except:
        pass
    
    # export cover image from audio file
    os.system('ffmpeg -i "' + audio_file + # input file
          '" -an -c:v copy ' # copy video codec
          '"' + folder_directory + file_names[0] + '/' + # folder directory
          'cover.jpg' + '"') # exported cover file name
    full_cover_file_name = folder_directory + file_names[0] + '/' + 'cover.jpg'
    # check if cover exported successfully
    try:
        os.rename(full_cover_file_name, full_cover_file_name)
    except:
        FLAG_cover = False
    else:
        FLAG_cover = True
    
    # repeat command for all except last due to needing different command
    # different command is needed as the program does not know
    # the total length of the audio
    for index in range(0, number_of_tracks-1):
        start = indices[index]
        # get 1 ahead as the start of the next track is the end of the last
        end = indices[index+1]
        # all shifted over 1 due to also including album name
        track_name = titles[index+1]
        # same reason as last comment
        file_name = file_names[index+1]
        if file_extension == ".mp3":
            os.system('ffmpeg -i "' + audio_file + # input file
              '" -ss ' + start + # go to start time
              ' -to ' + end + # cut to end time
              ' -c copy' + # copy audio and video codecs
              ' -id3v2_version 3' + # include mp3 tag version
              ' -metadata title="' + track_name + '"' + # add title metadata
              ' -metadata artist="' + artist_name + '"' + # add artist name metadata
              ' -metadata album="' + titles[0] + '"' + # add album name metadata
              ' -metadata track="' + str(index+1) + '"' + # add track number metadata
              ' "' + folder_directory + file_names[0] + '/' + # folder directory
              number_prefixes[index] + ' ' + # add number prefix
              file_name + file_extension + '"') # file name and extension
        if file_extension == ".flac":
            os.system('ffmpeg -i "' + audio_file + # input file
              '" -ss ' + start + # go to start time
              ' -to ' + end + # cut to end time
              ' -metadata title="' + track_name + '"' + # add title metadata
              ' -metadata artist="' + artist_name + '"' + # add artist name metadata
              ' -metadata album="' + titles[0] + '"' + # add album name metadata
              ' -metadata track="' + str(index+1) + '"' + # add track number metadata
              ' "' + folder_directory + file_names[0] + '/' + # folder directory
              number_prefixes[index] + ' ' + # add number prefix
              file_name + file_extension + '"') # file name and extension
    # split for last song
    start = indices[number_of_tracks-1]
    track_name = titles[number_of_tracks]
    file_name = file_names[number_of_tracks]
    if file_extension == ".mp3":
        os.system('ffmpeg -i "' + audio_file + # input file
          '" -ss ' + start + # go to start time
          ' -c copy' + # copy audio and video codecs
          ' -id3v2_version 3' + # include mp3 tag version
          ' -metadata title="' + track_name + '"' + # add title metadata
          ' -metadata artist="' + artist_name + '"' + # add artist name metadata
          ' -metadata album="' + titles[0] + '"' + # add album name metadata
          ' -metadata track="' + str(number_of_tracks) + '"' + # add track number metadata
          ' "' + folder_directory + file_names[0] + '/' + # folder directory
          number_prefixes[number_of_tracks-1] + ' ' + # add number prefix
          file_name + file_extension + '"') # file name and extension
    elif file_extension == ".flac":
        os.system('ffmpeg -i "' + audio_file + # input file
          '" -ss ' + start + # go to start time
          ' -metadata title="' + track_name + '"' + # add title metadata
          ' -metadata artist="' + artist_name + '"' + # add artist name metadata
          ' -metadata album="' + titles[0] + '"' + # add album name metadata
          ' -metadata track="' + str(number_of_tracks) + '"' + # add track number metadata
          ' "' + folder_directory + file_names[0] + '/' + # folder directory
          number_prefixes[number_of_tracks-1] + ' ' + # add number prefix
          file_name + file_extension + '"') # file name and extension
    
    # if cover is not found end with no errors
    if FLAG_cover == False:
        # program ends
        return 0

    # add cover image to split files
    for index in range(0, number_of_tracks):
        # all shifted over 1 due to also including album name
        file_name = folder_directory + file_names[0] + '/' + number_prefixes[index] + ' ' + file_names[index+1] + file_extension
        file_name_temp = folder_directory + file_names[0] + '/temp ' + number_prefixes[index] + ' ' + file_names[index+1] + file_extension

        # audio files have to be renamed as ffmpeg cannot overwrite files 
        # whilst working on them
        os.rename(file_name, file_name_temp)

        # adding front cover to audio files depends on format and needs different commands
        # this program "only" support mp3 and flac
        if file_extension == ".mp3":
            os.system('ffmpeg -i "' + file_name_temp + # temp audio
                  '" -i "' + full_cover_file_name + '"' # cover art
                  ' -map 0:0 -map 1:0' + # map inputs to audio and video
                  ' -c copy' + # copy audio and video codecs
                  ' -id3v2_version 3' + # include mp3 tag version
                  ' -metadata:s:v comment="Cover (front)" ' + # set video codec to front cover
                  '"' + file_name + '"') # out as the final naming
        elif file_extension == ".flac":
            os.system('ffmpeg -i "' + file_name_temp + # temp audio
                  '" -i "' + full_cover_file_name + '"' # cover art
                  ' -map 0:0 -map 1:0' + # map inputs to audio and video
                  ' -c copy' + # copy audio and video codecs
                  ' -disposition:v attached_pic ' + # set image metadata as cover
                  ' -metadata:s:v comment="Cover (front)" ' + # set video codec to front cover
                  '"' + file_name + '"') # out as the final naming
        else:
            print("program can only add cover art to mp3 and flac")
            # change name back
            os.rename(file_name, file_name_temp)
            return 0
        # delete temporary files
        os.remove(file_name_temp)
main()