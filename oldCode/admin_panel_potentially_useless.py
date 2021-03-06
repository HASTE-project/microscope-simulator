@app.route("/adminPanel")
def admin():
    return render_template("admin_panel.html")


# start a new test run and save score
# use timeit
# files = os.listdir(file_path)
# output: 1. text file with freq info 2. graphs showing performance

def admin_fun():
    #test max freq - kolla hur lång tid varje steg i for-loopen tar
    #test if set freq corresponds to actual freq
    #test freq for different image sizes

    # input: JSON file with test settings (possible to make multiple runs at once)
    json_file = request.form["file_path"]
    json_file = open(json_file, "r")
    run_information = json_file.read()
    run_information = json.loads(run_information)

    return run_information


@app.route("/adminPanel", methods=['POST'])


def test_timeit():
    runs = int(request.form["runs"])

    setup_template = '''
from simulator import admin_fun, get_files
run_information = admin_fun() 
frequency = run_information['run']['frequency']
color_channel = run_information['run']['color_channel']
binning = run_information['run']['binning']
file_path = run_information['run']['file_path']
connect_kafka = run_information['run']['connect_kafka']   
    '''

    for run in range(1, runs+1):
        setup = setup_template.replace("'run'", "'run{}'".format(run))
        save_results(str(timeit.timeit('get_files(file_path, frequency, binning, color_channel, connect_kafka)',
                                       setup=setup, number=3)), run)

    run_information = admin_fun()
    print(len(run_information))
    for run in run_information:
        frequency = run_information[run]['frequency']
        color_channel = run_information[run]['color_channel']
        binning = run_information[run]['binning']
        file_path = run_information[run]['file_path']
        connect_kafka = run_information[run]['connect_kafka']
        time_get_files(file_path, frequency, binning, color_channel, connect_kafka)
    return "test ready"


def save_results(results, run):
    fo = open("result.txt", "a")
    fo.write("Run nr, result: {} ".format(run))
    fo.write(results)
    fo.write("\n")
    fo.close()


# def get_files(file_path, period, binning, color_channel, connect_kafka):
#     print('in get_files')
#     for root, dirs, files in os.walk(file_path):
#         print('in for')
#         if not files:
#             print('in if')
#         #           pass
#         else:
#             if not dirs:
#                 print('if not dirs')
#             #		pass
#             for i in range(len(files)):
#                 #		print('2 for loop')
#
#                 simulatorNoFlask.get_file(files, color_channel, file_path, binning, connect_kafka)
#
#                 get_file(files, i, color_channel, file_path, binning, connect_kafka)
#                 #                simulatorNoFlask.get_file(files, color_channel, file_path, binning, connect_kafka)
#
#                 time.sleep(period)
#
#
# def get_file(files, i, color_channel, file_path, binning, connect_kafka):
#     print('in get_file')
#     if files[i][-5] in color_channel:
#         print('in color_channel')
#         img = cv2.imread(file_path + files[i], -1)
#         binned_img = block_reduce(img, block_size=(binning, binning), func=np.sum)
#         if connect_kafka == "yes":
#             print('in connect_kafka')
#             ret, jpeg = cv2.imencode('.png', img_as_ubyte(binned_img))
#             kafka_producer.connect(jpeg.tobytes())


# def time_get_files(file_path, period, binning, color_channel, connect_kafka):
#     result = []
#     for root, dirs, files in os.walk(file_path):
#         if not files:
#             pass
#         else:
#             if not dirs:
#                 pass
#             if period == 0:
#                 for i in range(len(files)):
#                     start = time.clock()
#                     if files[i][-5] in color_channel:
#                         img = cv2.imread(file_path + files[i], -1)
#                         binned_img = block_reduce(img, block_size=(binning, binning), func=np.sum)
#                         if connect_kafka == "yes":
#                             ret, jpeg = cv2.imencode('.png', img_as_ubyte(binned_img))
#                             kafka_producer.connect(jpeg.tobytes())
#                     stop = time.clock()
#                     result.append(stop - start)
#             else:
#                 for i in range(len(files)):
#                     start = time.clock()
#                     if files[i][-5] in color_channel:
#                         img = cv2.imread(file_path + files[i], -1)
#                         binned_img = block_reduce(img, block_size=(binning, binning), func=np.sum)
#                         if connect_kafka == "yes":
#                             ret, jpeg = cv2.imencode('.png', img_as_ubyte(binned_img))
#                             kafka_producer.connect(jpeg.tobytes())
#                     time.sleep(period)
#                     stop = time.clock()
#                     result.append(stop - start)
#             print(result)