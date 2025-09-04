import os
import sys
import json
from secrets import randbelow
from string import ascii_uppercase
from string import ascii_lowercase
import tkinter as tk
from tkinter import messagebox, filedialog

# Constants and mappings
FALLBACK_CODE = 67
SPACE_PLACEHOLDER = "§"

decimal = list(range(100))  # 0-99
sign = [str(x) for x in range(10)] + list(ascii_uppercase) + list(ascii_lowercase) + [
    ".", ",", "!", "?", "_", SPACE_PLACEHOLDER, "ß", "$", "&", "%", '"', "(", ")", "-", "{", "}", "[", "]", "*", "/", "+", "Ä",
    "Ü", "=", "²", "<", ">", ";", ":", "~", "#", "@", "Ö", "°", "^", "ö", "ä", "ü"
]
mastercode = dict(zip(sign, decimal))
masterdecode = dict(zip(decimal, sign))

codes_global = {}  # store generated/loaded codes

# --- Tkinter setup ---

root = tk.Tk()
root.title("Zablos Secret Sharer V3")

# Frame for menu buttons
frame_menu = tk.Frame(root)
frame_menu.pack(padx=10, pady=5, fill="x")

# Frame for dynamic content (input fields, outputs)
frame_content = tk.Frame(root)
frame_content.pack(padx=10, pady=5, fill="both", expand=True)

# Frame for output display
frame_output = tk.Frame(root)
frame_output.pack(padx=10, pady=5, fill="both", expand=True)

output_text = tk.Text(frame_output, height=12, wrap="word")
output_text.pack(fill="both", expand=True)
output_text.config(state=tk.DISABLED)

# Store code entries for decoding input
code_entries = {}

# --- Utility functions ---

def clear_content_frame():
    for widget in frame_content.winfo_children():
        widget.destroy()

def clear_output():
    output_text.config(state=tk.NORMAL)
    output_text.delete(1.0, tk.END)
    output_text.config(state=tk.DISABLED)

def append_output(text):
    output_text.config(state=tk.NORMAL)
    output_text.insert(tk.END, text + "\n")
    output_text.config(state=tk.DISABLED)
    output_text.see(tk.END)

def clear_all():
    clear_content_frame()
    clear_output()
    code_entries.clear()

# --- Menu button commands ---

def show_mastercode():
    clear_all()
    append_output("Mastercode (decimal->char):")
    append_output(str(masterdecode))
    append_output("\nMastercode (char->decimal):")
    append_output(str(mastercode))

def check_int_dialog():
    # Simple dialog for number of shares (2-99)
    from tkinter.simpledialog import askinteger
    shares = askinteger("Shares count", "Enter shares count (2-99):", minvalue=2, maxvalue=99)
    if shares is None:
        return 2
    return shares

def translate_into_mastercode_gui():
    clear_all()
    shares = check_int_dialog()
    if not shares:
        return

    # Message input
    clear_content_frame()

    tk.Label(frame_content, text="Message (spaces allowed):").grid(row=0, column=0, sticky='w')
    message_entry = tk.Entry(frame_content, width=50)
    message_entry.grid(row=0, column=1, sticky='w')
    message_entry.focus_set()

    tk.Label(frame_content, text=f"Code1/{shares}:").grid(row=1, column=0, sticky='w')
    code1_entry = tk.Entry(frame_content, width=50)
    code1_entry.grid(row=1, column=1, sticky='w')

    def on_submit():
        message = message_entry.get()
        ucc_input = code1_entry.get()

        # Replace spaces in code1 silently with §
        c1str = ucc_input.replace(" ", SPACE_PLACEHOLDER)

        # Translate message to mastercode decimals (spaces kept as spaces in display)
        messageMaster = [mastercode.get(ch if ch != " " else SPACE_PLACEHOLDER, FALLBACK_CODE) for ch in message]
        UccMaster = [mastercode.get(ch if ch != " " else SPACE_PLACEHOLDER, FALLBACK_CODE) for ch in c1str]

        if len(messageMaster) < len(UccMaster):
            # pad messageMaster with FALLBACK_CODE
            messageMaster += [FALLBACK_CODE] * (len(UccMaster) - len(messageMaster))
        elif len(messageMaster) > len(UccMaster):
            messagebox.showerror("Error", "Code is too short!")
            return

        codes_global.clear()
        codes_global['C1'] = list(c1str)

        clear_output()
        append_output(f"Code1/{shares}: {c1str}")

        if shares == 2:
            # Code 2 is messageMaster + (-1)*UccMaster mod 100
            UccNeg = [-x for x in UccMaster]
            c2 = [(m + u) % 100 for m, u in zip(messageMaster, UccNeg)]
            code2_list = [masterdecode[x] for x in c2]
            codes_global['C2'] = code2_list
            code2_str = ''.join(code2_list)
            append_output(f"Code2/2: {code2_str}")
        else:
            # More shares: generate random shares and last code
            pseudo_random_numbers(messageMaster, UccMaster, shares)

    btn = tk.Button(frame_content, text="Generate Codes", command=on_submit)
    btn.grid(row=2, column=1, sticky='w', pady=5)

