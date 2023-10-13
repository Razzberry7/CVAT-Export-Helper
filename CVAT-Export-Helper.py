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
from tkinter.ttk import Progressbar
from zipfile import ZipFile
from paramiko import SSHClient
from scp import SCPClient


# Function for opening the file explorer window
def browse_files():
    global file_path
    filename = filedialog.askopenfilename(initialdir="/",
                                          title="Select a File",
                                          filetypes=(("Zip files",
                                                      "*.zip*"),
                                                     ("all files",
                                                      "*.*")))
    file_path = filename
    # Change label contents
    label_file_explorer.configure(text="File Opened: " + filename)

def zip_folder(path, zipf):
    for dirname, subdirs, files in os.walk(path):
        for filename in files:
            zipf.write(os.path.join(dirname, filename),
                     os.path.relpath(os.path.join(dirname, filename),
                                     os.path.join(path, '..')))

# Function creating aforementioned structure
def export_helper(path):
    try:
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
            dir_path = path_origin + filename + "/" + folder_settings_var.get()
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                os.mkdir(dir_path)
            else:
                os.mkdir(dir_path)

            # Making images folder if it doesn't exist
            images_path = path_origin + filename + "/" + folder_settings_var.get() + "/images"
            if os.path.exists(images_path):
                shutil.rmtree(images_path)
                os.mkdir(images_path)
            else:
                os.mkdir(images_path)

            # Making labels folder if it doesn't exist
            labels_path = path_origin + filename + "/" + folder_settings_var.get() + "/labels"
            if os.path.exists(labels_path):
                shutil.rmtree(labels_path)
                os.mkdir(labels_path)
            else:
                os.mkdir(labels_path)

            # Create a data.yaml file
            dir_path = path_origin + filename + "/"
            with open(dir_path + '/data.yaml', 'w') as f:
                f.write('train: ./data/training_data/' + filename + '/train/images\n')
                f.write('val: ./data/training_data/' + filename + '/valid/images\n')
                f.write('test: ./data/training_data/' + filename + '/test/images\n')
                f.write('\n')
                if class_settings_var.get() == "Berry":
                    f.write('nc: 2\n')
                    f.write("names: ['blue', 'green']")
                if class_settings_var.get() == "Bush":
                    f.write('nc: 1\n')
                    f.write("names: ['bush']")
                if class_settings_var.get() == "Scorch":
                    f.write('nc: 1\n')
                    f.write("names: ['scorch']")

            with ZipFile(path, 'r') as zip:
                for file in zip.namelist():
                    if 'obj_train_data' in file and (file.endswith(".jpg") or file.endswith(".png") or file.endswith(".jpeg")):
                        zip.extract(file, images_path)
                    if 'obj_train_data' in file and file.endswith(".txt"):
                        zip.extract(file, labels_path)

            for file in os.listdir(images_path + "/obj_train_data"):
                shutil.move(os.path.join(images_path + "/obj_train_data", file), images_path)
            shutil.rmtree(images_path + "/obj_train_data")

            for file in os.listdir(labels_path + "/obj_train_data"):
                shutil.move(os.path.join(labels_path + "/obj_train_data", file), labels_path)
            shutil.rmtree(labels_path + "/obj_train_data")

            zf = ZipFile(path_origin + filename + ".zip", "w")
            zip_folder(path_origin + filename, zf)
            zf.close()
    except:
        print("ERROR: Something went wrong when trying to convert the CVAT file. "
              "\nAre you sure you choose the correct zip file?")


def SCP_to_Lambda(file_path, export_path, username, password):
    # print(file_path)
    # print(export_path)
    # print(username)
    # print(password)
    try:
        if file_path and export_path and username and password != "":
            ssh = SSHClient()
            ssh.load_system_host_keys()
            ssh.connect(hostname='lambda04.rowan.edu', port=22, username=username, password=password)

            with SCPClient(ssh.get_transport()) as scp:
                scp.put(file_path, export_path)
    except:
        print("Something went wrong when trying to SCP onto Lambda."
              "\nAre you sure you're connected to the Rowan VPN?")


file_path = ""

# Create the root window
root = Tk()

# Set window title
root.title('CVAT Export Helper, by: Brandon McHenry')

# Set window size
root.geometry("850x300")

# root.iconbitmap("./berry.ico")

# Set window background color
berry_blue = '#%02x%02x%02x' % (164, 206, 252)
text_color = '#%02x%02x%02x' % (15, 51, 117)
outline_color = '#%02x%02x%02x' % (119, 182, 251)
root.config(background=berry_blue)

# Create a File Explorer label
label_file_explorer = Label(root,
                            text="Select the exported zip file from CVAT by clicking the 'Browse Files' button",
                            width=100, height=4,
                            fg=text_color, bg=berry_blue,
                            font=("Helvetica", 12, "bold"))

label_file_explorer.pack(anchor=N, fill=BOTH, expand=True)

# <editor-fold desc="INPUTS GUI">
input_frame = Frame(root)

input_frame.config(bg=outline_color, borderwidth=1, relief="solid")

# <editor-fold desc="Buttons GUI">
buttons_frame = Frame(input_frame)

buttons_frame.config(bg=outline_color)

button_explore = Button(buttons_frame,
                        text="Browse Files",
                        fg=text_color,
                        command=lambda: browse_files())

