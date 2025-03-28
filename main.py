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

        self.todo_frame = tk.Frame(self.root, bg="black")
        self.todo_frame.pack(fill="both", expand=True)

        self.todos = self.load_todos()
        self.update_todo_list()

        button_frame = tk.Frame(self.root, bg="black")
        button_frame.pack(side="bottom", fill="x")

        self.toggle_button = tk.Button(button_frame, text="Not On Top", command=self.toggle_on_top,
                                       bg="blue", fg="white")
        self.toggle_button.pack(side="left", fill="both", expand=True)

        self.add_todo_button = tk.Button(button_frame, text="Add To-Do", command=self.add_todo, bg="green", fg="white")
        self.add_todo_button.pack(side="left", fill="both", expand=True)

        self.close_button = tk.Button(button_frame, text="X", command=self.close_app, bg="red", fg="white",
                                      font=("Arial", 12, "bold"))
        self.close_button.pack(side="right", fill="both", expand=True)

        self.root.bind("<ButtonPress-1>", self.start_move)
        self.root.bind("<B1-Motion>", self.on_move)
        self.root.bind("<ButtonRelease-1>", self.stop_move)

        self.reset_time = "06:00:00"
        self.check_reset_time()

        self.on_top = self.load_on_top_state()
        self.set_on_top(self.on_top)
        self.restore_position()

    def close_app(self):
        self.root.quit()
        self.root.destroy()

    def update_todo_list(self):
        for widget in self.todo_frame.winfo_children():
            widget.destroy()

        for i, todo in enumerate(self.todos):
            todo_frame = tk.Frame(self.todo_frame, bg="black")
            todo_frame.pack(fill="x", pady=2, anchor="w")

            if 'var' not in todo:
                todo['var'] = tk.IntVar(value=0)

            canvas = tk.Canvas(todo_frame, width=24, height=24, bd=0, highlightthickness=0, bg="black")
            canvas.pack(side="left", padx=5, anchor="w")
            canvas.create_oval(2, 2, 22, 22, fill="red", outline="red")

            if todo['checked']:
                canvas.create_oval(2, 2, 22, 22, fill="green", outline="green")
            else:
                canvas.create_oval(2, 2, 22, 22, fill="white", outline="white")

            canvas.bind("<Button-1>", lambda event, idx=i: self.toggle_rectangle(idx))

            label = tk.Label(todo_frame, text=todo['task'], fg="white", bg="black", font=("Arial", 10), anchor="w",
                             width=21)
            label.pack(side="left", fill="x", anchor="w")

            label.update_idletasks()

            delete_icon = PhotoImage(file="delete_icon.png")
            delete_icon = delete_icon.subsample(12, 12)
            delete_label = tk.Label(todo_frame, image=delete_icon, bg="black", width=20, height=20)
            delete_label.photo = delete_icon
            delete_label.pack(side="right", padx=(0, 5))

            delete_label.bind("<Button-1>", lambda event, idx=i: self.delete_todo(idx))

            move_up_icon = PhotoImage(file="up.png")
            move_up_icon = move_up_icon.subsample(12, 12)
            move_up_label = tk.Label(todo_frame, image=move_up_icon, bg="black", width=20, height=20)
            move_up_label.photo = move_up_icon
            move_up_label.pack(side="right", padx=5)

            move_up_label.bind("<Button-1>", lambda event, idx=i: self.move_up(idx))

            move_down_icon = PhotoImage(file="down.png")
            move_down_icon = move_down_icon.subsample(12, 12)
            move_down_label = tk.Label(todo_frame, image=move_down_icon, bg="black", width=20, height=20)
            move_down_label.photo = move_down_icon
            move_down_label.pack(side="right")

            move_down_label.bind("<Button-1>", lambda event, idx=i: self.move_down(idx))

        self.todo_frame.update_idletasks()
        self.adjust_window_height()

    def move_up(self, idx):
        if idx > 0:  # Can't move up the first item
            self.todos[idx], self.todos[idx - 1] = self.todos[idx - 1], self.todos[idx]
            self.save_todos()
            self.update_todo_list()

    def move_down(self, idx):
        if idx < len(self.todos) - 1:  # Can't move down the last item
            self.todos[idx], self.todos[idx + 1] = self.todos[idx + 1], self.todos[idx]
            self.save_todos()
            self.update_todo_list()

    def adjust_window_height(self):
        todo_count = len(self.todos)
        if todo_count == 0:
            estimated_height = 58
        else:
            estimated_height = 28 * todo_count + 30
        self.root.geometry(f"300x{estimated_height}+1000+10")
        self.snap_to_corner()

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
        self.on_top = not self.on_top
        self.set_on_top(self.on_top)
        self.save_on_top_state(self.on_top)

    def set_on_top(self, on_top):
        if on_top:
            self.root.wm_attributes("-topmost", True)
            self.toggle_button.config(text="Not On Top")
        else:
            self.root.wm_attributes("-topmost", False)
            self.toggle_button.config(text="On Top")

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
                widget.delete("all")
                if todo['checked']:
                    widget.create_oval(2, 2, 22, 22, fill="green", outline="green")
                else:
                    widget.create_oval(2, 2, 22, 22, fill="white", outline="white")

    def delete_todo(self, idx):
        del self.todos[idx]
        self.save_todos()
        self.update_todo_list()

    def save_todos(self):
        serializable_todos = [{'task': todo['task'], 'checked': todo['checked']} for todo in self.todos]

        # Get the path to the user's AppData folder
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'TODO Float')
        os.makedirs(app_data_dir, exist_ok=True)

        todos_pickle = os.path.join(app_data_dir, 'todos.pkl')

        with open(todos_pickle, "wb") as f:
            pickle.dump(serializable_todos, f)

    def load_todos(self):
        # Get the path to the user's AppData folder
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'TODO Float')
        todos_pickle = os.path.join(app_data_dir, 'todos.pkl')

        if os.path.exists(todos_pickle):
            try:
                with open(todos_pickle, "rb") as f:
                    if os.path.getsize(todos_pickle) > 0:
                        todos = pickle.load(f)
                        for todo in todos:
                            if 'var' not in todo:
                                todo['var'] = tk.IntVar(value=1 if todo['checked'] else 0)
                        return todos
            except (EOFError, pickle.UnpicklingError):
                return []
        return []

    def save_on_top_state(self, on_top):
        # Get the path to the user's AppData folder
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'TODO Float')
        os.makedirs(app_data_dir, exist_ok=True)

        on_top_pickle = os.path.join(app_data_dir, 'window_on_top.pkl')

        with open(on_top_pickle, "wb") as f:
            pickle.dump(on_top, f)

    def load_on_top_state(self):
        # Get the path to the user's AppData folder
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'TODO Float')
        on_top_pickle = os.path.join(app_data_dir, 'window_on_top.pkl')

        if os.path.exists(on_top_pickle):
            try:
                with open(on_top_pickle, "rb") as f:
                    return pickle.load(f)
            except (EOFError, pickle.UnpicklingError):
                return False
        return False

    def save_position(self):
        self.root.update_idletasks()
        position = (self.root.winfo_x(), self.root.winfo_y(), self.root.winfo_width(), self.root.winfo_height())

        # Get the path to the user's AppData folder
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'TODO Float')
        os.makedirs(app_data_dir, exist_ok=True)

        position_pickle = os.path.join(app_data_dir, 'window_position.pkl')

        with open(position_pickle, "wb") as f:
            pickle.dump(position, f)

    def restore_position(self):
        screen_width = self.root.winfo_screenwidth()

        # Get the path to the user's AppData folder
        app_data_dir = os.path.join(os.getenv('APPDATA'), 'TODO Float')
        position_pickle = os.path.join(app_data_dir, 'window_position.pkl')

        if os.path.exists(position_pickle):
            try:
                with open(position_pickle, "rb") as f:
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
