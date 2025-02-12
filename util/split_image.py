#divide
from PIL import Image
import os
import math
from pathlib import Path

def scale_of(item, low_x, high_x, low_y, high_y, vector):
  scale = 0
  if(item[0] < low_x):
    scale = (low_x - item[0]) / vector[0]
  if(item[0] > high_x):
    scale = (high_x - item[0]) / vector[0]
  if(item[1] < low_y):
    scale = (low_y - item[1]) / vector[1]
  if(item[1] > high_y):
    scale = (high_y - item[1]) / vector[1]
  return scale

def distance(a, b):
  x_diff = (a[0] - b[0])
  y_diff = (a[1] - b[1])
  return math.sqrt(x_diff*x_diff + y_diff * y_diff)

def size_of(point, right_p, left_p):
  width = distance(point, right_p)
  height = distance(point, left_p)
  return width * height


def divideImage(folder_path, image_path, destination_path, split_counter, img_dim=640):
  counter = split_counter
  im = Image.open(image_path)
  img_name = Path(image_path).stem
  img_type = str(im.format)
  if img_type == "MPO":
    img_type = "JPG"
  txt_path = folder_path+"labels/"+img_name+".txt"
  with open(txt_path, "r") as file:
    lines = file.read().splitlines()
  x, y = im.size

  #ceiling division
  num_of_row = -(x // -img_dim)
  x_padding = img_dim - (x // num_of_row)
  num_of_col = -(y // -img_dim)
  y_padding = img_dim - (y // num_of_col)
  for i in range(0, x, img_dim):
    for j in range(0, y, img_dim):
      #adds 10 pixel padding to the images
      start_i = (i - x_padding * (i / img_dim))
      start_j = (j - y_padding * (j / img_dim))
      low_x =  start_i / x
      low_y =  start_j/ y
      high_x = (start_i + img_dim) / x
      high_y = (start_j + img_dim) / y
      
      #overlap the last row/column images
      if (i + img_dim) > x:
        high_x = 1
        low_x = 1 - img_dim / x
        start_i = x - img_dim
      if (j + img_dim) > y:
        high_y = 1
        low_y = 1 - img_dim / y
        start_j = y - img_dim
        
      newList = []
      x_scale = high_x - low_x
      y_scale = high_y - low_y
      for line in lines:
        boxlistString = list(line.split(" "))
        a_class = boxlistString[0] #All annotations will be CR
        boxlist = [0, float(boxlistString[1]), float(boxlistString[2]), float(boxlistString[3]), float(boxlistString[4]), float(boxlistString[5]), float(boxlistString[6]), float(boxlistString[7]), float(boxlistString[8])]
        box = [(boxlist[1],boxlist[2]),(boxlist[3],boxlist[4]),(boxlist[5],boxlist[6]),(boxlist[7],boxlist[8])]
        center = ((min(point[0] for point in box) + max(point[0] for point in box))/2, (min(point[1] for point in box) + max(point[1] for point in box))/2)
        points = []
        for coord in box:
          if(coord[0] >= low_x and coord[0] <= high_x and coord[1] >= low_y and coord[1] <= high_y):
            points.append(coord)
        #if(len(points) > 1 or (center[0] > low_x and center[0] < high_x and center[1] > low_y and center[1] < high_y)):
        if(len(points) > 1):
          coords = [(boxlist[1],boxlist[2]),(boxlist[3],boxlist[4]),(boxlist[5],boxlist[6]),(boxlist[7],boxlist[8])]
          if(len(points) == 3):
            counter = counter + 1
            for item in box:
              if item not in points:
                item_index = box.index(item)
                left_p = box[(item_index + 3) % 4]
                right_p = box[(item_index + 1) % 4]
                fourth_p = box[(item_index + 2) % 4]
                
                vector = (left_p[0] - item[0], left_p[1] - item[1])
                scale = scale_of(item, low_x, high_x, low_y, high_y, vector)
                left_n_p = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                left_n_r = (right_p[0] + scale * vector[0], right_p[1] + scale * vector[1])
                left_size = size_of(left_n_p, left_n_r, left_p)
                
                vector = (right_p[0] - item[0], right_p[1] - item[1])
                scale = scale_of(item, low_x, high_x, low_y, high_y, vector)
                right_n_p = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                right_n_l = (left_p[0] + scale * vector[0], left_p[1] + scale * vector[1])
                right_size = size_of(right_n_p, right_n_l, right_p)
                
                
                if(left_size > right_size):
                  coords[item_index] = left_n_p
                  coords[(item_index + 3) % 4] = left_p
                  coords[(item_index + 2) % 4] = fourth_p
                  coords[(item_index + 1) % 4] = left_n_r
                else:
                  coords[item_index] = right_n_p
                  coords[(item_index + 1) % 4] = right_p
                  coords[(item_index + 2) % 4] = fourth_p
                  coords[(item_index + 3) % 4] = right_n_l
          if(len(points) == 2):
            size_coords = []
            counter = counter + 1
            for item in box:
              if item not in points:
                item_index = box.index(item)
                left_p = box[(item_index + 3) % 4]
                right_p = box[(item_index + 1) % 4]
                fourth_p = box[(item_index + 2) % 4]
                new_item = item
                new_right = right_p
                new_left = left_p
                  
                new_size = size_of(new_item, right_p, left_p)
                if left_p in points:
                  vector = (left_p[0] - item[0], left_p[1] - item[1])
                  if(item[0] < low_x):
                    scale = (low_x - item[0]) / vector[0]
                    new_item = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_right = (right_p[0] + scale * vector[0], right_p[1] + scale * vector[1])
                    new_size = size_of(new_item, new_right, left_p)
                  if(item[0] > high_x):
                    scale = (high_x - item[0]) / vector[0]
                    new_item = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_right = (right_p[0] + scale * vector[0], right_p[1] + scale * vector[1])
                    new_size = size_of(new_item, new_right, left_p)
                  
                  if(item[1] < low_y):
                    scale = (low_y - item[1]) / vector[1]
                    new_item_y = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_right_y = (right_p[0] + scale * vector[0], right_p[1] + scale * vector[1])
                    new_size_y = size_of(new_item_y, new_right_y, left_p)
                    if(new_size_y < new_size):
                      new_item = new_item_y
                      new_right = new_right_y
                      new_size = new_size
                  if(item[1] > high_y):
                    scale = (high_y - item[1]) / vector[1]
                    new_item_y = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_right_y = (right_p[0] + scale * vector[0], right_p[1] + scale * vector[1])
                    new_size_y = size_of(new_item_y, new_right_y, left_p)
                    if(new_size_y < new_size):
                      new_item = new_item_y
                      new_right = new_right_y
                      new_size = new_size
                  
                  
                if right_p in points:
                  vector = (right_p[0] - item[0], right_p[1] - item[1])
                  if(item[0] < low_x):
                    scale = (low_x - item[0]) / vector[0]
                    new_item = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_left = (left_p[0] + scale * vector[0], left_p[1] + scale * vector[1])
                    new_size = size_of(new_item, new_left, right_p)
                  if(item[0] > high_x):
                    scale = (high_x - item[0]) / vector[0]
                    new_item = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_left = (left_p[0] + scale * vector[0], left_p[1] + scale * vector[1])
                    new_size = size_of(new_item, new_left, right_p)
                  
                  if(item[1] < low_y):
                    scale = (low_y - item[1]) / vector[1]
                    new_item_y = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_left_y = (left_p[0] + scale * vector[0], left_p[1] + scale * vector[1])
                    new_size_y = size_of(new_item_y, new_left_y, right_p)
                    if(new_size_y < new_size):
                      new_item = new_item_y
                      new_left = new_left_y
                      new_size = new_size
                  if(item[1] > high_y):
                    scale = (high_y - item[1]) / vector[1]
                    new_item_y = (item[0] + scale * vector[0], item[1] + scale * vector[1])
                    new_left_y = (left_p[0] + scale * vector[0], left_p[1] + scale * vector[1])
                    new_size_y = size_of(new_item_y, new_left_y, right_p)
                    if(new_size_y < new_size):
                      new_item = new_item_y
                      new_left = new_left_y
                      new_size = new_size
                
                coords[item_index] = new_item
                coords[(item_index + 3) % 4] = new_left
                coords[(item_index + 2) % 4] = fourth_p
                coords[(item_index + 1) % 4] = new_right
                size = size_of(new_item, new_left, new_right)
                size_coords.append([size, list(coords)])
            if(size_coords[0][0] < size_coords[1][0]):
              coords = size_coords[0][1]
          
          clipped_coords = [(coords[0][0] - low_x) / x_scale, (coords[0][1]- low_y) / y_scale, (coords[1][0] - low_x) / x_scale, (coords[1][1] - low_y) / y_scale, (coords[2][0] - low_x) / x_scale, (coords[2][1] - low_y) / y_scale , (coords[3][0] - low_x) / x_scale, (coords[3][1] - low_y) / y_scale]
          
          #checks if each of the four edges are outside boundary and clips if needed
          #checking left side x=0
          for clipped_coord in clipped_coords:
            if(clipped_coord < 0 or clipped_coord > 1):
              clipped_coord = max(0, min(1, clipped_coord))
          newList.append(clipped_coords)

      newIm = im.crop((start_i, start_j, start_i + img_dim, start_j + img_dim))


      newIm.save(f"{destination_path}images/{img_name}_{str(start_i)}_{str(start_j)}.{img_type}")
      txt_file = open(f"{destination_path}labels/{img_name}_{str(start_i)}_{str(start_j)}.txt", "w")
      for coordinates in newList:
        print(f"0 {coordinates[0]} {coordinates[1]} {coordinates[2]} {coordinates[3]} {coordinates[4]} {coordinates[5]} {coordinates[6]} {coordinates[7]}", file = txt_file)
      txt_file.close()
  im.close()
  os.remove(image_path)
  os.remove(txt_path)
  return counter
