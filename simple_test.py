import tkinter as tk

root = tk.Tk()
root.title("简单测试")
root.geometry("400x300")

label = tk.Label(root, text="Hello, World!")
label.pack(pady=20)

root.mainloop()