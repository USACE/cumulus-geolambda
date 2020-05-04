import hashlib
import json
import logging
import shutil


def checksum(file, algorithm='SHA256', size=1000000):
    """Generate a checksum/hash for a given file.
    filename
        Location of file to hash
    block_size
        Number of bytes to read at a time. Default: 1000000 (1MB)

    https://stackoverflow.com/questions/2229298/python-md5-not-matching-md5-in-terminal
    https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
    """
    supported_algorithms = {
        'SHA256': hashlib.sha256(),
        'MD5': hashlib.md5()
    }

    try:
        checksum = supported_algorithms[algorithm.upper()]
    except:
        logging.error('Checksum algorithm not supported: {}'.format(algorithm))
        return None

    with open(file, 'rb') as f:
        while True:
            data = f.read(size)
            if len(data) == 0:
                break
            checksum.update(data)

    return checksum.hexdigest()


import errno
import gzip
import os


def gunzip_file(infile, outfile):

    with gzip.open(infile, 'rb') as f:
        content = f.read()
        with open(outfile, 'wb') as out:
            out.write(content)


def gzip_file(infile, outfile):

    with open(infile, 'rb') as f_in:
        with gzip.open(outfile, 'wb') as f_out:
            shutil.copyfileobj(f_in, f_out)
    
    return os.path.abspath(outfile)


def delete_files_by_extension(directory, extensions):
    """
    Uses split() instead of os.path.splitext() to cover extensions
    that include more than one '.', such as '.tar.gz'.
    """

    for f in os.listdir(directory):
        if f.split(os.extsep, 1)[1] in extensions:
            os.remove(
                os.path.join(directory, f)
            )


def change_file_extension(infile, extension):
    """Replace file extension starting from leftmost '.' with provided <extension>
    Note: provided <extension> should not include leading '.'

    Method uses split() instead of os.path.splitext() to handle extensions
    that include more than one '.', such as '.tar.gz'.
    """

    return '.'.join([
        os.path.basename(infile).split(os.extsep, 1)[0],
        extension
    ])


def mkdir_p(path):
    '''Simulate mkdir_p.
    http://stackoverflow.com/questions/600268/mkdir-p-functionality-in-python
    '''
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST:
            pass
        else:
            raise


def write_json_to_file(dct, file):
    """Writes a dictionary to compact JSON in a file"""

    # Write JSON Statistics to a file
    _abspath = os.path.abspath(file)
    with open(_abspath, 'w') as outfile:
        outfile.write(json.dumps(dct, separators=(",", ":")))

    return _abspath