def pseudo_random_numbers(messageMaster, UccMaster, shares):
    global codes_global
    random_codes = {}
    count = len(UccMaster)
    for x in range(2, shares):
        key = f'C{x}'
        value = [randbelow(100) for _ in range(count)]
        random_codes[key] = value
    last_code(messageMaster, random_codes, UccMaster, shares)

def last_code(messageMaster, random_codes, UccMaster, shares):
    global codes_global
    count = len(UccMaster)

    for i in range(2, shares):
        key = f'C{i}'
        templist = random_codes[key]
        codes_global[key] = [masterdecode[y] for y in templist]
        messageOut = ''.join(codes_global[key])
        append_output(f'Code{i}/{shares}: {messageOut}')

    # sum across random codes for each position
    mdtemp = list(zip(*random_codes.values()))
    copylist = [sum(l) for l in mdtemp]

    finalSum = [(m + c) for m, c in zip(copylist, UccMaster)]
    copylist = [x % 100 for x in finalSum]

    last_code_list = [((m - c) % 100) for m, c in zip(messageMaster, copylist)]

    last_code_chars = [masterdecode[x] for x in last_code_list]

    codes_global[f'C{shares}'] = last_code_chars
    messageOut = ''.join(last_code_chars)
    append_output(f'Code{shares}/{shares}: {messageOut}')

def decode_message_gui():
    clear_all()
    shares = check_int_dialog()
    if not shares:
        return

    clear_content_frame()
    tk.Label(frame_content, text=f"Enter {shares} codes below (spaces not allowed):").grid(row=0, column=0, columnspan=2, sticky='w')

    global code_entries
    code_entries.clear()

    for i in range(1, shares + 1):
        tk.Label(frame_content, text=f"Code{i}:").grid(row=i, column=0, sticky='w')
        entry = tk.Entry(frame_content, width=50)
        entry.grid(row=i, column=1, sticky='w')
        code_entries[i] = entry

    def on_decode():
        codes = {}
        for i in range(1, shares + 1):
            val = code_entries[i].get()
            if " " in val:
                messagebox.showerror("Input Error", "Codes must not contain spaces. Use '§' instead.")
                return
            codes[f'C{i}'] = list(val)

        if shares <= 1:
            messagebox.showerror("Error", "At least 2 shares are required.")
            return

        copylist = []
        md = list(zip(*codes.values()))

        for l in md:
            temp = sum(mastercode.get(v, FALLBACK_CODE) for v in l) % 100
            copylist.append(temp)

        messageOut = ''.join(masterdecode[x] for x in copylist)
        messageOut = messageOut.replace(SPACE_PLACEHOLDER, " ")
        append_output(f"\nDecoded Message:\n{messageOut}")

    btn = tk.Button(frame_content, text="Decode", command=on_decode)
    btn.grid(row=shares + 1, column=1, sticky='w', pady=5)

def generate_otp_gui():
    clear_all()
    clear_content_frame()

    from tkinter.simpledialog import askinteger

    count = askinteger("OTP length", "Enter code length:", minvalue=1)
    if count is None:
        return

    while True:
        range_low = askinteger("Range start", "Enter code start#:", minvalue=1)
        if range_low is None:
            return
        range_high = askinteger("Range end", "Enter code last#:", minvalue=range_low)
        if range_high is None:
            return
        if range_low <= range_high:
            break

    random_codes = {}
    for x in range(range_low, range_high + 1):
        key = f'C{x}'
        value = [randbelow(100) for _ in range(count)]
        random_codes[key] = value

    codes_global.clear()
    clear_output()
    for key, templist in random_codes.items():
        codes_global[key] = [masterdecode[y] for y in templist]
        code_str = ''.join(codes_global[key])
        append_output(f'{key}: {code_str}')


# --- Save / Load with file dialogs and drag & drop support ---

save_filename_var = tk.StringVar()
load_filename_var = tk.StringVar()

