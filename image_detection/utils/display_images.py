import os
import tkinter as tk 
from PIL import Image, ImageTk

# TODO: Confirm width, height
def display_results(dir_path):
    width = 600
    height= 480
    
    number = 0
    for file in os.listdir(dir_path):
        filename = os.fsdecode(file)
        # filename = f"{dir_path}/{number}.jpg"
        img = Image.open(filename)

        # resize image
        resize_img = img.resize((width, height))
        final_img = ImageTk.PhotoImage(resize_img)
        
        label = tk.Label(image=final_img)
        label.photo = final_img 
        
        # display in 2 rows
        number+=1
        if number <= 3:
            label.grid(row=1, column=number)
        else:
            label.grid(row=2, column=number-3)
        
def get_results(dir_path):
    root = tk.Tk()
    display_results(dir_path)
    root.mainloop()

if __name__ == '__main__':
    get_results()