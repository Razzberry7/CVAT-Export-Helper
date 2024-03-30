### The CVAT-Export-Helper creates a series of folders and sub-folders
### in order to match the organization of exported YOLO data from Roboflow.

## This is the format:
## > Main-Folder/
##     > [train/valid/test]/
##          > images/
##          > labels/
##     > data.yaml

# USAGE: python ./CVAT-Export-Helper.py


import sys
import os
import shutil
from tkinter import *
from tkinter import filedialog
from tkinter.ttk import *
from tkinter.messagebox import showinfo
from zipfile import ZipFile
from paramiko import SSHClient
from scp import SCPClient
from PIL import ImageTk, Image
import json
import math
from scipy.spatial import ConvexHull
import numpy as np

import util.config_parser as config_parser
import util.dataset_splitter as dataset_splitter

# Things needed for building with Pyinstaller
building = False
if building:
    path_prefix = "_internal/"
else:
    path_prefix = ""

# Parse config2 json file
conf = config_parser.Config.load_json(f'{path_prefix}config/config2.json')

# Function for opening the file explorer window
def browse_files():
    global file_path
    filename = filedialog.askopenfilename(initialdir=conf.browse_default_path,
                                          title="Select a File",
                                          filetypes=(("Zip files",
                                                      "*.zip*"),
                                                     ("all files",
                                                      "*.*")))
    file_path = filename
    # Change label contents
    file_explorer_label.configure(text="File Opened: " + filename)
    conf.browse_default_path = os.path.dirname(file_path)


# Function for zipping a folder
def zip_folder(path, zipf):
    for dirname, subdirs, files in os.walk(path):
        for filename in files:
            zipf.write(os.path.join(dirname, filename),
                       os.path.relpath(os.path.join(dirname, filename),
                                       os.path.join(path, '..')))


# Function creating aforementioned structure
def export_helper(path, per_train, per_valid, per_test, seed, data_path, class_setting):
        conf.datasets.percent_train = per_train
        conf.datasets.percent_valid = per_valid
        conf.datasets.percent_test = per_test
        conf.datasets.seed = seed
        conf.datasets.data_path = data_path
        conf.datasets.classes = class_setting

    # try:
        if path != "":
            path_origin = os.path.dirname(path) + "/"
            filename = os.path.basename(path[:-4])

            print(path_origin)
            print(filename)

            # Making first folder if it doesn't exist
            dir_path = path_origin + filename
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.mkdir(dir_path)
            else:
                os.mkdir(dir_path)

            # Making dataset folder if it doesn't exist
            #            dir_path = path_origin + filename + "/" + folder_settings_var.get()
            dir_path = path_origin + filename + "/train"
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.mkdir(dir_path)
            else:
                os.mkdir(dir_path)

            # Making images folder if it doesn't exist
            #            images_path = path_origin + filename + "/" + folder_settings_var.get() + "/images"
            images_path = path_origin + filename + "/train/images"
            if os.path.exists(images_path):
                shutil.rmtree(images_path)
                os.mkdir(images_path)
            else:
                os.mkdir(images_path)

            # Making labels folder if it doesn't exist
            #            labels_path = path_origin + filename + "/" + folder_settings_var.get() + "/labels"
            labels_path = path_origin + filename + "/train/labels"
            if os.path.exists(labels_path):
                shutil.rmtree(labels_path)
                os.mkdir(labels_path)
            else:
                os.mkdir(labels_path)

            # Create a data.yaml file
            dir_path = path_origin + filename + "/"
            with open(dir_path + '/data.yaml', 'w') as f:
                print(f'train: {data_path}{filename}/train/images', file=f)
                print(f'val: {data_path}{filename}/valid/images', file=f)
                print(f'test: {data_path}{filename}/test/images', file=f)
                print('', file=f)
                print('nc: ' + str(len(conf.classes[class_setting])), file=f)
                print("names: " + str(conf.classes[class_setting]), file=f)

            with ZipFile(path, 'r') as zip:
                for file in zip.namelist():
                    print(file)
                    if 'obj_train_data' in file and (file.endswith((".jpg", ".jpeg", ".JPG", ".JPEG", ".png", ".PNG"))):
                        zip.extract(file, images_path)
                    if 'obj_train_data' in file and file.endswith(".txt"):
                        zip.extract(file, labels_path)

            for file in os.listdir(images_path + "/obj_train_data"):
                shutil.move(os.path.join(images_path + "/obj_train_data", file), images_path)
            shutil.rmtree(images_path + "/obj_train_data")

            for file in os.listdir(labels_path + "/obj_train_data"):
                shutil.move(os.path.join(labels_path + "/obj_train_data", file), labels_path)
            shutil.rmtree(labels_path + "/obj_train_data")

            dataset_splitter.assign(path_to_project=path_origin+filename,
                                    dataset_folder="train",
                                    per_train=per_train,
                                    per_valid=per_valid,
                                    per_test=per_test,
                                    seed=seed)

            zf = ZipFile(path_origin + filename + ".zip", "w")
            zip_folder(path_origin + filename, zf)
            zf.close()
    # except:
    #     popup_show_error("ERROR CONVERTING FILE", "Are you sure you choose the correct zip file from CVAT?")
    #     print("ERROR: Something went wrong when trying to convert the CVAT file. "
    #           "Are you sure you choose the correct zip file from CVAT?")


