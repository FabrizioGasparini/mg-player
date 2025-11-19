import os
from tkinter import *
from tkinter import filedialog, messagebox, ttk, Tk
from pygame import mixer
import cv2
from PIL import Image, ImageTk
from glob import glob
import threading
import time

class MGPlayer:
    def __init__(self, root: Tk):
        self.root = root
        self.root.title("MG Player")
        self.root.geometry("1100x650")
        self.root.configure(bg="#1e1e1e")

        self.video_files = []
        self.audio_files = []

        self.current_video_index = None
        self.current_music_index = None
        self.video_stop_event = threading.Event()
        self.music_stop_event = threading.Event()

        mixer.init()

        self.video_thread = None
        self.music_thread = None

        self.config_ui()
        self.create_ui()
        self.update_controls_state()

    def config_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e1e")
        style.configure("TLabel", background="#1e1e1e", foreground="#dddddd", font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 14, "bold"), foreground="#ffffff", background="#2b2b2b")
        style.configure("TButton", font=("Segoe UI", 10))
        style.map("TButton",
                  foreground=[("active", "#ffffff")],
                  background=[("active", "#3a86ff")])
        style.configure("Treeview",
                        background="#2b2b2b",
                        fieldbackground="#2b2b2b",
                        foreground="#ffffff",
                        rowheight=22,
                        font=("Segoe UI", 10))
        style.map("Treeview", background=[("selected", "#3a86ff")], foreground=[("selected", "#ffffff")])

    def create_ui(self):
        # Barra del titolo
        self.topbar = Frame(self.root, bg="#1e1e1e", height=80, width=200)
        self.topbar.pack(side=TOP, anchor=CENTER)

        self.logo_label = Label(self.topbar, bg="#1e1e1e")
        self.logo_label.pack(side=LEFT, padx=10, pady=10)

        img = Image.open(".\mg_player_logo.png").convert("RGBA")
        max_h = 64
        w, h = img.size
        ratio = max_h / float(h)
        new_w = int(w * ratio)
        img = img.resize((new_w, max_h), Image.LANCZOS)
        self.logo_imgtk = ImageTk.PhotoImage(img)
        self.logo_label.configure(image=self.logo_imgtk, bg="#1e1e1e")

        # Frame titolo e sottotitolo
        title_frame = Frame(self.topbar, bg="#2b2b2b")
        title_frame.pack(side=LEFT, padx=10)
        title = ttk.Label(title_frame, text="MG Player", style="Header.TLabel")
        title.pack(anchor=W)
        subtitle = ttk.Label(title_frame, text="Carica cartelle di video e musica e premi Play", font=("Segoe UI", 9), foreground="#cccccc", background="#2b2b2b")
        subtitle.pack(anchor=W)

        # Frame principale
        self.content = Frame(self.root, bg="#1e1e1e")
        self.content.pack(fill=BOTH, expand=True, padx=12, pady=12)

        # Colonna video
        self.left = Frame(self.content, bg="#1e1e1e")
        self.left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0,6))

        label_video = ttk.Label(self.left, text="Videos")
        label_video.pack(anchor=W)

        v_tree_frame = Frame(self.left, bg="#1e1e1e")
        v_tree_frame.pack(fill=BOTH, expand=True)
        self.video_tree = ttk.Treeview(v_tree_frame, show='tree', selectmode='browse')
        v_scroll = ttk.Scrollbar(v_tree_frame, orient=VERTICAL, command=self.video_tree.yview)
        self.video_tree.configure(yscrollcommand=v_scroll.set)
        self.video_tree.pack(side=LEFT, fill=BOTH, expand=True)
        v_scroll.pack(side=LEFT, fill=Y)
        self.video_tree.bind("<<TreeviewSelect>>", self.on_video_select)
        
        # alterna i colori delle righe
        self.video_tree.tag_configure('odd', background='#2b2b2b')
        self.video_tree.tag_configure('even', background='#232323')

        load_video_button_frame = Frame(self.left, bg="#1e1e1e")
        load_video_button_frame.pack(fill=X, pady=8)
        ttk.Button(load_video_button_frame, text="Load Video Folder", command=self.load_video_folder).pack(side=LEFT, padx=4)
        ttk.Button(load_video_button_frame, text="Clear Selection", command=self.clear_video_selection).pack(side=LEFT, padx=4)

        # Colonna musica
        self.right = Frame(self.content, bg="#1e1e1e")
        self.right.pack(side=LEFT, fill=BOTH, expand=True, padx=(6,0))

        label_music = ttk.Label(self.right, text="Music")
        label_music.pack(anchor=W)

        m_tree_frame = Frame(self.right, bg="#1e1e1e")
        m_tree_frame.pack(fill=BOTH, expand=True)
        self.music_tree = ttk.Treeview(m_tree_frame, show='tree', selectmode='browse')
        m_scroll = ttk.Scrollbar(m_tree_frame, orient=VERTICAL, command=self.music_tree.yview)
        self.music_tree.configure(yscrollcommand=m_scroll.set)
        self.music_tree.pack(side=LEFT, fill=BOTH, expand=True)
        m_scroll.pack(side=LEFT, fill=Y)
        self.music_tree.bind("<<TreeviewSelect>>", self.on_music_select)

        # alterna i colori delle righe
        self.music_tree.tag_configure('odd', background='#2b2b2b')
        self.music_tree.tag_configure('even', background='#232323')

        load_button_frame = Frame(self.right, bg="#1e1e1e")
        load_button_frame.pack(fill=X, pady=8)
        ttk.Button(load_button_frame, text="Load Music Folder", command=self.load_music_folder).pack(side=LEFT, padx=4)
        ttk.Button(load_button_frame, text="Clear Selection", command=self.clear_music_selection).pack(side=LEFT, padx=4)

        # Center controls and large play/stop buttons
        self.ctrl_frame = Frame(self.root, bg="#1e1e1e")
        self.ctrl_frame.pack(fill=X, pady=(0,8))

        self.play_button = ttk.Button(self.ctrl_frame, text="► Play", command=self.play, width=20)
        self.play_button.pack(side=LEFT, padx=10)
        self.stop_button = ttk.Button(self.ctrl_frame, text="■ Stop", command=self.stop, width=20)
        self.stop_button.pack(side=LEFT, padx=10)

        self.status_label = ttk.Label(self.ctrl_frame, text="Ready", font=("Segoe UI", 9))
        self.status_label.pack(side=LEFT, padx=10)

        # Frame dove viene riprodotti il video
        self.video_panel = Frame(self.root, bg="#000000", bd=2, relief=RIDGE)
        self.video_panel.pack(fill=BOTH, expand=True, padx=12, pady=(0,12))
        self.video_label = Label(self.video_panel, bg="#000000")
        self.video_label.pack(fill=BOTH, expand=True)

        # Canvas per visualizzare le onde audio
        self.wave_canvas = Canvas(self.video_panel, bg="#000000", highlightthickness=0)

    def load_video_folder(self):
        # Chiede una cartella all'utente contente file
        folder = filedialog.askdirectory(title="Select Video Folder")
        if not folder:
            return
        # Cerca solo file in estensione .mp4
        self.video_files = sorted(glob(os.path.join(folder, "*.mp4")))
        self.populate_video_list()
        self.current_video_index = None
        self.clear_video_selection()
        self.update_controls_state()

    def populate_video_list(self):
        self.video_tree.delete(*self.video_tree.get_children())
        for i, f in enumerate(self.video_files):
            tag = 'even' if (i % 2 == 0) else 'odd'
            self.video_tree.insert('', 'end', text=os.path.basename(f), tags=(tag,))

    def load_music_folder(self):
        # Chiede all'utente la cartella con gli audio
        folder = filedialog.askdirectory(title="Select Music Folder")
        if not folder:
            return
        # Prende solo i file .mp3
        self.music_files = sorted(glob(os.path.join(folder, "*.mp3")))
        self.populate_music_list()
        self.current_music_index = None
        self.clear_music_selection()
        self.update_controls_state()

    def populate_music_list(self):
        self.music_tree.delete(*self.music_tree.get_children())
        for i, f in enumerate(self.music_files):
            tag = 'even' if (i % 2 == 0) else 'odd'
            self.music_tree.insert('', 'end', text=os.path.basename(f), tags=(tag,))

    def on_video_select(self, event):
        sel = self.video_tree.selection()
        if sel:
            self.current_video_index = int(self.video_tree.index(sel[0]))
        else:
            self.current_video_index = None
        self.update_controls_state()

    def on_music_select(self, event):
        sel = self.music_tree.selection()
        if sel:
            self.current_music_index = int(self.music_tree.index(sel[0]))
        else:
            self.current_music_index = None
        self.update_controls_state()

    def clear_video_selection(self):
        for s in self.video_tree.selection():
            self.video_tree.selection_remove(s)
        self.current_video_index = None
        self.update_controls_state()

    def clear_music_selection(self):
        for s in self.music_tree.selection():
            self.music_tree.selection_remove(s)
        self.current_music_index = None
        self.update_controls_state()

    def get_mode(self):
        if self.current_video_index is not None and self.current_music_index is not None:
            return "both"
        if self.current_video_index is not None:
            return "video"
        if self.current_music_index is not None:
            return "music"
        return None

    def update_controls_state(self):
        mode = self.get_mode()
        if mode is None:
            self.play_button.state(["disabled"])
            self.status_label.config(text="Select a video and/or music to enable Play")
        else:
            self.play_button.state(["!disabled"])
            if mode == "both":
                self.status_label.config(text="Mode: Play Both (video + music)")
            elif mode == "video":
                self.status_label.config(text="Mode: Play Video Only (loop)")
            else:
                self.status_label.config(text="Mode: Play Music Only")

    def hide_ui_for_play(self):
        # nasconde topbar, tutte le liste e il tasto play, lascia solo il tasto stop
        try:
            self.topbar.pack_forget()
            self.content.pack_forget()
        except Exception:
            pass
        try:
            self.play_button.pack_forget()
            self.status_label.pack_forget()
            self.stop_button.pack_forget()
            self.stop_button.pack(side=LEFT, padx=10)
        except Exception:
            pass

    def restore_ui(self):
        # mostra di nuovo bar le liste e tutto il resto
        try:
            self.topbar.pack(fill=X, side=TOP)
            self.content.pack(fill=BOTH, expand=True, padx=12, pady=12)
        except Exception:
            pass

        try:
            for w in self.ctrl_frame.winfo_children():
                w.pack_forget()
            self.play_button.pack(side=LEFT, padx=10)
            self.stop_button.pack(side=LEFT, padx=10)
            self.status_label.pack(side=LEFT, padx=10)
        except Exception:
            pass

    def play(self):
        mode = self.get_mode()
        if mode is None:
            messagebox.showinfo("Info", "Nessun file selezionato.")
            return

        self.stop()
        self.status_label.config(text="Playing...")

        self.hide_ui_for_play()

        if mode in ("both", "video") and self.current_video_index is not None:
            try:
                self.wave_canvas.pack_forget()
            except Exception:
                pass
            if not self.video_label.winfo_ismapped():
                self.video_label.pack(fill=BOTH, expand=True)
            self.video_stop_event.clear()
            loop = (mode == "video")
            self.video_thread = threading.Thread(target=self.play_video, args=(loop,), daemon=True)
            self.video_thread.start()

        if mode in ("both", "music") and self.current_music_index is not None:
            if mode == "music":
                try:
                    self.video_label.pack_forget()
                except Exception:
                    pass
                self.wave_canvas.pack(fill=BOTH, expand=True)
                #self._start_wave_animation()
            self.music_stop_event.clear()
            self.music_thread = threading.Thread(target=self.play_music, daemon=True)
            self.music_thread.start()

    def stop(self):
        self.video_stop_event.set()
        self.music_stop_event.set()
        try:
            mixer.music.stop()
        except Exception:
            pass
        #self._stop_wave_animation()

        self.status_label.config(text="Stopped")

        def clear():
            try:
                self.video_label.configure(image="")
                self.video_label.imgtk = None
            except Exception:
                pass
        try:
            self.video_label.after(0, clear)
        except Exception:
            pass

        self.restore_ui()
        try:
            self.wave_canvas.pack_forget()
            if not self.video_label.winfo_ismapped():
                self.video_label.pack(fill=BOTH, expand=True)
        except Exception:
            pass

    def play_video(self, loop=False):
        if not self.video_files or self.current_video_index is None:
            return

        video_path = self.video_files[self.current_video_index]
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            self.status_label.config(text="Cannot open video")
            return

        # usa gli FPS massimi possibili dati da cv oppure 30 se cv non li fornisce
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        delay = 1.0 / fps

        while not self.video_stop_event.is_set() and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                if loop:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break

            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            panel_w = self.video_label.winfo_width() or 800
            panel_h = self.video_label.winfo_height() or 400
            h, w = frame.shape[:2]
            ratio = min(panel_w / w, panel_h / h)
            new_size = (max(1, int(w * ratio)), max(1, int(h * ratio)))
            frame_resized = cv2.resize(frame, new_size, interpolation=cv2.INTER_AREA)

            img = Image.fromarray(frame_resized)
            imgtk = ImageTk.PhotoImage(image=img)

            def update(imgtk=imgtk):
                self.video_label.imgtk = imgtk
                self.video_label.configure(image=imgtk)
            try:
                self.video_label.after(0, update)
            except Exception:
                pass

            time.sleep(delay)

        cap.release()
        def clear():
            try:
                self.video_label.configure(image="")
                self.video_label.imgtk = None
            except Exception:
                pass
        try:
            self.video_label.after(0, clear)
        except Exception:
            pass

    def play_music(self):
        if not self.music_files or self.current_music_index is None:
            return
        music_path = self.music_files[self.current_music_index]
        try:
            mixer.music.load(music_path)
            mixer.music.play()
            while mixer.music.get_busy() and not self.music_stop_event.is_set():
                time.sleep(0.2)
            mixer.music.stop()
        except Exception:
            pass
        # stop wave when music ends
        #self._stop_wave_animation()
        if not (self.video_thread and self.video_thread.is_alive()):
            try:
                self.status_label.config(text="Stopped")
            except Exception:
                pass

if __name__ == "__main__":
    root = Tk()
    logo_path = r".\mg_player_logo.png"  # esempio: modifica a tuo piacere
    app = MGPlayer(root)
    root.mainloop()