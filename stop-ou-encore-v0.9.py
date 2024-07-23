import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
import tkinter as tk
from tkinter import filedialog, messagebox, Menu, ttk
import shutil
from PIL import Image, ImageTk

class GameApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Stop ou Encore")
        self.root.geometry("1400x800")  # Adjusted size to fit all elements

        self.accepted_games = []
        self.rejected_games = []
        self.hold_games = []
        self.games = []
        self.filtered_games = []
        self.duplicates = set()
        self.current_index = 0
        self.system_name = ""
        self.filter_mode = "All"
        self.letter_filter = None

        self.setup_ui()
        self.create_menu()

        # Show message on startup
        messagebox.showinfo("Welcome", "Please select a game directory to start")

    def setup_ui(self):
        self.letter_buttons_frame = tk.Frame(self.root)
        self.letter_buttons_frame.grid(row=0, column=0, rowspan=6, sticky="ns")

        self.listbox_frame = tk.Frame(self.root)
        self.listbox_frame.grid(row=0, column=1, rowspan=6, sticky="ns")

        self.scrollbar = tk.Scrollbar(self.listbox_frame, orient=tk.VERTICAL)
        self.listbox = tk.Listbox(self.listbox_frame, width=50, yscrollcommand=self.scrollbar.set)
        self.scrollbar.config(command=self.listbox.yview)

        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.listbox.bind("<<ListboxSelect>>", self.on_game_select)

        self.name_label = tk.Label(self.root, text="", font=("Helvetica", 16), wraplength=300)
        self.name_label.grid(row=0, column=2, sticky="w")

        self.filename_label = tk.Label(self.root, text="", font=("Helvetica", 12), wraplength=300)
        self.filename_label.grid(row=1, column=2, sticky="w")

        self.region_label = tk.Label(self.root, text="", font=("Helvetica", 12))
        self.region_label.grid(row=2, column=2, sticky="w")

        self.image_label = tk.Label(self.root)
        self.image_label.grid(row=3, column=2)

        self.desc_text = tk.Text(self.root, height=10, width=50, wrap=tk.WORD)
        self.desc_text.grid(row=4, column=2, sticky="w")

        self.button_frame = tk.Frame(self.root)
        self.button_frame.grid(row=5, column=2, pady=10)

        self.accept_button = tk.Button(self.button_frame, text="Accept (A)", command=self.accept_game, bg="green")
        self.accept_button.grid(row=0, column=0, padx=5)

        self.reject_button = tk.Button(self.button_frame, text="Reject (R)", command=self.reject_game, bg="red")
        self.reject_button.grid(row=0, column=1, padx=5)

        self.hold_button = tk.Button(self.button_frame, text="Hold (H)", command=self.hold_game, bg="orange")
        self.hold_button.grid(row=0, column=2, padx=5)

        # Add letter buttons
        self.add_letter_buttons()

        # Add counters
        self.counter_frame = tk.Frame(self.root)
        self.counter_frame.grid(row=0, column=3, rowspan=6, sticky="ns")

        self.total_games_label = tk.Label(self.counter_frame, text="Total games: 0", font=("Helvetica", 12))
        self.total_games_label.pack()

        self.accepted_games_label = tk.Label(self.counter_frame, text="Accepted games: 0", font=("Helvetica", 12))
        self.accepted_games_label.pack()

        self.rejected_games_label = tk.Label(self.counter_frame, text="Rejected games: 0", font=("Helvetica", 12))
        self.rejected_games_label.pack()

        self.hold_games_label = tk.Label(self.counter_frame, text="On hold games: 0", font=("Helvetica", 12))
        self.hold_games_label.pack()

        self.untagged_games_label = tk.Label(self.counter_frame, text="Untagged games: 0", font=("Helvetica", 12))
        self.untagged_games_label.pack()

        # Key bindings
        self.root.bind('<a>', lambda event: self.accept_game())
        self.root.bind('<r>', lambda event: self.reject_game())
        self.root.bind('<h>', lambda event: self.hold_game())

    def disable_key_bindings(self, event):
        self.root.unbind('<a>')
        self.root.unbind('<r>')
        self.root.unbind('<h>')

    def enable_key_bindings(self, event):
        self.root.bind('<a>', lambda event: self.accept_game())
        self.root.bind('<r>', lambda event: self.reject_game())
        self.root.bind('<h>', lambda event: self.hold_game())

    def add_letter_buttons(self):
        # Add "All" and "0-9" buttons
        all_button = tk.Button(self.letter_buttons_frame, text="All", command=lambda: self.filter_by_letter(None))
        all_button.grid(row=0, column=0, sticky="ew")

        num_button = tk.Button(self.letter_buttons_frame, text="0-9", command=lambda: self.filter_by_letter("0-9"))
        num_button.grid(row=1, column=0, sticky="ew")

        # Add letter buttons
        for i, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ", start=2):
            button = tk.Button(self.letter_buttons_frame, text=letter, command=lambda l=letter: self.filter_by_letter(l))
            button.grid(row=i, column=0, sticky="ew")

    def filter_by_letter(self, letter):
        self.letter_filter = letter
        self.update_listbox()

    def create_menu(self):
        menu = Menu(self.root)
        self.root.config(menu=menu)

        file_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Load New Gamelist", command=self.load_console_directory)
        file_menu.add_separator()
        file_menu.add_command(label="Save Progress", command=self.save_progress)
        file_menu.add_command(label="Load Progress", command=self.load_progress)
        file_menu.add_separator()
        file_menu.add_command(label="Export Accepted Games", command=self.export_games)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        filter_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="Filter", menu=filter_menu)
        filter_menu.add_command(label="All", command=lambda: self.set_filter_mode("All"))
        filter_menu.add_command(label="Accepted", command=lambda: self.set_filter_mode("Accepted"))
        filter_menu.add_command(label="Rejected", command=lambda: self.set_filter_mode("Rejected"))
        filter_menu.add_command(label="On Hold", command=lambda: self.set_filter_mode("On Hold"))
        filter_menu.add_command(label="No Selection", command=lambda: self.set_filter_mode("No Selection"))

        about_menu = Menu(menu, tearoff=0)
        menu.add_cascade(label="About", menu=about_menu)
        about_menu.add_command(label="About", command=self.show_about)

    def show_about(self):
        messagebox.showinfo("About", "Coded by Joao Gomes with the help of ChatGPT")

    def set_filter_mode(self, mode):
        self.filter_mode = mode
        self.update_listbox()

    def load_console_directory(self):
        self.console_dir = filedialog.askdirectory(title="Select Console Directory")
        if not self.console_dir:
            messagebox.showerror("Error", "No directory selected!")
            return

        self.gamelist_path = os.path.join(self.console_dir, 'gamelist.xml')
        if not os.path.exists(self.gamelist_path):
            messagebox.showerror("Error", f"No gamelist.xml found in {self.console_dir}")
            return

        self.system_name = os.path.basename(self.console_dir)
        self.load_gamelist()

    def load_gamelist(self):
        tree = ET.parse(self.gamelist_path)
        root = tree.getroot()

        self.games = []
        self.accepted_games = []
        self.rejected_games = []
        self.hold_games = []
        self.duplicates = set()
        self.current_index = 0
        self.listbox.delete(0, tk.END)

        for game in root.findall('game'):
            game_data = {}
            for elem in game:
                game_data[elem.tag] = elem.text
            self.games.append(game_data)

        self.find_duplicates()
        self.update_listbox()
        self.update_counters()
        self.show_game(0)  # Ensure the first game is shown correctly

    def find_duplicates(self):
        seen = {}
        self.duplicates = set()
        for game in self.games:
            if game['name'] in seen:
                self.duplicates.add(game['name'])
                self.duplicates.add(seen[game['name']])
            else:
                seen[game['name']] = game['name']

    def load_progress(self):
        progress_file = os.path.join(self.console_dir, f"{self.system_name}_progress.txt")
        if os.path.exists(progress_file):
            with open(progress_file, 'r') as file:
                lines = file.readlines()
                section = None
                for line in lines:
                    line = line.strip()
                    if line == "Accepted:":
                        section = "accepted"
                    elif line == "Rejected:":
                        section = "rejected"
                    elif line == "On Hold:":
                        section = "hold"
                    elif section == "accepted":
                        for game in self.games:
                            if game['path'] == line:
                                self.accepted_games.append(game)
                                break
                    elif section == "rejected":
                        for game in self.games:
                            if game['path'] == line:
                                self.rejected_games.append(game)
                                break
                    elif section == "hold":
                        for game in self.games:
                            if game['path'] == line:
                                self.hold_games.append(game)
                                break
        self.update_listbox()
        self.update_counters()

    def save_progress(self):
        progress_file = os.path.join(self.console_dir, f"{self.system_name}_progress.txt")
        if os.path.exists(progress_file):
            result = messagebox.askyesno("Warning", "Progress file already exists. Do you want to overwrite it?")
            if not result:
                return

        with open(progress_file, 'w') as file:
            file.write("Accepted:\n")
            for game in self.accepted_games:
                file.write(f"{game['path']}\n")
            file.write("\nRejected:\n")
            for game in self.rejected_games:
                file.write(f"{game['path']}\n")
            file.write("\nOn Hold:\n")
            for game in self.hold_games:
                file.write(f"{game['path']}\n")

    def on_game_select(self, event):
        w = event.widget
        if w.curselection():
            index = int(w.curselection()[0])
            self.current_index = index
            self.show_game(index)

    def show_game(self, index):
        if index < 0 or index >= len(self.filtered_games):
            return

        game = self.filtered_games[index]
        self.name_label.config(text=f"Name: {game['name']}")
        self.filename_label.config(text=f"Filename: {game['path']}")
        self.region_label.config(text=f"Region: {game.get('region', 'Unknown')}")
        self.desc_text.delete(1.0, tk.END)
        self.desc_text.insert(tk.END, game.get('desc', 'No description available'))

        if game.get('image') and os.path.exists(os.path.join(self.console_dir, game['image'])):
            image_path = os.path.join(self.console_dir, game['image'])
            image = Image.open(image_path)
            image.thumbnail((300, 300))  # Increased image size
            photo = ImageTk.PhotoImage(image)
            self.image_label.configure(image=photo)
            self.image_label.image = photo
        else:
            self.image_label.configure(image=None)
            self.image_label.image = None

        self.update_listbox_colors()

    def accept_game(self):
        if not self.filtered_games:
            return
        game = self.filtered_games[self.current_index]
        if game not in self.accepted_games:
            self.accepted_games.append(game)
        if game in self.rejected_games:
            self.rejected_games.remove(game)
        if game in self.hold_games:
            self.hold_games.remove(game)
        self.update_listbox_colors()
        self.update_counters()
        self.next_game()

    def reject_game(self):
        if not self.filtered_games:
            return
        game = self.filtered_games[self.current_index]
        if game not in self.rejected_games:
            self.rejected_games.append(game)
        if game in self.accepted_games:
            self.accepted_games.remove(game)
        if game in self.hold_games:
            self.hold_games.remove(game)
        self.update_listbox_colors()
        self.update_counters()
        self.next_game()

    def hold_game(self):
        if not self.filtered_games:
            return
        game = self.filtered_games[self.current_index]
        if game not in self.hold_games:
            self.hold_games.append(game)
        if game in self.accepted_games:
            self.accepted_games.remove(game)
        if game in self.rejected_games:
            self.rejected_games.remove(game)
        self.update_listbox_colors()
        self.update_counters()
        self.next_game()

    def next_game(self):
        if self.current_index < len(self.filtered_games) - 1:
            self.current_index += 1
            self.listbox.select_clear(0, tk.END)
            self.listbox.select_set(self.current_index)
            self.listbox.event_generate("<<ListboxSelect>>")

    def update_listbox(self):
        self.filtered_games = []
        self.listbox.delete(0, tk.END)
        for game in self.games:
            if self.letter_filter == "0-9" and not game['name'][0].isdigit():
                continue
            if self.letter_filter and self.letter_filter != "0-9" and not game['name'].startswith(self.letter_filter):
                continue
            if self.filter_mode == "All":
                self.filtered_games.append(game)
                self.listbox.insert(tk.END, game['name'])
            elif self.filter_mode == "Accepted" and game in self.accepted_games:
                self.filtered_games.append(game)
                self.listbox.insert(tk.END, game['name'])
            elif self.filter_mode == "Rejected" and game in self.rejected_games:
                self.filtered_games.append(game)
                self.listbox.insert(tk.END, game['name'])
            elif self.filter_mode == "On Hold" and game in self.hold_games:
                self.filtered_games.append(game)
                self.listbox.insert(tk.END, game['name'])
            elif self.filter_mode == "No Selection" and game not in self.accepted_games and game not in self.rejected_games and game not in self.hold_games:
                self.filtered_games.append(game)
                self.listbox.insert(tk.END, game['name'])
        self.update_listbox_colors()

    def update_listbox_colors(self):
        for i, game in enumerate(self.filtered_games):
            bg = 'white'
            if game['name'] in self.duplicates:
                if game in self.accepted_games:
                    bg = 'green'
                elif game in self.rejected_games:
                    bg = 'red'
                elif game in self.hold_games:
                    bg = 'orange'
                else:
                    bg = 'pink'
            elif game in self.accepted_games:
                bg = 'green'
            elif game in self.rejected_games:
                bg = 'red'
            elif game in self.hold_games:
                bg = 'orange'
            if i == self.current_index:
                bg = 'yellow'
            self.listbox.itemconfig(i, {'bg': bg})

    def update_counters(self):
        total_games = len(self.games)
        accepted_games = len(self.accepted_games)
        rejected_games = len(self.rejected_games)
        hold_games = len(self.hold_games)
        untagged_games = total_games - accepted_games - rejected_games - hold_games

        self.total_games_label.config(text=f"Total games: {total_games}")
        self.accepted_games_label.config(text=f"Accepted games: {accepted_games}")
        self.rejected_games_label.config(text=f"Rejected games: {rejected_games}")
        self.hold_games_label.config(text=f"On hold games: {hold_games}")
        self.untagged_games_label.config(text=f"Untagged games: {untagged_games}")

    def export_games(self):
        if not self.accepted_games:
            messagebox.showerror("Error", "No accepted games to export!")
            return

        export_dir = filedialog.askdirectory(title="Select Export Directory")
        if not export_dir:
            messagebox.showerror("Error", "No directory selected!")
            return

        # Create the export progress window
        self.progress_window = tk.Toplevel(self.root)
        self.progress_window.title("Export Progress")
        self.progress_window.geometry("500x100")

        self.progress_label = tk.Label(self.progress_window, text="Starting export...")
        self.progress_label.pack(pady=10)

        self.progress_bar = ttk.Progressbar(self.progress_window, orient="horizontal", length=400, mode="determinate")
        self.progress_bar.pack(pady=10)
        self.progress_bar["maximum"] = len(self.accepted_games)
        self.progress_bar["value"] = 0

        export_gamelist_path = os.path.join(export_dir, 'gamelist.xml')
        root = ET.Element('gameList')

        for i, game in enumerate(self.accepted_games):
            game_element = ET.SubElement(root, 'game')
            for key, value in game.items():
                ET.SubElement(game_element, key).text = value

                # Copy game files and images
                game_path = os.path.join(self.console_dir, game['path'])
                if key in ['image', 'video', 'marquee', 'thumbnail', 'manual', 'rating', 'fanart', 'boxart']:
                    file_path = os.path.join(self.console_dir, value)
                    if os.path.exists(file_path):
                        self.progress_label.config(text=f"Copying: {value}")
                        self.progress_bar.update()
                        self.copy_file(file_path, export_dir)
                elif os.path.exists(game_path):
                    self.progress_label.config(text=f"Copying: {game['path']}")
                    self.progress_bar.update()
                    self.copy_file(game_path, export_dir)

            self.progress_bar["value"] += 1
            self.progress_bar.update()

        xml_str = ET.tostring(root, encoding='utf-8')
        parsed_str = minidom.parseString(xml_str)
        pretty_str = parsed_str.toprettyxml(indent="  ")

        with open(export_gamelist_path, 'w', encoding='utf-8') as f:
            f.write(pretty_str)

        self.progress_label.config(text="Export Complete")
        messagebox.showinfo("Export Complete", "Accepted games have been exported successfully!")
        self.progress_window.destroy()

    def copy_file(self, src, dest_dir):
        rel_path = os.path.relpath(src, self.console_dir)
        dest_path = os.path.join(dest_dir, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy(src, dest_path)

if __name__ == "__main__":
    root = tk.Tk()
    app = GameApp(root)
    root.mainloop()