# Function for SCP-ing a zip file to Lambda
def SCP_to_Lambda(file_path, export_path, username, password):
    try:
        if file_path and export_path and username and password != "":
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(hostname='lambda04.rowan.edu', port=22, username=username, password=password)

            with SCPClient(ssh.get_transport()) as scp:
                scp.put(file_path, export_path)
    except:
        popup_show_error("ERROR CONNECTING TO LAMBDA", "Are you sure you're connected to the Rowan VPN?")
        print("Something went wrong when trying to SCP onto Lambda. "
              "Are you sure you're connected to the Rowan VPN?")


# Updates the config and then closes the program
def save_and_close():
    global theme

    # Update theme in our config dictionary
    # conf.appearance.current_theme = theme
    # if scp_settings_path_tb.get() != "":
    #     conf.lambda_server.destination_path = scp_settings_path_tb.get()
    # if scp_settings_username_tb.get() != "":
    #     conf.lambda_server.username = scp_settings_username_tb.get()

    # Save any changed config values in our dictionary
    with open(f"{path_prefix}config/config2.json", 'w') as outfile:
        json.dump(conf, outfile, indent=4)

    # Close applicationw
    sys.exit()


# Configures the styles used in the program based on the theme values in the config file
def update_color(new_theme):
    global theme
    theme = new_theme

    # Change the color values based on the config file & theme passed in as a parameter
    main_bg = '#%02x%02x%02x' % (conf.appearance.themes[theme].main_bg[0],
                                 conf.appearance.themes[theme].main_bg[1],
                                 conf.appearance.themes[theme].main_bg[2])
    text_color = '#%02x%02x%02x' % (conf.appearance.themes[theme].text[0],
                                    conf.appearance.themes[theme].text[1],
                                    conf.appearance.themes[theme].text[2])
    settings_color = '#%02x%02x%02x' % (conf.appearance.themes[theme].settings_bg[0],
                                        conf.appearance.themes[theme].settings_bg[1],
                                        conf.appearance.themes[theme].settings_bg[2])
    error_color = '#%02x%02x%02x' % (255, 0, 0)

    # NOTE: prefix.T_____ is important, you can use any prefix though
    style.configure('main.TLabel', background=main_bg, foreground=text_color)
    style.configure('main.TFrame', background=main_bg)
    style.configure('settings.TLabel', background=settings_color, foreground=text_color)
    style.configure('settings.TFrame', background=settings_color)
    style.configure('color.TButton', background=main_bg, foreground=text_color)
    style.configure('color.TRadiobutton', background=settings_color, foreground=text_color)
    style.configure('color.TEntry', fieldbackground=main_bg, foreground=text_color)
    style.configure('color.TMenubutton', background=main_bg, foreground=text_color)
    style.configure('error.TLabel', background=settings_color, foreground=error_color)


# Work in progress for animating things
def animation(imageObject, frames, gif_Label, count):
    global showAnimation
    speed = 15
    new_image = imageObject[count]
    gif_Label.configure(image=new_image)

    count += 1
    if count == frames:
        count = 0

    showAnimation = tk_root.after(speed, lambda: animation(imageObject, frames, image_window, count))


