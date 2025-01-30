import cv2
import glob
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import math
import datetime
import pandas as pd
import exifread


class ImageLineDrawer:
    def __init__(self, image_paths):
        self.image_paths = image_paths
        self.current_image_index = 0
        self.total_photos = len(image_paths)
        self.points = []  # Initialize points list
        self.lines = []   # Store drawn lines
        self.most_recent_line_length = 0  # Track the most recent line length
        self.results_list = [] 
        self.dates_list =[] 
        self.root = tk.Tk()

        self.canvas_width = 800
        self.canvas_height = 600

        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack()

        self.btn_save = tk.Button(self.root, text="Save", command=self.save_line_info)
        self.root.bind("<Return>", lambda event: self.save_line_info())
        
        self.btn_save.pack()
        self.status_label = tk.Label(self.root, text="")
        self.status_label.pack()


        self.load_next_image()
        self.root.mainloop()

    def load_next_image(self):
        if self.current_image_index < self.total_photos:
            self.image_path = self.image_paths[self.current_image_index]
            self.img = cv2.imread(self.image_path)
            self.display_image()
            self.canvas.bind("<Button-1>", self.on_click)
            mydate = self.get_image_datetime(self.image_path)
            self.dates_list.append(mydate)
        else:
            self.finish_and_close()

    def display_image(self):
        img_rgb = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        img_pil.thumbnail((self.canvas_width, self.canvas_height))
        img_tk = ImageTk.PhotoImage(img_pil)
  

        self.canvas.create_image(0, 0, anchor="nw", image=img_tk)
        self.canvas.image = img_tk
        status_text = f"Photo {self.current_image_index + 1}/{self.total_photos}"
        self.status_label.config(text=status_text)

        # Draw existing lines on the canvas
        for line in self.lines:
            self.canvas.create_line(line, fill='purple', width=4)  # Purple and twice as thick

    def on_click(self, event):
        # Record the clicked points
        self.points.append((event.x, event.y))
        if len(self.points) == 2:
            self.lines.append(self.points)  # Append the entire points list as a line
            self.points = []
            self.display_image()

    def save_line_info(self):
    # Check if there are enough points to calculate the line length and angle
        if len(self.lines) > 0:
            line = self.lines[-1]  # Retrieve the most recent drawn line
            # Calculate and save the length of the line in pixels
            length = self.calculate_line_length(line)
            # Calculate and save the angle of the line with the horizontal axis
            angle = self.calculate_line_angle(line)

            # Save or store the length and angle in the results list
            self.results_list.append({"Length": length, "Angle": angle})

            # Update the most recent line length
            self.most_recent_line_length = length

            # Move to the next image
            self.current_image_index += 1
            self.lines = []  # Clear drawn lines for the next image
            self.load_next_image()
        else:
            print("No line drawn. Click on the canvas to draw a line.")


    def calculate_line_length(self, line):
        # Check if the line has two points
        if len(line) == 2:
            # Calculate the Euclidean distance between two points
            return np.sqrt((line[1][0] - line[0][0])**2 + (line[1][1] - line[0][1])**2)
        else:
            return 0  # Return 0 if the line doesn't have two points
        
    def get_image_datetime(self, image_path):
        # Extract datetime from image metadata using exifread
        with open(image_path, 'rb') as file:
            tags = exifread.process_file(file)
            datetime_tag = tags.get('EXIF DateTimeOriginal')
            if datetime_tag:
                return datetime.datetime.strptime(str(datetime_tag), '%Y:%m:%d %H:%M:%S')
            else:
                return None


    def calculate_line_angle(self, line):
        # Check if the line has two points
        if len(line) == 2:
            # Calculate the angle between the line and the horizontal axis
            angle_rad = math.atan2(line[1][1] - line[0][1], line[1][0] - line[0][0])
            # Convert radians to degrees
            angle_deg = math.degrees(angle_rad)
            return angle_deg
        else:
            return 0  # Return 0 if the line doesn't have two points
    def finish_and_close(self):
        # Save the results to a DataFrame after processing all images
        results_list = self.results_list
        indexes = self.dates_list
        print(len(results_list))
        # indexes = np.unique(indexes)

        print(len(indexes))
        df = pd.DataFrame(results_list, index = indexes)
        df.to_csv(f'/Users/cowherd/Documents/caldorphotos/{folder}_results.csv')
        # results_list = self.results_list
        # indexes = self.dates_list

        ## make it into a dataframe
        #df = pd.DataFrame(results_list, index = indexes)
        # df.to_csv(f'/Users/cowherd/Documents/caldorphotos/{folder}_results.csv')
        # print(df.head)
        # Close the photo viewer
        self.root.destroy()
        

if __name__ == "__main__":
    # Provide a list of image paths
    folder='101_WSCT_286'
    images = sorted(glob.glob(f'/Users/cowherd/Documents/caldorphotos/{folder}/*.JPG'))
    print(len(images))
    # Create an instance of the ImageLineDrawer class
    drawer = ImageLineDrawer(images) 
    

    ## make it into a dataframe