def show_save_codes():
    clear_all()

    tk.Label(frame_content, text="Select filename to save (.json):").grid(row=0, column=0, sticky='e')
    filename_label = tk.Label(frame_content, textvariable=save_filename_var, width=40, anchor='w', relief='sunken')
    filename_label.grid(row=0, column=1, sticky='w')

    def browse_save_file():
        file = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if file:
            save_filename_var.set(file)

    browse_btn = tk.Button(frame_content, text="Browse...", command=browse_save_file)
    browse_btn.grid(row=0, column=2, sticky='w', padx=5)

    def on_save():
        if not codes_global:
            messagebox.showinfo("Info", "No codes generated or loaded yet to save.")
            return
        filename = save_filename_var.get()
        if not filename:
            messagebox.showerror("Error", "Please select a filename to save.")
            return
        try:
            with open(filename, "w") as f:
                json.dump(codes_global, f, indent=4)
            messagebox.showinfo("Success", f"Codes saved to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file: {e}")

    save_btn = tk.Button(frame_content, text="Save Codes", command=on_save)
    save_btn.grid(row=1, column=1, sticky='w', pady=5)

def show_load_codes():
    clear_all()

    tk.Label(frame_content, text="Select filename to load (.json):").grid(row=0, column=0, sticky='e')
    filename_label = tk.Label(frame_content, textvariable=load_filename_var, width=40, anchor='w', relief='sunken')
    filename_label.grid(row=0, column=1, sticky='w')

    def browse_load_file():
        file = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file:
            load_filename_var.set(file)
            load_codes_from_json()

    browse_btn = tk.Button(frame_content, text="Browse...", command=browse_load_file)
    browse_btn.grid(row=0, column=2, sticky='w', padx=5)

    # Enable drag & drop on filename label if possible
    try:
        import tkinterdnd2
        # Initialize root as TkinterDnD.Tk() if needed outside this snippet for full drag & drop
        filename_label.drop_target_register('*')
        def on_drop(event):
            files = root.tk.splitlist(event.data)
            for f in files:
                if f.endswith(".json"):
                    load_filename_var.set(f)
                    load_codes_from_json()
                    break
        filename_label.dnd_bind('<<Drop>>', on_drop)
    except ImportError:
        pass

def load_codes_from_json():
    global codes_global
    filename = load_filename_var.get()
    if not filename:
        messagebox.showerror("Error", "Please select a filename to load.")
        return
    try:
        with open(filename, "r") as f:
            loaded = json.load(f)
        codes_global = loaded
        clear_output()
        append_output("[Loaded Codes]:")
        for key, val in codes_global.items():
            code_str = ''.join(val)
            append_output(f"{key}: {code_str}")
        # Fill decode entries if open
        for i in range(1, 100):
            key = f'C{i}'
            if key in codes_global and i in code_entries:
                code_entries[i].delete(0, tk.END)
                code_entries[i].insert(0, ''.join(codes_global[key]))
        messagebox.showinfo("Success", f"Codes loaded from {filename}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load file: {e}")

# --- Main menu buttons ---

btn_split = tk.Button(frame_menu, text="(S)plit", width=8, command=translate_into_mastercode_gui)
btn_split.pack(side=tk.LEFT, padx=2)

btn_combine = tk.Button(frame_menu, text="(C)ombine", width=8, command=decode_message_gui)
btn_combine.pack(side=tk.LEFT, padx=2)

btn_master = tk.Button(frame_menu, text="(M)astercode", width=10, command=show_mastercode)
btn_master.pack(side=tk.LEFT, padx=2)

btn_otp = tk.Button(frame_menu, text="(O)TP", width=8, command=generate_otp_gui)
btn_otp.pack(side=tk.LEFT, padx=2)

btn_wipe = tk.Button(frame_menu, text="(W)ipe", width=8, command=clear_all)
btn_wipe.pack(side=tk.LEFT, padx=2)

btn_save = tk.Button(frame_menu, text="Sa(V)e", width=8, command=show_save_codes)
btn_save.pack(side=tk.LEFT, padx=2)

btn_load = tk.Button(frame_menu, text="(L)oad", width=8, command=show_load_codes)
btn_load.pack(side=tk.LEFT, padx=2)

def on_quit():
    if messagebox.askyesno("Quit", "Are you sure you want to quit?"):
        root.destroy()
        sys.exit()

btn_quit = tk.Button(frame_menu, text="(Q)uit", width=8, command=on_quit)
btn_quit.pack(side=tk.LEFT, padx=2)


# Run the GUI
root.mainloop()