# Popup message for errors
def popup_show_error(error_type, error_message):
    showinfo(error_type, error_message)


# Popup menu for exporting
def popup_export_helper(file_path):
    # Inner method for checking the percentages add up to 100
    def check_percentages():
        if int(eh_train_percent_tb.get()) + int(eh_valid_percent_tb.get()) + int(eh_test_percent_tb.get()) == 100:
            return True
        else:
            return False

    # Inner method for checking if the submission is valid, saving the config file, and running the export helper
    def submit():
        if check_percentages():
            if eh_train_percent_tb.get() != "":
                conf.datasets.percent_train = int(eh_train_percent_tb.get())
            if eh_valid_percent_tb.get() != "":
                conf.datasets.percent_valid = int(eh_valid_percent_tb.get())
            if eh_test_percent_tb.get() != "":
                conf.datasets.percent_test = int(eh_test_percent_tb.get())

            # Save any changed config values in our dictionary
            with open(f"{path_prefix}config/config2.json", 'w') as outfile:
                json.dump(conf, outfile, indent=4)

            export_helper(file_path,
                          int(eh_train_percent_tb.get()),
                          int(eh_valid_percent_tb.get()),
                          int(eh_test_percent_tb.get()),
                          eh_seed_tb.get(),
                          eh_data_path_tb.get(),
                          eh_class_settings_var.get())

            win.destroy()
        else:
            print("WARNING: Percentages do not add up to 100%")
            eh_warning.config(text="WARNING: Percentages do not add up to 100%")

    # GUI for the popup root
    win = Toplevel()
    win.geometry("600x300")
    win.config(background='white')
    win.wm_title("EXPORT SETTINGS")

    # GUI for the popup frame
    win_frame = Frame(win)
    win_frame.config(style='main.TFrame')
    win_frame.pack(fill='both', expand=True)

    eh_train_percent = Label(win_frame,
                             text="Percent of dataset assigned to train: ",
                             style='settings.TLabel',
                             font=("Helvetica", 9, "bold"))
    eh_train_percent.grid(row=0, column=0, padx=5, pady=5)

    eh_train_percent_tb = Entry(win_frame,
                                width=10,
                                style='color.TEntry')
    eh_train_percent_tb.insert(0, conf.datasets.percent_train)
    eh_train_percent_tb.grid(row=0, column=1, padx=5, pady=5)

    eh_valid_percent = Label(win_frame,
                             text="Percent of dataset assigned to valid: ",
                             style='settings.TLabel',
                             font=("Helvetica", 9, "bold"))
    eh_valid_percent.grid(row=1, column=0, padx=5, pady=5)

    eh_valid_percent_tb = Entry(win_frame,
                                width=10,
                                style='color.TEntry')
    eh_valid_percent_tb.insert(0, conf.datasets.percent_valid)
    eh_valid_percent_tb.grid(row=1, column=1, padx=5, pady=5)

    eh_test_percent = Label(win_frame,
                            text="Percent of dataset assigned to test: ",
                            style='settings.TLabel',
                            font=("Helvetica", 9, "bold"))
    eh_test_percent.grid(row=2, column=0, padx=5, pady=5)

    eh_test_percent_tb = Entry(win_frame,
                               width=10,
                               style='color.TEntry')
    eh_test_percent_tb.insert(0, conf.datasets.percent_test)
    eh_test_percent_tb.grid(row=2, column=1, padx=5, pady=5)

    eh_data_path = Label(win_frame,
                            text="Path to training_data on Lambda: ",
                            style='settings.TLabel',
                            font=("Helvetica", 9, "bold"))
    eh_data_path.grid(row=3, column=0, padx=5, pady=5)

    eh_data_path_tb = Entry(win_frame,
                               width=60,
                               style='color.TEntry')
    eh_data_path_tb.insert(0, conf.datasets.data_path)
    eh_data_path_tb.grid(row=3, column=1, padx=5, pady=5)

    eh_seed = Label(win_frame,
                    text="Random Seed: ",
                    style='settings.TLabel',
                    font=("Helvetica", 9, "bold"))
    eh_seed.grid(row=4, column=0, padx=5, pady=5)

    eh_seed_tb = Entry(win_frame,
                       width=20,
                       style='color.TEntry')
    eh_seed_tb.insert(0, conf.datasets.seed)
    eh_seed_tb.grid(row=4, column=1, padx=5, pady=5)

    eh_class_settings = Label(win_frame,
                    text="Class to Use: ",
                    style='settings.TLabel',
                    font=("Helvetica", 9, "bold"))
    eh_class_settings.grid(row=5, column=0, padx=5, pady=5)

    # Populate list of classes from config file
    classes = []
    for conf_model_class in conf.classes:
        classes.append(conf_model_class)

    # Create a dropdown menu for all the classes in the config file
    eh_class_settings_var = StringVar(value=conf.datasets.classes)
    eh_class_settings_m = OptionMenu(win_frame, eh_class_settings_var, f"{eh_class_settings_var.get()}", *classes, style="settings.TLabel")
    eh_class_settings_m.config(width=20)
    eh_class_settings_m.grid(row=5, column=1)

    # for i, model_class in enumerate(conf.classes):
    #     eh_class_settings_rb = Radiobutton(win_frame,
    #                                     text="Using " + model_class + " classes",
    #                                     variable=eh_class_settings_var,
    #                                     style='color.TRadiobutton',
    #                                     value=model_class)
    #     eh_class_settings_rb.grid(row=5, column=i, padx=5, pady=5, ipadx=5, ipady=5)

    eh_warning = Label(win_frame,
                       text="",
                       style='error.TLabel',
                       font=("Helvetica", 9, "bold"))
    eh_warning.grid(row=6, column=0, padx=5, pady=5)

    eh_submit_b = Button(win_frame,
               text="Submit",
               style='color.TButton',
               command=lambda: submit())
    eh_submit_b.grid(row=7, column=0, padx=5, pady=5)


