import os
import csv

# Define the path to the CSV file
movedict_csv = os.path.join(os.getcwd(), "data", "MoveDict.csv")
modified_csv = os.path.join(os.getcwd(), "data", "MoveDictModified.csv")

#read each .png file in the folder and return a list of the names
def get_png_files(folder):
    png_files = []
    for file in os.listdir(folder):
        if file.endswith(".png") and "_Dark" not in file:
            png_files.append(file)
    return png_files

images = get_png_files("assets")
# print("images:",images)

#read each image name and filter the move name
moves = []
for image in images:
    name = image[3:][:-4]
    if "_Dark" in name:
        continue
    #if the first letter is a number, remove the first 3 characters
    if name[0].isdigit():
        name = name[3:]
    moves.append(name)
# print("moves:",moves)

#make a dictionary with the moves as keys and the images as values
move_dict = {}
for move,image in zip(moves,images):
    move_dict[move] = image

print(move_dict)

# Open the CSV file and read its contents
new_csv = {}
with open(movedict_csv, mode='r') as file:
    csv_reader = csv.DictReader(file, delimiter=';')
    
    # if the "move" column value is the same as the "move" on the move_dict, add the image to the new_csv
    for row in csv_reader:
        move = row["Move"]
        if move in move_dict:
            row["Image"] = move_dict[move]
        new_csv[move] = row

# Write the new CSV file
with open(modified_csv, mode='w', newline='') as file:
    fieldnames = ["Move", "Name", "Image"]
    writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
    writer.writeheader()
    for key in new_csv:
        writer.writerow(new_csv[key])