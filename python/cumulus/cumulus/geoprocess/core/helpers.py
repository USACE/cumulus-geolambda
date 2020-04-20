import hashlib
import logging
import math

# Helper Function for buffering bounding envelope
def buffered_extent(extent, cells, cell_size):

    def round_down(value):
        return (math.floor(value/cell_size) - cells)*cell_size

    def round_up(value):
        return (math.ceil(value/cell_size) + cells)*cell_size


    if cell_size == 0 or cells == 0:
        logging.warning('cell_size 0 or cells 0; no buffer applied')
        return extent

    return (round_down(extent[0]), round_down(extent[1]), round_up(extent[2]), round_up(extent[3]))