# Popup menu for scp-ing
def popup_scp():
    # Inner method for saving the config file and running the scp method
    def submit():
        global lambda_password, file_path
        lambda_password = scp_settings_password_tb.get()

        if scp_settings_path_tb.get() != "":
            conf.lambda_server.destination_path = scp_settings_path_tb.get()
        if scp_settings_username_tb.get() != "":
            conf.lambda_server.username = scp_settings_username_tb.get()

        # Save any changed config values in our dictionary
        with open(f"{path_prefix}config/config2.json", 'w') as outfile:
            json.dump(conf, outfile, indent=4)

        SCP_to_Lambda(file_path,
                      conf.lambda_server.destination_path,
                      conf.lambda_server.username,
                      lambda_password)

        win.destroy()

    # GUI for the popup root
    win = Toplevel()
    win.geometry("500x150")
    win.config(background='white')
    win.wm_title("SCP - REQUIRED INFO")

    # GUI for the popup frame
    win_frame = Frame(win)
    win_frame.config(style='main.TFrame')
    win_frame.pack(fill='both', expand=True)

    scp_settings_path = Label(win_frame,
                              text="Path on Lambda: ",
                              style='settings.TLabel',
                              font=("Helvetica", 9, "bold"))

    scp_settings_path.grid(row=0, column=0)

    scp_settings_path_tb = Entry(win_frame,
                                 width=50,
                                 style='color.TEntry')
    scp_settings_path_tb.insert(0, conf.lambda_server.destination_path)

    scp_settings_path_tb.grid(row=0, column=1, padx=5, pady=5)

    scp_settings_username = Label(win_frame,
                                  text="Username on Lambda: ",
                                  style='settings.TLabel',
                                  font=("Helvetica", 9, "bold"))
    scp_settings_username.grid(row=1, column=0)

    scp_settings_username_tb = Entry(win_frame,
                                     width=50,
                                     style='color.TEntry')
    scp_settings_username_tb.insert(0, conf.lambda_server.username)

    scp_settings_username_tb.grid(row=1, column=1, padx=5, pady=5)

    scp_settings_password = Label(win_frame,
                                  text="Password on Lambda: ",
                                  style='settings.TLabel',
                                  font=("Helvetica", 9, "bold"))
    scp_settings_password.grid(row=2, column=0)

    scp_settings_password_tb = Entry(win_frame,
                                     show='*',
                                     width=50,
                                     style='color.TEntry')
    scp_settings_password_tb.grid(row=2, column=1, padx=5, pady=5)

    b = Button(win_frame,
               text="Submit",
               style='color.TButton',
               command=lambda: submit())
    b.grid(row=3, column=0, padx=5, pady=5)


