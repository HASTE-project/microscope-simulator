"""
Simulator program to simulate a microscope by setting frequency, binning and color channel. The simulator
can be attached to a streaming framework, at the moment Apache Kafka.

The simulator is started by calling:
simulatorNoFlask.get_files(file_path, frequency, binning, color_channel, connect_kafka)
file_path: where the image files are stored period: the period time between each image. The maximum
speed allowed by the system is retrieved when setting period to 0. binning: change image's binning to decrease
message size color_channel: set which color_channels to include, there are up to five channels (1-5), they are set by
giving a list, for example ['1','3'] sets color_channels 1 and 3.
connect_kafka: set to "yes" is Kafka is used as a streaming framework.
"""

import datetime
import os
import time
import azn_filenames
import benchmarking
import cv2
import numpy as np
from skimage import img_as_uint
from skimage.measure import block_reduce
from collections import OrderedDict

from hio_stream_target import HarmonicIOStreamTarget


def get_files(image_directory_path, period, binning, color_channel_filter, send_to_target, hio_config=None,
              stream_id_tag='ll', send_matching_files=lambda file_info: True):
    """
    This function retrieves files and creates a stream of files to be used as a microscope simulator.
    :param image_directory_path: path to directory containing image test data set files
    :param period: The time period between every image (setting to 0 gives minimal time period)
    :param binning: specify the binning (reduce the number of pixels to compress the image), this is given as an
    int. Or 'None' to use the original image.
    :param color_channel_filter: filter files according to color channels to send (according to AZ convention), the channels
    are given as a list eg. ['1', '2'] (the Yokogawa microscope can have up to five color channels).
    Or 'None' to include all files.
    :param send_to_target: specify if the simulator shall stream images somewhere else with streaming framework. String, e.g. 'yes'
    :param hio_config: configuration dict for HarmonicIO integration. (see: hio_stream_target.py)
    :param stream_id_tag: string to use in stream ID
    :param send_matching_files: predicate for a file_info, return True to send the file. Sends all image files if unspecified.
    """

    benchmark_started = benchmarking.start_benchmark()

    files = os.listdir(image_directory_path)
    files = [file for file in files if not file.startswith('.')]

    stream_id = datetime.datetime.today().strftime('%Y_%m_%d__%H_%M_%S') + '_' + stream_id_tag
    print("simulator: stream ID is: " + stream_id)

    stream_target = None
    if send_to_target == 'yes':  # TODO: convert to boolean.
        # connect to stream target:
        # stream_target = KafkaStreamTarget() # TODO - pick one here. (or pass it in).
        stream_target = HarmonicIOStreamTarget(hio_config)
        # print(stream_target)
        # topic = stream_target[0]
        # producer = stream_target[1]
        print("simulator: initialized streaming target")
    else:
        print("simulator: skipping stream target initialization")
    # producer = None
    # topic = None

    files = {filename: azn_filenames.parse_azn_file_name(filename) for filename in files}

    # Exclude files which failed to parse:
    files = {filename: file_info for filename, file_info in files.items() if file_info is not None}

    files = {filename: file_info for filename, file_info in files.items() if send_matching_files(file_info)}

    # Add full path:
    for filename in files:
        files[filename]['full_path'] = os.path.join(image_directory_path, filename)

    # Filter on color channel:
    if color_channel_filter is not None:
        files = {filename: file_info for filename, file_info in files.items()
                 if file_info['color_channel'] in color_channel_filter}

    # sort the image stream to match the real microscope
    files = OrderedDict(sorted(files.items(), key=lambda file_info: (file_info[1]['time_point_number'],
                                                                     file_info[1]['well'],
                                                                     file_info[1]['imaging_point_number'],
                                                                     file_info[1]['color_channel'])))

    print("simulator: list of files to stream:")
    print(files.keys())

    # TODO: group into set of images with all colors, and send as a single message?

    benchmarking.end_benchmark('simulator_no_flask', 'prepared_to_stream', benchmark_started)

    print("now starting streaming:")

    benchmark_started_streaming = benchmarking.start_benchmark()
    for filename, file_info in files.items():
        __stream_file(filename, file_info, stream_id, stream_target, binning)
        time.sleep(period)  # TODO: we haven't allocated any time since the last image was sent ?!
    benchmarking.end_benchmark('simulator_no_flask', 'stream_all_images', benchmark_started_streaming)

    print("simulator: all files streamed")
    benchmarking.end_benchmark('simulator_no_flask', 'prepare_and_stream_all_images', benchmark_started)

    return stream_id


def __stream_file(file_name, file_info, stream_id, stream_target, binning):
    # take one file, read, and send to the streaming framework.

    # don't modify the original
    file_info = file_info.copy()

    image_bytes_tiff = __prepare_image_bytes(binning, file_info['full_path'])

    print("file: {} has size: {}".format(file_name, len(image_bytes_tiff)))

    file_info['stream_id'] = stream_id
    file_info['timestamp'] = file_info['time_point_number']  # This is the timestamp used for the document in HASTE
    file_info['location'] = (12.34, 56.78)
    file_info['substream_id'] = file_info['well']  # Use the well ID as the HASTE Substream ID

    file_info['image_length_bytes'] = len(image_bytes_tiff)
    file_info['original_filename'] = file_name
    file_info['unix_timestamp'] = time.time()

    if stream_target is not None:
        # print(topic)
        # print("prod: {} topic: {}".format(producer, topic))
        benchmark_send_image = benchmarking.start_benchmark()
        stream_target.send_message(image_bytes_tiff, file_name, file_info)
        benchmarking.end_benchmark('simulator_no_flask', 'stream_file', benchmark_send_image)


def __prepare_image_bytes(binning, file_path):
    benchmark_start_image = benchmarking.start_benchmark()

    if binning is not None:
        benchmark_binning = benchmarking.start_benchmark()

        # Read the file from disk, apply the binning, and convert back to bytes.
        # Note: this is slow, and will limit the maximum possible streaming rate.

        img = cv2.imread(file_path, -1)  # -1: Load colors as they are.
        # BB: this doesn't work with an ordinary PNG with 2 arguments in the block size.
        # BB: this seems to work on an ordinary image with 3 arguments - color channels?
        binned_img = block_reduce(img, block_size=(binning, binning), func=np.sum)

        # Convert image to bytes:
        benchmark_to_bytes = benchmarking.start_benchmark()
        ret, image_bytes_tiff = cv2.imencode('.tif', img_as_uint(binned_img))

        image_bytes_tiff = image_bytes_tiff.tobytes()
        benchmarking.end_benchmark('simulator_no_flask', 'read_image_from_disk_and_bin', benchmark_binning)
    else:
        # No binning, Just read the file from disk as bytes, and send it as-is (assume its a TIFF):
        with open(file_path, "rb") as binary_file:
            image_bytes_tiff = binary_file.read()

        benchmarking.end_benchmark('simulator_no_flask', 'read_image_from_disk_no_bin', benchmark_start_image)

    benchmarking.end_benchmark('simulator_no_flask', 'prepare_image_bytes_method', benchmark_start_image)
    return image_bytes_tiff
