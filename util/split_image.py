#divide
from PIL import Image
import os
from pathlib import Path



def divideImage(folder_path, image_path, img_dim=640):
  im = Image.open(image_path)
  img_name = Path(image_path).stem
  img_type = str(im.format)
  if img_type == "MPO":
    img_type = "JPG"
  txt_path = folder_path+"labels/"+img_name+".txt"
  with open(txt_path, "r") as file:
    lines = file.read().splitlines()
  x, y = im.size

  for i in range(0, x, img_dim):
    for j in range(0, y, img_dim):
      low_x = (i) / x
      low_y = (j) / y
      high_x = (i + img_dim) / x
      high_y = (j + img_dim) / y

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
          if(coord[0] > low_x and coord[0] < high_x and coord[1] > low_y and coord[1] < high_y):
            points.append(coord)
        #if(len(points) > 1 or (center[0] > low_x and center[0] < high_x and center[1] > low_y and center[1] < high_y)):
        if(len(points) > 1):
          coords = [(boxlist[1] - low_x) / x_scale, (boxlist[2]- low_y) / y_scale, (boxlist[3] - low_x) / x_scale, (boxlist[4] - low_y) / y_scale, (boxlist[5] - low_x) / x_scale, (boxlist[6] - low_y) / y_scale , (boxlist[7] - low_x) / x_scale, (boxlist[8] - low_y) / y_scale]
          clipped_coords = [min(max(0, coord), 1) for coord in coords]
          newList.append(clipped_coords)

      newIm = im.crop((i, j, i + img_dim, j + img_dim))


      newIm.save(f"{folder_path}images/{img_name}_{str(i)}_{str(j)}.{img_type}")
      txt_file = open(f"{folder_path}labels/{img_name}_{str(i)}_{str(j)}.txt", "w")
      for coordinates in newList:
        print(f"0 {coordinates[0]} {coordinates[1]} {coordinates[2]} {coordinates[3]} {coordinates[4]} {coordinates[5]} {coordinates[6]} {coordinates[7]}", file = txt_file)
      txt_file.close()
  im.close()
  os.remove(image_path)
  os.remove(txt_path)