# Popup menu for adding a new class to the config file
def popup_add_to_config():
    def submit(new_key, new_value):
        new_value = new_value.split(",")
        if new_key != "" and new_value != []:
            conf.classes.update({new_key: new_value})

        # Save any changed config values in our dictionary
        with open(f"{path_prefix}config/config2.json", 'w') as outfile:
            json.dump(conf, outfile, indent=4)

        win.destroy()

    def remove(key):
        # print(key)
        # print(conf.classes[key])

        # Delete from config file by key
        conf.classes.pop(key)

        # Save any changed config values in our dictionary
        with open(f"{path_prefix}config/config2.json", 'w') as outfile:
            json.dump(conf, outfile, indent=4)

        win.destroy()

    win = Toplevel()
    win.geometry("700x150")
    win.config(background='white')
    win.wm_title("ADD TO CONFIG FILE")

    win_frame = Frame(win)
    win_frame.config(style='main.TFrame')
    win_frame.pack(fill='both', expand=True)

    l1 = Label(win_frame,
               text="New class name: ",
               style='settings.TLabel',
               font=("Helvetica", 9, "bold"))
    l1.grid(row=0, column=0)

    e1 = Entry(win_frame,
               width=50,
               style='color.TEntry')
    e1.grid(row=0, column=1, padx=5, pady=5)

    l2 = Label(win_frame,
               text="Class labels (separated by commas, no white-space): ",
               style='settings.TLabel',
               font=("Helvetica", 9, "bold"))
    l2.grid(row=1, column=0)

    e2 = Entry(win_frame,
               width=50,
               style='color.TEntry')
    e2.grid(row=1, column=1, padx=5, pady=5)

    b1 = Button(win_frame,
                text="Submit",
                style='color.TButton',
                command=lambda: submit(e1.get(), e2.get()))
    b1.grid(row=1, column=2, padx=5, pady=5)

    l3 = Label(win_frame,
               text="Remove class(es): ",
               style='settings.TLabel',
               font=("Helvetica", 9, "bold"))
    l3.grid(row=3, column=0)

    # Populate list of classes from config file
    classes = []
    for conf_model_class in conf.classes:
        classes.append(conf_model_class)

    # Create a dropdown menu for all the classes in the config file
    dropdown_val = StringVar()
    menu = OptionMenu(win_frame, dropdown_val, "  (CLASS TO REMOVE)", *classes, style="settings.TLabel")
    menu.config(width=20)
    menu.grid(row=3, column=1)

    b2 = Button(win_frame,
                text="Remove",
                style='color.TButton',
                command=lambda: remove(dropdown_val.get()))
    b2.grid(row=3, column=2, padx=5, pady=5)


#for given two points in convex hull, finds unit vector and orthogonal unit vector and use them as the axis of the rectangle.
def smallestRect(j0, j1, vertices, coords):
  u = [0] * 2
  u[0] = coords[vertices[j1]]-coords[vertices[j0]]
  u[0] = u[0]/np.linalg.norm(u[0])
  u[1] = [-u[0][1],u[0][0]]
  index=[vertices[j1],vertices[j1],vertices[j1],vertices[j1]]
  origin = coords[vertices[j0]]
  zero = [np.dot(u[0],coords[vertices[j1]]), np.dot(u[1],coords[vertices[j1]])] #j1 will always be min Y.
  support = [zero, zero, zero, zero]

  for vert in vertices:
    diff = coords[vert]
    v = [np.dot(u[0],diff), np.dot(u[1],diff)]

    if(v[0] > support[1][0] or (v[0] == support[1][0] and v[1] > support[1][1])): #If same max X, get bigger Y
      index[1] = vert
      support[1] = v

    if(v[1] > support[2][1] or (v[1] == support[2][1] and v[0] < support[2][0])): #If same max Y, get smaller X
      index[2] = vert
      support[2] = v

    if(v[0] < support[3][0] or (v[0] == support[3][0] and v[1] < support[3][1])): #If same min X, get smaller Y
      index[3] = vert
      support[3] = v

  corners = fourPoints(u, support)
  size = (support[1][0] - support[3][0]) * (support[2][1] - support[0][1])
  return size, index, corners;

