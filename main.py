import tkinter as tk
from tkinter.simpledialog import askstring
import pickle
import os
from datetime import datetime
from tkinter import PhotoImage


class FloatingWidget:
    def __init__(self, root):
        self.root = root
        self.root.geometry("300x300+1000+10")
        self.root.configure(bg="black")
        self.root.wm_attributes("-alpha", 0.8)
        self.root.overrideredirect(True)
        self.root.wm_attributes("-topmost", True)

        self.todo_frame = tk.Frame(self.root, bg="black")
        self.todo_frame.pack(fill="both", expand=True)

        self.todos = self.load_todos()
        self.update_todo_list()

        button_frame = tk.Frame(self.root, bg="black")
        button_frame.pack(side="bottom", fill="x")

        self.toggle_button = tk.Button(button_frame, text="Turn OFF Always On Top", command=self.toggle_on_top,
                                       bg="blue", fg="white")
        self.toggle_button.pack(side="left", fill="both", expand=True)

        self.add_todo_button = tk.Button(button_frame, text="Add To-Do", command=self.add_todo, bg="green", fg="white")
        self.add_todo_button.pack(side="left", fill="both", expand=True)

        self.root.bind("<ButtonPress-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.on_move)
        self.root.bind("<ButtonRelease-1>", self.stop_move)

        self.reset_time = "06:00:00"
        self.check_reset_time()

        self.restore_position()

    def update_todo_list(self):
        for widget in self.todo_frame.winfo_children():
            widget.destroy()

        for i, todo in enumerate(self.todos):
            todo_frame = tk.Frame(self.todo_frame, bg="black")
            todo_frame.pack(fill="x", pady=2, anchor="w")

            if 'var' not in todo:
                todo['var'] = tk.IntVar(value=0)

            canvas = tk.Canvas(todo_frame, width=24, height=24, bg="red", bd=0, highlightthickness=0)
            canvas.pack(side="left", padx=5, anchor="w")

            if todo['checked']:
                canvas.config(bg="green")
            else:
                canvas.config(bg="red")

            canvas.bind("<Button-1>", lambda event, idx=i: self.toggle_rectangle(idx))

            label = tk.Label(todo_frame, text=todo['task'], fg="white", bg="black", font=("Arial", 10), anchor="w")
            label.pack(side="left", fill="x", padx=10, anchor="w")

            label.update_idletasks()
            delete_icon = PhotoImage(file="delete_icon.png")
            delete_icon = delete_icon.subsample(12, 12)
            delete_label = tk.Label(todo_frame, image=delete_icon, bg="black", width=20, height=20)
            delete_label.photo = delete_icon
            delete_label.pack(side="right", padx=5)

            delete_label.bind("<Button-1>", lambda event, idx=i: self.delete_todo(idx))

        self.todo_frame.update_idletasks()
        self.adjust_window_height()

    def adjust_window_height(self):
        todo_count = len(self.todos)
        if todo_count == 0:
            estimated_height = 58
        else:
            estimated_height = 28 * todo_count + 30
        self.root.geometry(f"300x{estimated_height}+1000+10")

    def check_reset_time(self):
        current_time = datetime.now()
        reset_time_today = datetime.strptime(f"{current_time.date()} {self.reset_time}", "%Y-%m-%d %H:%M:%S")
        if current_time >= reset_time_today:
            self.reset_checkboxes()

    def reset_checkboxes(self):
        for todo in self.todos:
            todo['checked'] = False
            todo['var'].set(0)
        self.save_todos()
        self.update_todo_list()

    def toggle_on_top(self):
        if self.root.wm_attributes("-topmost"):
            self.root.wm_attributes("-topmost", False)
            self.toggle_button.config(text="Turn ON Always On Top")
        else:
            self.root.wm_attributes("-topmost", True)
            self.toggle_button.config(text="Turn OFF Always On Top")

    def add_todo(self):
        todo_text = askstring("To-Do", "Enter your task:", parent=self.root)
        if todo_text:
            todo = {'task': todo_text, 'checked': False, 'var': tk.IntVar(value=0)}
            self.todos.append(todo)
            self.save_todos()
            self.update_todo_list()

    def toggle_rectangle(self, idx):
        todo = self.todos[idx]
        todo['checked'] = not todo['checked']
        self.update_single_rectangle(idx)
        self.save_todos()

    def update_single_rectangle(self, idx):
        todo = self.todos[idx]
        todo_frame = self.todo_frame.winfo_children()[idx]
        for widget in todo_frame.winfo_children():
            if isinstance(widget, tk.Canvas):
                if todo['checked']:
                    widget.config(bg="green")
                else:
                    widget.config(bg="red")

    def delete_todo(self, idx):
        del self.todos[idx]
        self.save_todos()
        self.update_todo_list()

    def save_todos(self):
        serializable_todos = [{'task': todo['task'], 'checked': todo['checked']} for todo in self.todos]
        with open("todos.pkl", "wb") as f:
            pickle.dump(serializable_todos, f)

    def load_todos(self):
        if os.path.exists("todos.pkl"):
            try:
                with open("todos.pkl", "rb") as f:
                    if os.path.getsize("todos.pkl") > 0:
                        todos = pickle.load(f)
                        for todo in todos:
                            if 'var' not in todo:
                                todo['var'] = tk.IntVar(value=1 if todo['checked'] else 0)
                        return todos
            except (EOFError, pickle.UnpicklingError):
                return []
        return []

    def save_position(self):
        self.root.update_idletasks()
        position = (self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height())
        with open("window_position.pkl", "wb") as f:
            pickle.dump(position, f)

    def restore_position(self):
        screen_width = self.root.winfo_screenwidth()
        if os.path.exists("window_position.pkl"):
            try:
                with open("window_position.pkl", "rb") as f:
                    position = pickle.load(f)
                    if position:
                        self.root.geometry(f"+{position[0]}+{position[1]}")
                        return
            except (EOFError, pickle.UnpicklingError):
                pass
        self.root.geometry(f"+{screen_width - 300}+0")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def on_move(self, event):
        self.root.geometry(f"+{event.x_root - self.x}+{event.y_root - self.y}")

    def snap_to_corner(self):
        screen_width = self.root.winfo_screenwidth()
        win_x = self.root.winfo_x()
        win_width = 300

        if win_x < screen_width / 2:
            self.root.geometry(f"+0+0")  # Snap to top-left
        else:
            self.root.geometry(f"+{screen_width - win_width}+0")  # Snap to top-right

    def stop_move(self, event):
        self.snap_to_corner()
        self.save_position()


root = tk.Tk()
app = FloatingWidget(root)
root.mainloop()
