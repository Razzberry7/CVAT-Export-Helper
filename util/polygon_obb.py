import math
from scipy.spatial import ConvexHull
import numpy as np
import os
import shutil
import random
import string

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

#From dataset_splitter.py
#modified 4/1/2024
def move_files(path, path_to_new_folder, num_to_move, seed):
    random.seed(seed)
    # List the files at the path
    img_files = os.listdir(path + "images/")

    # For as many as we're moving based on the percent of files we want to move
    for i in range(num_to_move):
        # Grab random image file
        file = random.choice(img_files)

        # Define paths for image files in order to move them
        src_img_file = os.path.join(path+ "images/", file)
        dst_img_file = os.path.join(path_to_new_folder + "/images/", file)

        # Display
        print("This file: " + src_img_file + " is going to: " + dst_img_file)

        # Move the file
        shutil.move(src_img_file, dst_img_file)

        fileType = -4
        # Define paths for the corresponding text files in order to move them
        if file.endswith((".jpg", ".JPG", ".png", ".PNG")):
            fileType = -4
        elif file.endswith((".jpeg", ".JPEG")): 
            fileType = -5
        else:
            print("Warning: it looks like the image files are not jpg, png, jpeg. The name of the image file is ", file)
        src_txt_file = os.path.join(path + "labelTxt/", file[:fileType] + ".txt")
        dst_txt_file = os.path.join(path_to_new_folder + "labelTxt/", file[:fileType] + ".txt")

        # Display
        print("This file: " + src_txt_file + " is going to: " + dst_txt_file)

        # Move the file
        shutil.move(src_txt_file, dst_txt_file)