button_run = Button(buttons_frame,
                    text="Run helper",
                    fg=text_color,
                    command=lambda: export_helper(file_path))

button_scp = Button(buttons_frame,
                    text="SCP to Lambda",
                    fg=text_color,
                    command=lambda: SCP_to_Lambda(file_path,
                                                  scp_settings_path_tb.get(),
                                                  scp_settings_username_tb.get(),
                                                  scp_settings_password_tb.get()))

button_exit = Button(buttons_frame,
                     text="Close",
                     fg=text_color,
                     command=lambda: sys.exit())

button_explore.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

button_run.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

button_scp.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

button_exit.pack(side=LEFT, padx=5, pady=5, ipadx=5, ipady=5)

buttons_frame.grid(row=0, column=0, padx=10)

# </editor-fold>

# <editor-fold desc="Settings GUI">
settings_frame = Frame(input_frame)

settings_frame.config(bg=berry_blue)

# <editor-fold desc="Folder Settings GUI">
folder_settings_frame = Frame(settings_frame)

folder_settings_frame.config(bg=outline_color)

folder_settings_label = Label(folder_settings_frame,
                              text="Settings: ",
                              fg=text_color, bg=outline_color,
                              font=("Helvetica", 16, "bold"))
folder_settings_label.pack(side=TOP)

folder_settings_var = StringVar(value="train")
folder_settings_train_cb = Radiobutton(folder_settings_frame,
                                       text="Create train folder",
                                       variable=folder_settings_var,
                                       fg=text_color, bg=outline_color,
                                       value="train")
folder_settings_train_cb.pack(side=LEFT)

folder_settings_valid_cb = Radiobutton(folder_settings_frame,
                                       text="Create valid folder",
                                       variable=folder_settings_var,
                                       fg=text_color, bg=outline_color,
                                       value="valid")
folder_settings_valid_cb.pack(side=LEFT)

folder_settings_test_cb = Radiobutton(folder_settings_frame,
                                      text="Create test folder",
                                      variable=folder_settings_var,
                                      fg=text_color, bg=outline_color,
                                      value="test")
folder_settings_test_cb.pack(side=LEFT)

folder_settings_frame.pack(expand=True, fill='x')
# </editor-fold>

# <editor-fold desc="Class Settings GUI">
class_settings_frame = Frame(settings_frame)

class_settings_frame.config(bg=outline_color)

class_settings_var = StringVar(value="Berry")
class_settings_berry_cb = Radiobutton(class_settings_frame,
                                      text="Using berry classes",
                                      variable=class_settings_var,
                                      fg=text_color, bg=outline_color,
                                      value="Berry")
class_settings_berry_cb.pack(side=LEFT)

class_settings_bush_cb = Radiobutton(class_settings_frame,
                                     text="Using bush classes",
                                     variable=class_settings_var,
                                     fg=text_color, bg=outline_color,
                                     value="Bush")
class_settings_bush_cb.pack(side=LEFT)

class_settings_scorch_cb = Radiobutton(class_settings_frame,
                                       text="Using scorch classes",
                                       variable=class_settings_var,
                                       fg=text_color, bg=outline_color,
                                       value="Scorch")
class_settings_scorch_cb.pack(side=LEFT)

class_settings_frame.pack(expand=True, fill='x') # Center the frame
# </editor-fold>

# <editor-fold desc="SCP Settings GUI">
scp_settings_frame = Frame(settings_frame)

scp_settings_frame.config(bg=outline_color)

# Create a File Explorer label
scp_settings_path = Label(scp_settings_frame,
                            text="Path on Lambda: ",
                            fg=text_color, bg=outline_color,
                            font=("Helvetica", 9, "bold"))

scp_settings_path.grid(row=0, column=0)

scp_settings_path_tb = Entry(scp_settings_frame,
                            width=50,
                            fg=text_color, bg=berry_blue)

scp_settings_path_tb.grid(row=0, column=1, padx=5, pady=5)

scp_settings_username = Label(scp_settings_frame,
                            text="Username on Lambda: ",
                            fg=text_color, bg=outline_color,
                            font=("Helvetica", 9, "bold"))

scp_settings_username.grid(row=1, column=0)

scp_settings_username_tb = Entry(scp_settings_frame,
                            width=25,
                            fg=text_color, bg=berry_blue)

scp_settings_username_tb.grid(row=1, column=1, padx=5, pady=5)

scp_settings_password = Label(scp_settings_frame,
                            text="Password on Lambda: ",
                            fg=text_color, bg=outline_color,
                            font=("Helvetica", 9, "bold"))

scp_settings_password.grid(row=2, column=0)

scp_settings_password_tb = Entry(scp_settings_frame,
                            show='*',
                            width=25,
                            fg=text_color, bg=berry_blue)

scp_settings_password_tb.grid(row=2, column=1, padx=5, pady=5)


scp_settings_frame.pack(expand=True, fill='x') # Center the frame

# </editor-fold>

settings_frame.grid(row=0, column=1)

# </editor-fold>

# progress = Progressbar(root, orient=HORIZONTAL, length=500, mode='determinate')
#
# progress.pack(anchor=S)
#
# progress.start()


input_frame.pack(anchor=S, padx=10, pady=10)

# </editor-fold>

root.mainloop()
