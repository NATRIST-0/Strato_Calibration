#!/usr/bin/python3
# author: Tristan Gayrard

"""
Strato_Cal_multi-slider Combined Script
"""

import tkinter as tk
from tkinter import Text, filedialog
from tkinter import ttk
import sys
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, TextBox
import pandas as pd

def convert_time_from_start(start_time, current_time):
    time_diff = current_time - start_time
    time_in_hours = time_diff.total_seconds() / 3600
    return time_in_hours

def load_file():
    file_path = filedialog.askopenfilename(filetypes=[("Text files", "*.txt")])
    if file_path:
        file_label.config(text=file_path)
        return file_path
    return None

def send():
    gas_str = selected_gas.get()
    dil_str = dil_text.get("1.0", "end-1c").strip()
    error_label.config(text="")

    if gas_str and dil_str:
        try:
            gas = gas_str
            dil_val = int(dil_str)
            if not (3 <= dil_val <= 6):
                raise ValueError("Number of dilutions must be between 3 and 6")
            file_path = file_label.cget("text")
            if not file_path:
                error_label.config(text="Please load a file", foreground="red")
                return
            # Run visualization code
            visualize(file_path, gas, dil_val)
        except ValueError as e:
            error_label.config(text=str(e), foreground="red")
    else:
        error_label.config(text="Please enter values for both calibration gas and number of dilutions", foreground="red")

def visualize(file_path, gas_name, num_dilutions):
    # Load data
    data = pd.read_csv(file_path, delimiter=',')
    data['Time'] = pd.to_datetime(data['Time Stamp'])
    start_time = data['Time'].min()
    data['Time_from_start'] = data['Time'].apply(lambda x: convert_time_from_start(start_time, x))
    Date, time = data.iloc[1, 0].split(" ")

    # Check if gas_name is in data columns
    if gas_name not in data.columns:
        print(f"Error: '{gas_name}' not found in the data columns.")
        return

    gas = data[gas_name]

    # Create figure and axes
    fig, axes = plt.subplots(nrows=1, ncols=2)
    plt.subplots_adjust(bottom=0.4)

    # Initialize plot and sliders
    line, = axes[0].plot(data['Time_from_start'], gas, color='blue', alpha=0.5)
    highlights = []

    # Function to update slider highlights
    def update(val):
        for i, slider in enumerate(sliders):
            start = int(slider.val)
            end = start + 30
            highlights[i].set_xdata(data['Time_from_start'][start:end])
            highlights[i].set_ydata(gas[start:end])
            # Update slider value label
            slider.valtext.set_text(f"{np.mean(gas[start:end]):.2f}")
        fig.canvas.draw_idle()

    def update_sliders(val):
        update(None)

    # Set labels and title
    axes[0].set_xlabel('Date and Time')
    axes[0].set_ylabel(f'{gas_name}')
    axes[0].grid(True)
    axes[0].set_title(f'{gas_name} Calibration Raw Data from {Date}')

    # Create sliders and highlights
    sliders = []
    colors = ['red', 'green', 'orange', 'purple', 'deepskyblue', 'darkgreen']
    for i in range(num_dilutions):
        ax_slider = plt.axes([0.085 if i < 3 else 0.38, 0.25 - 0.05 * (i % 3), 0.2, 0.03], facecolor='lightgoldenrodyellow')
        slider = Slider(ax_slider, f'{i+1}th Dilution\n', 0, len(data['Time_from_start']) - 30, valinit=0, color=colors[i])
        sliders.append(slider)
        highlight, = axes[0].plot(data['Time_from_start'][:30], gas[:30], 'o', color=colors[i], markersize=5)
        highlights.append(highlight)
        slider.on_changed(update_sliders)

    # Set up the TextBox widgets for dilution concentrations
    dilution_boxes = []
    for i in range(num_dilutions):
        ax_box = plt.axes([0.75, 0.3 - 0.05 * i, 0.15, 0.03])
        box = TextBox(ax_box, f'Dil {i+1} Concentration =', initial="")
        dilution_boxes.append(box)

    # Function to handle submission from TextBox widgets
    def submit(event):
        try:
            concentrations = [float(box.text) for box in dilution_boxes[:len(sliders)]]
            avg_values = [np.mean(gas[int(slider.val):int(slider.val) + 30]) for slider in sliders]

            # Perform linear regression
            x = np.array(concentrations)
            y = np.array(avg_values)
            coeffs = np.polyfit(x, y, 1)
            line_fit = np.polyval(coeffs, x)

            # Calculate R squared
            correlation_matrix = np.corrcoef(x, y)
            correlation_xy = correlation_matrix[0, 1]
            r_squared = correlation_xy ** 2

            # Clear the second axes
            axes[1].clear()

            # Plot the average values against concentrations
            axes[1].plot(x, y, 'o', label='Data')

            # Plot the regression line
            axes[1].plot(x, line_fit, label='Linear Regression', color='red')

            # Display the equation of the line and R squared
            equation = f'y = {coeffs[0]:.5f}x + {coeffs[1]:.5f}'
            r_squared_text = f'R² = {r_squared:.5f}'
            axes[1].text(0.05, 0.95, equation, transform=axes[1].transAxes, fontsize=10, verticalalignment='top')
            axes[1].text(0.05, 0.90, r_squared_text, transform=axes[1].transAxes, fontsize=10, verticalalignment='top')

            # Set labels and title for the second plot
            axes[1].set_xlabel(f'Theoretical {gas_name}')
            axes[1].set_ylabel(f'Measured {gas_name}')
            axes[1].set_title(f'{gas_name} Calibration from {Date}')

            # Draw the plot
            plt.draw()
        except ValueError:
            print("Please enter valid concentrations for all dilutions.")

    # Connect the submit function to TextBox widgets
    for box in dilution_boxes:
       
        box.on_submit(submit)
        
        plt.ion()
        plt.show()

def on_close():
    root.destroy()
    sys.exit()

root = tk.Tk()
root.title("Strato Cal Home Screen")
root.geometry("700x150")

style = ttk.Style()
style.theme_use('clam')

frame = ttk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

load_button = ttk.Button(frame, text="Load File", command=load_file)
load_button.grid(row=0, column=0, padx=10, pady=5)

file_label = ttk.Label(frame, text="", font=('Sans-serif', 12))
file_label.grid(row=0, column=1, padx=10, pady=5, columnspan=4)

selected_gas = tk.StringVar(frame)
selected_gas.set('Select a Calibration Gas')
gas_label = ttk.OptionMenu(frame, selected_gas, 'Select a Calibration Gas', 'N2O (ppm)', 'CO2(ppm)', 'CH4 (ppm)', 'C2H6 (ppb)')
gas_label.grid(row=1, column=0, padx=10, pady=5)

dil_label = ttk.Label(frame, text="Number of dilutions = ", font=('Sans-serif', 12))
dil_label.grid(row=1, column=2, padx=10, pady=5)
dil_text = Text(frame, height=1, width=7, font=('Sans-serif', 12))
dil_text.grid(row=1, column=3, padx=10, pady=5)

send_button = ttk.Button(frame, text="Send", command=send)
send_button.grid(row=1, column=4, padx=10, pady=5)

error_label = ttk.Label(frame, text="", font=('Sans-serif', 12))
error_label.grid(row=2, column=0, padx=10, pady=5, columnspan=5)

signature = ttk.Label(frame, text="By : Tristan Gayrard 👍😎", font=('Sans-serif', 7))
signature.grid(row=3, column=0, padx=10, pady=1, columnspan=1)


root.protocol("WM_DELETE_WINDOW", on_close)
root.mainloop()
