import tkinter as tk 
from PIL import Image, ImageTk

# TODO: Confirm width, height and number of obstacles
def display_results():
    width = 600
    height= 480
    
    for number in range(1, 6):
        filename = f"../test_images/{number}_detected.jpg"
        img = Image.open(filename)

        resize_img = img.resize((width, height))

        final_img = ImageTk.PhotoImage(resize_img)
        
        label = tk.Label(image=final_img)
        label.photo = final_img 
        
        if number <= 3:
            label.grid(row=1, column=number)
        else:
            label.grid(row=2, column=number-3)
        
def get_results():
    root = tk.Tk()
    display_results()
    root.mainloop()

if __name__ == '__main__':
    get_results()