#Convert the oriented coordinates to the regular x-axis and y-axis coordinates
def toCoords(vector, u):
  x = (vector[0] * u[0][0] + vector[1] * u[1][0])
  y = (vector[0] * u[0][1] + vector[1] * u[1][1])
  return [x,y]

#get the four points of the rectangle and return the coordinates.
# u is size 2 array each containing major axis and minor axis of the rectangle as unit vectors
# support is array of 4 points of the convex hull used to create the bounding boxd
def fourPoints(u, support):
  points = [0] * 4
  LeftTop = [support[3][0], support[2][1]]  #(x min, y max)
  RightTop = [support[1][0], support[2][1]] #(x max, y max)
  RightBot = [support[1][0], support[0][1]] #(x max, y min)
  LeftBot = [support[3][0], support[0][1]]  #(x min, y min)
  points[0] = toCoords(LeftTop, u)
  points[1] = toCoords(RightTop, u)
  points[2] = toCoords(RightBot, u)
  points[3] = toCoords(LeftBot, u)
  return np.array(points)

#return the corners of minimum bounding box of given points
def MinimumRectangle(points):
  if(len(points) < 3):
    print("The number of points have to be greater than 2")
    return None
  coords = np.array(points)
  hull = ConvexHull(coords)
  minSize, minRect, minCorners = smallestRect(hull.vertices.size - 1, 0, hull.vertices, coords) #first rectangle as default
  for j in range(hull.vertices.size - 1): #check all vertices and get the smallest size rectangle
    j1 = j
    j2 = j + 1
    size, rect, corners = smallestRect(j1, j2, hull.vertices, coords)
    if(size < minSize):
      rectCoords = rect
      minSize = size
      minRect = rect
      minCorners = corners
  return minCorners

def convertToDota(file_path):
  if(file_path != ""):
    label_path = f"{file_path}labelTxt/"
    if os.path.exists(label_path):
        shutil.rmtree(label_path)
        os.mkdir(label_path)
    else:
        os.mkdir(label_path)

    annotation_path = ""
    annotation_file_name = ""
    for file in os.listdir(f"{file_path}annotations/"):
        annotation_path = f"{file_path}annotations/{file}"
        annotation_file_name = file
    coco = json.load(open(annotation_path, 'r'))
    img_names = [img["file_name"][:-4] for img in coco["images"]]

    #create label txt files for each image
    for fname in img_names:
        f = open(f"{file_path}labelTxt/{fname}.txt", 'w')
        f.close()
    print(coco["annotations"][0]["segmentation"])

    with open(f"{file_path}images.txt", 'w') as f:
        for fname in img_names:
            print(fname, file = f)

    #convert annotations to labels
    for annotation in coco["annotations"]:
        segmentation = annotation["segmentation"][0]
        if annotation["id"] == 1:
          print(type(segmentation))
        image_id = annotation["image_id"]
        image_name = img_names[int(image_id) - 1]
        coords = [[segmentation[index * 2], segmentation[(index * 2 + 1)]] for index in range(int(len(segmentation) / 2))]
        corners = MinimumRectangle(coords)
        classname = "CR"

        ##Create file
        with open(f"{label_path}{image_name}.txt", 'a') as f:
            print(f"{corners[0][0]} {corners[0][1]} {corners[1][0]} {corners[1][1]} {corners[2][0]} {corners[2][1]} {corners[3][0]} {corners[3][1]} {classname} 0", file=f)
        annotation["segmentation"][0] = [corners[0][0], corners[0][1], corners[1][0], corners[1][1], corners[2][0], corners[2][1], corners[3][0], corners[3][1]]
    print(coco["annotations"][0]["segmentation"])

    print(annotation_file_name)
    oldAnn_path = f"{file_path}annotations_old/"
    if os.path.exists(oldAnn_path):
        shutil.rmtree(oldAnn_path)
        os.mkdir(oldAnn_path)
    else:
        os.mkdir(oldAnn_path)
    shutil.move(annotation_path, f"{oldAnn_path}{annotation_file_name}")

    with open(f"{annotation_path}.json", 'w') as f:
      json.dump(coco, f)

## GLOBAL VARIABLES ##
file_path = ""
lambda_password = ""

