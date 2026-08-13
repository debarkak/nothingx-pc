#!/usr/bin/env python3
import customtkinter as ctk
import threading
import time
import traceback
from nothingx.device import Device, DeviceNotFoundError

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class NothingXGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Nothing X PC")
        self.geometry("500x750")
        self.resizable(False, False)
        
        self.configure(fg_color="#000000")

        self.ear = None
        self.device_lock = threading.Lock()
        self.fetching = False

        self.build_ui()
        
        threading.Thread(target=self.connect_and_poll, daemon=True).start()

    def build_ui(self):
        # Header
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.pack(pady=(20, 10), padx=20, fill="x")
        
        self.title_lbl = ctk.CTkLabel(self.header_frame, text="Nothing X", font=("Arial", 28, "bold"))
        self.title_lbl.pack(side="left")
        
        self.dev_name_lbl = ctk.CTkLabel(self.header_frame, text="Connecting...", font=("Arial", 14), text_color="gray")
        self.dev_name_lbl.pack(side="right", pady=(10, 0))

        # Battery Section
        self.bat_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1c1c1e")
        self.bat_frame.pack(pady=10, padx=20, fill="x")
        
        self.bat_frame.grid_columnconfigure((0,1,2), weight=1)
        
        self.l_bat_lbl = ctk.CTkLabel(self.bat_frame, text="L\n--%", font=("Arial", 16, "bold"))
        self.l_bat_lbl.grid(row=0, column=0, pady=20)
        
        self.c_bat_lbl = ctk.CTkLabel(self.bat_frame, text="Case\n--%", font=("Arial", 16, "bold"))
        self.c_bat_lbl.grid(row=0, column=1, pady=20)
        
        self.r_bat_lbl = ctk.CTkLabel(self.bat_frame, text="R\n--%", font=("Arial", 16, "bold"))
        self.r_bat_lbl.grid(row=0, column=2, pady=20)

        # ANC Section
        self.anc_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1c1c1e")
        self.anc_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.anc_frame, text="Noise Control", font=("Arial", 16, "bold")).pack(pady=(15,5), padx=15, anchor="w")
        
        self.anc_var = ctk.StringVar(value="off")
        # Use an OptionMenu instead of segmented button to avoid layout truncation
        self.anc_dropdown = ctk.CTkOptionMenu(self.anc_frame, 
                                              values=["high", "mid", "low", "adaptive", "transparency", "off"],
                                              variable=self.anc_var,
                                              command=self.on_anc_change,
                                              state="disabled",
                                              dynamic_resizing=False,
                                              width=200)
        self.anc_dropdown.pack(pady=(0, 15), padx=15, anchor="w")

        # Toggles Section (In-Ear, Low Lag)
        self.toggles_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1c1c1e")
        self.toggles_frame.pack(pady=10, padx=20, fill="x")
        
        # In-Ear
        self.inear_var = ctk.BooleanVar(value=False)
        self.inear_switch = ctk.CTkSwitch(self.toggles_frame, text="In-Ear Detection", font=("Arial", 14),
                                          variable=self.inear_var, command=self.on_inear_change, state="disabled")
        self.inear_switch.pack(pady=15, padx=15, anchor="w")
        
        # Low Lag
        self.lag_var = ctk.BooleanVar(value=False)
        self.lag_switch = ctk.CTkSwitch(self.toggles_frame, text="Low Lag Mode", font=("Arial", 14),
                                        variable=self.lag_var, command=self.on_lag_change, state="disabled")
        self.lag_switch.pack(pady=(0,15), padx=15, anchor="w")

        # Enhanced Bass
        self.bass_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1c1c1e")
        self.bass_frame.pack(pady=10, padx=20, fill="x")
        
        self.bass_var = ctk.BooleanVar(value=False)
        self.bass_switch = ctk.CTkSwitch(self.bass_frame, text="Enhanced Bass", font=("Arial", 14),
                                         variable=self.bass_var, command=self.on_bass_toggle, state="disabled")
        self.bass_switch.pack(pady=(15,10), padx=15, anchor="w")
        
        self.bass_slider = ctk.CTkSlider(self.bass_frame, from_=1, to=5, number_of_steps=4,
                                         command=self.on_bass_slider, state="disabled")
        self.bass_slider.pack(pady=(0,15), padx=15, fill="x")
        self.bass_slider.set(1)
        self.bass_lvl_lbl = ctk.CTkLabel(self.bass_frame, text="Level: 1", font=("Arial", 12))
        self.bass_lvl_lbl.pack(pady=(0, 10))

        # Find Earbuds
        self.find_frame = ctk.CTkFrame(self, corner_radius=15, fg_color="#1c1c1e")
        self.find_frame.pack(pady=10, padx=20, fill="x")
        
        ctk.CTkLabel(self.find_frame, text="Find Earbuds", font=("Arial", 16, "bold")).pack(pady=(15,5), padx=15, anchor="w")
        
        find_btn_frame = ctk.CTkFrame(self.find_frame, fg_color="transparent")
        find_btn_frame.pack(pady=(0,15), padx=15, fill="x")
        
        self.btn_find_l = ctk.CTkButton(find_btn_frame, text="Left", command=lambda: self.on_find("left"), state="disabled")
        self.btn_find_l.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_find_r = ctk.CTkButton(find_btn_frame, text="Right", command=lambda: self.on_find("right"), state="disabled")
        self.btn_find_r.pack(side="left", padx=5, expand=True, fill="x")
        
        self.btn_find_stop = ctk.CTkButton(find_btn_frame, text="Stop", fg_color="#b22222", hover_color="#8b0000", command=lambda: self.on_find("stop"), state="disabled")
        self.btn_find_stop.pack(side="right", padx=5, expand=True, fill="x")

    def _ui_update_connected(self, dev_name):
        self.dev_name_lbl.configure(text=dev_name)
        self.anc_dropdown.configure(state="normal")
        self.inear_switch.configure(state="normal")
        self.lag_switch.configure(state="normal")
        self.bass_switch.configure(state="normal")
        self.bass_slider.configure(state="normal")
        self.btn_find_l.configure(state="normal")
        self.btn_find_r.configure(state="normal")
        self.btn_find_stop.configure(state="normal")

    def _ui_update_disconnected(self):
        self.dev_name_lbl.configure(text="Disconnected")
        self.anc_dropdown.configure(state="disabled")
        self.inear_switch.configure(state="disabled")
        self.lag_switch.configure(state="disabled")
        self.bass_switch.configure(state="disabled")
        self.bass_slider.configure(state="disabled")
        self.btn_find_l.configure(state="disabled")
        self.btn_find_r.configure(state="disabled")
        self.btn_find_stop.configure(state="disabled")

    def connect_and_poll(self):
        try:
            self.ear = Device.discover()
            self.after(0, self._ui_update_connected, self.ear.name)
            
            while True:
                self.fetch_state()
                time.sleep(5)
        except Exception as e:
            self.after(0, self._ui_update_disconnected)
            print(f"Connection error: {e}")

    def fetch_state(self):
        if not self.ear or self.fetching:
            return
        
        self.fetching = True
        try:
            with self.device_lock:
                # Fetch data synchronously in this background thread
                b = self.ear.battery()
                l_str = f"L\n{b.left}%" if b.left > 0 else "L\n--%"
                r_str = f"R\n{b.right}%" if b.right > 0 else "R\n--%"
                c_str = f"Case\n{b.case}%" if b.case else "Case\n--%"
                
                anc_mode = self.ear.anc.get()
                inear_state = self.ear.inear.get()
                latency_state = self.ear.latency.get()
                bass_info = self.ear.bass.get()

            # Prepare UI update package
            state = {
                "l_bat": l_str,
                "r_bat": r_str,
                "c_bat": c_str,
                "anc": anc_mode,
                "inear": inear_state,
                "latency": latency_state,
                "bass": bass_info
            }
            # Schedule UI update on main thread
            self.after(0, self.update_ui_state, state)
                    
        except Exception as e:
            print(f"Error fetching state: {e}")
        finally:
            self.fetching = False

    def update_ui_state(self, state):
        # Update Battery labels
        self.l_bat_lbl.configure(text=state["l_bat"])
        self.r_bat_lbl.configure(text=state["r_bat"])
        self.c_bat_lbl.configure(text=state["c_bat"])
        
        # Update variables
        if state["anc"] != "unknown":
            self.anc_var.set(state["anc"])
        
        self.inear_var.set(state["inear"])
        self.lag_var.set(state["latency"])
        
        self.bass_var.set(state["bass"]["enabled"])
        if state["bass"]["enabled"]:
            self.bass_slider.set(state["bass"]["level"])
            self.bass_lvl_lbl.configure(text=f"Level: {state['bass']['level']}")
        else:
            self.bass_lvl_lbl.configure(text=f"Level: --")

    def on_anc_change(self, value):
        def _run():
            with self.device_lock:
                try:
                    if value == "high": self.ear.anc.high()
                    elif value == "mid": self.ear.anc.mid()
                    elif value == "low": self.ear.anc.low()
                    elif value == "adaptive": self.ear.anc.adaptive()
                    elif value == "transparency": self.ear.anc.transparency()
                    elif value == "off": self.ear.anc.off()
                except Exception as e:
                    print(f"ANC change failed: {e}")
            self.fetch_state()
        threading.Thread(target=_run).start()

    def on_inear_change(self):
        val = self.inear_var.get()
        def _run():
            with self.device_lock:
                try:
                    self.ear.inear.set(val)
                except Exception as e:
                    print(f"In-ear set failed: {e}")
            self.fetch_state()
        threading.Thread(target=_run).start()

    def on_lag_change(self):
        val = self.lag_var.get()
        def _run():
            with self.device_lock:
                try:
                    self.ear.latency.set(val)
                except Exception as e:
                    print(f"Lag set failed: {e}")
            self.fetch_state()
        threading.Thread(target=_run).start()

    def on_bass_toggle(self):
        val = self.bass_var.get()
        lvl = int(self.bass_slider.get())
        def _run():
            with self.device_lock:
                try:
                    if val:
                        self.ear.bass.on(lvl)
                    else:
                        self.ear.bass.off()
                except Exception as e:
                    print(f"Bass toggle failed: {e}")
            self.fetch_state()
        threading.Thread(target=_run).start()

    def on_bass_slider(self, value):
        if not self.bass_var.get():
            return
        lvl = int(value)
        self.bass_lvl_lbl.configure(text=f"Level: {lvl}")
        def _run():
            with self.device_lock:
                try:
                    self.ear.bass.on(lvl)
                except Exception as e:
                    print(f"Bass slider failed: {e}")
            self.fetch_state()
        threading.Thread(target=_run).start()

    def on_find(self, side):
        def _run():
            with self.device_lock:
                try:
                    if side == "left": self.ear.find.left()
                    elif side == "right": self.ear.find.right()
                    elif side == "stop": self.ear.find.stop()
                except Exception as e:
                    print(f"Find {side} failed: {e}")
        threading.Thread(target=_run).start()

if __name__ == "__main__":
    app = NothingXGUI()
    app.mainloop()
