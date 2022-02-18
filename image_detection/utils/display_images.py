import tkinter as tk 
from PIL import Image, ImageTk

# TODO: Confirm width, height and number of obstacles
def display_results(dir_path):
    width = 600
    height= 480
    
    # TODO: change number to image id
    for number in range(1, 6):
        filename = f"{dir_path}/{number}.jpg"
        img = Image.open(filename)

        resize_img = img.resize((width, height))

        final_img = ImageTk.PhotoImage(resize_img)
        
        label = tk.Label(image=final_img)
        label.photo = final_img 
        
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