# Create the root window
tk_root = Tk()

# Create style Object
style = Style()

# Setting theme to default (built in themes can be found https://wiki.tcl-lang.org/page/List+of+ttk+Themes)
style.theme_use("default")

# Apply custom theme on start-up
theme = conf.appearance.current_theme
update_color(theme)

# Set window title
tk_root.title('CVAT Export Helper, by: Brandon McHenry, release: v1.1')

# Set window size
tk_root.geometry("1000x650")

tk_root.iconbitmap(f"{path_prefix}data/berry.ico")

# Set window background color
tk_root.config(background='white')

# Making a Frame to act as root so I can change the background on the fly
root_frame = Frame(tk_root)
root_frame.config(style='main.TFrame')
root_frame.pack(fill='both', expand=True)

# <editor-fold desc="OPTIONS TOOLBAR GUI">
#
# options_frame = Frame(root_frame)
# options_frame.config(style='settings.TFrame', borderwidth=1, relief="solid")
#
# options_menu1_val = StringVar()
# options_menu1 = Menubutton(root_frame,
#                                text="Theme",
#                                style='color.TMenubutton')
# options_menu1.menu = Menu (options_menu1, tearoff = 0)
# options_menu1["menu"] = options_menu1.menu
#
#
# theme_settings_var = StringVar(value=conf.appearance.current_theme)
# for i, theme_value in enumerate(conf.appearance.themes):
#     options_menu1.menu.add_radiobutton(label="Use " + theme_value,
#                                        variable=theme_settings_var,
#                                        value=theme_value,
#                                        command=lambda: update_color(theme_settings_var.get()))
#
#     # theme_settings_rb = Radiobutton(theme_settings_frame,
#     #                                 text="Use " + theme_value,
#     #                                 variable=theme_settings_var,
#     #                                 style='color.TRadiobutton',
#     #                                 value=theme_value,
#     #                                 command=lambda: update_color(theme_settings_var.get()))
#     # theme_settings_rb.grid(row=0, column=i, padx=5, pady=5, ipadx=5, ipady=5)
#
# options_menu1.pack(side=LEFT)
#
# options_frame.pack(side=TOP)
#
# # progress = Progressbar(root, orient=HORIZONTAL, length=500, mode='determinate')
# #
# # progress.pack(anchor=S)
# #
# # progress.start()

# </editor-fold>

# <editor-fold desc="DISPLAY WINDOW GUI">

# Create a File Explorer label
window_frame = Frame(root_frame)

window_frame.config(style='settings.TFrame', borderwidth=1, relief="solid")

file_explorer_label = Label(window_frame,
                            text="Select the exported zip file from CVAT by clicking the 'Browse Files' button",
                            # width=100, height=4,
                            style='settings.TLabel',
                            font=("Helvetica", 12, "bold"))

file_explorer_label.pack(anchor=CENTER, fill=Y, expand=True)

# DISPLAY AN IMAGE
img_path = f"{path_prefix}data/DJI_0465.JPG"
img = ImageTk.PhotoImage(Image.open(img_path).resize((500, 400), Image.LANCZOS))
image_window = Label(window_frame,
                     text="Select the exported zip file from CVAT by clicking the 'Browse Files' button",
                     # width=100, height=4,
                     style='main.TLabel',
                     image=img,
                     borderwidth=1, relief="solid")

image_window.pack(side='bottom', padx=20, pady=20)

# # Displaying a gif
# gif_path = f"{path_prefix}data/blueberry-walk3.gif"
# img = Image.open(gif_path)
# frames = img.n_frames
# imageObject = [PhotoImage(file=gif_path, format=f"gif -index {i}").subsample(2, 2) for i in range(frames)]
# count = 0
# showAnimation = None
# animation(imageObject, frames, image_window, count)

window_frame.pack(anchor=N, padx=10, pady=10)

# progress = Progressbar(root, orient=HORIZONTAL, length=500, mode='determinate')
#
# progress.pack(anchor=S)
#
# progress.start()

# </editor-fold>

# <editor-fold desc="INPUTS GUI">
input_frame = Frame(root_frame)

input_frame.config(style='settings.TFrame', borderwidth=1, relief="solid")

# <editor-fold desc="Buttons GUI">
buttons_frame = Frame(input_frame)

buttons_frame.config(style='settings.TFrame')

button_explore = Button(buttons_frame,
                        text="Browse Files",
                        style='color.TButton',
                        command=lambda: browse_files())

button_run = Button(buttons_frame,
                    text="Run helper",
                    style='color.TButton',
                    command=lambda: popup_export_helper(file_path))

button_scp = Button(buttons_frame,
                    text="SCP to Lambda",
                    style='color.TButton',
                    command=lambda: popup_scp())

button_exit = Button(buttons_frame,
                     text="Save & Close",
                     style='color.TButton',
                     command=lambda: save_and_close())

button_edit_classes = Button(buttons_frame,
                             text="Edit Classes",
                             style='color.TButton',
                             command=lambda: popup_add_to_config())

button_explore.grid(row=0, column=0, padx=5, pady=5, ipadx=5, ipady=5)

button_run.grid(row=0, column=1, padx=5, pady=5, ipadx=5, ipady=5)

button_scp.grid(row=0, column=2, padx=5, pady=5, ipadx=5, ipady=5)

button_exit.grid(row=0, column=3, padx=5, pady=5, ipadx=5, ipady=5)

button_edit_classes.grid(row=1, column=0, padx=5, pady=5, ipadx=5, ipady=5)

buttons_frame.grid(row=0, column=0, padx=10)

# </editor-fold>

# <editor-fold desc="Settings GUI">
settings_frame = Frame(input_frame)

settings_frame.config(style='main.TFrame')

settings_label = Label(settings_frame,
                       text="Settings:",
                       style='settings.TLabel',
                       font=("Helvetica", 16, "bold"))

settings_label.config(anchor='center')

settings_label.pack(expand=True, fill='x')

# # <editor-fold desc="Folder Settings GUI">
# folder_settings_frame = Frame(settings_frame)
#
# folder_settings_frame.config(style='settings.TFrame')
#
# folder_settings_var = StringVar(value="train")
# folder_settings_train_rb = Radiobutton(folder_settings_frame,
#                                        text="Create train folder",
#                                        variable=folder_settings_var,
#                                        style='color.TRadiobutton',
#                                        value="train")
# folder_settings_train_rb.grid(row=0, column=0, padx=5, pady=5, ipadx=5, ipady=5)
#
# folder_settings_valid_rb = Radiobutton(folder_settings_frame,
#                                        text="Create valid folder",
#                                        variable=folder_settings_var,
#                                        style='color.TRadiobutton',
#                                        value="valid")
# folder_settings_valid_rb.grid(row=0, column=1, padx=5, pady=5, ipadx=5, ipady=5)
#
# folder_settings_test_rb = Radiobutton(folder_settings_frame,
#                                       text="Create test folder",
#                                       variable=folder_settings_var,
#                                       style='color.TRadiobutton',
#                                       value="test")
# folder_settings_test_rb.grid(row=0, column=2, padx=5, pady=5, ipadx=5, ipady=5)
#
# folder_settings_frame.pack(expand=True, fill='x')
# # </editor-fold>



# <editor-fold desc="Theme Settings GUI">
theme_settings_frame = Frame(settings_frame)

theme_settings_frame.config(style='settings.TFrame')

theme_settings_var = StringVar(value=conf.appearance.current_theme)
for i, theme_value in enumerate(conf.appearance.themes):
    theme_settings_rb = Radiobutton(theme_settings_frame,
                                    text="Use " + theme_value,
                                    variable=theme_settings_var,
                                    style='color.TRadiobutton',
                                    value=theme_value,
                                    command=lambda: update_color(theme_settings_var.get()))
    theme_settings_rb.grid(row=0, column=i, padx=5, pady=5, ipadx=5, ipady=5)

theme_settings_frame.pack(expand=True, fill='x')
# </editor-fold>

settings_frame.grid(row=0, column=1)

# </editor-fold>

input_frame.pack(anchor=S, padx=10, pady=10)

# </editor-fold>

tk_root.mainloop()

# """
#
# key = Fernet.generate_key()
# encryption_type = Fernet(key)
# encrypted_message = encryption_type.encrypt(code)
#
# decrypted_message = encryption_type.decrypt(encrypted_message)
#
# exec(decrypted_message)
