import requests
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
import tkinter as tk
from tkinter import messagebox, ttk
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import textwrap
import numpy as np
from PIL import Image, ImageSequence
import os
import sys


def create_gui():
    root = tk.Tk()
    root.title("Weather App")

    # create a style object
    style = ttk.Style()
    style.theme_use('default')

    # create input field for location
    location_label = ttk.Label(root, text="Enter your location:")
    location_label.pack()
    location_entry = ttk.Entry(root)
    location_entry.pack()

    # create buttons for each type of weather information
    radar_button = ttk.Button(root, text="Radar", command=lambda: display_radar(location_entry))
    radar_button.pack()
    forecast_button = ttk.Button(root, text="7-Day Forecast", command=lambda: display_forecast(location_entry,
                                                                                               weather_text))
    forecast_button.pack()
    current_button = ttk.Button(root, text="Current Weather", command=lambda: display_current(location_entry,
                                                                                              weather_text))
    current_button.pack()
    alert_button = ttk.Button(root, text="Alerts", command=lambda: display_alerts(location_entry, weather_text))
    alert_button.pack()

    # create a frame to hold the weather label and scrollbar
    frame = tk.Frame(root)
    frame.pack()

    # create a scrollbar for the frame
    scrollbar = ttk.Scrollbar(frame)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    # create a text widget to display weather data
    weather_text = tk.Text(frame, width=70, height=20, wrap=tk.WORD)
    weather_text.pack(side=tk.LEFT)

    # configure the scrollbar and text widget
    scrollbar.config(command=weather_text.yview)
    weather_text.config(yscrollcommand=scrollbar.set)

    try:
        root.mainloop()
    except KeyboardInterrupt:
        delete_radar_gif(radar_gif_path)
        sys.exit(0)


def get_lat_lon(location):
    geolocator = Nominatim(user_agent="weather_app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    try:
        location_data = geocode(location)
        lat = location_data.latitude
        lon = location_data.longitude
        return lat, lon
    except:
        return None

    
def get_weather_data(lat, lon):
    base_url = "https://api.weather.gov/"
    point_url = f"points/{lat},{lon}"
    response = requests.get(base_url + point_url)
    if response.status_code == 200:
        data = response.json()
        forecast_url = data["properties"]["forecast"]
        forecast_response = requests.get(forecast_url)
        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()

            # Retrieve radar station from the original response
            radar_station = data["properties"]["radarStation"]
            forecast_data["properties"]["radarStation"] = radar_station

            return forecast_data
        else:
            print(f"Failed to retrieve forecast data. Status code: {forecast_response.status_code}")
    else:
        print(f"Failed to retrieve point data. Status code: {response.status_code}")
    return None


radar_gif_path = ""


def display_radar(location_entry):
    location = location_entry.get()
    if location:
        lat_lon = get_lat_lon(location)
        if lat_lon:
            lat, lon = lat_lon
            weather_data = get_weather_data(lat, lon)
            if weather_data:
                properties = weather_data.get('properties', {})
                radar_station = properties.get('radarStation')
                if radar_station:
                    radar_image_url = f"https://radar.weather.gov/ridge/standard/{radar_station}_loop.gif"
                    print('THIS IS THE URL', radar_image_url)
                    response = requests.get(radar_image_url)
                    if response.status_code == 200:
                        radar_gif_path = f"{radar_station}_loop.gif"
                        with open(radar_gif_path, "wb") as f:
                            f.write(response.content)

                        # Read the radar image as a sequence of frames
                        radar_image = Image.open(f"{radar_station}_loop.gif")
                        frames = [frame.convert('RGBA') for frame in ImageSequence.Iterator(radar_image)]

                        # Create the basemap
                        fig = plt.figure(figsize=(6, 6))
                        m = Basemap()
                        m.set_axes_limits(False)

                        # Overlay each frame on the basemap
                        for frame in frames:
                            frame_array = np.array(frame)
                            m.imshow(frame_array, origin='upper', extent=[m.llcrnrx, m.urcrnrx, m.llcrnry, m.urcrnry])

                        # Display the basemap with radar overlay
                        plt.show(block=False)

                        # Call delete_radar_gif() when the basemap window is closed
                        fig.canvas.mpl_connect('close_event', lambda event: delete_radar_gif(radar_gif_path))
                    else:
                        messagebox.showerror("Error", "Failed to download radar image")
                else:
                    messagebox.showerror("Error", "No radar station found in the weather data")
            else:
                messagebox.showerror("Error", "Failed to retrieve weather data")
        else:
            messagebox.showerror("Error", "Could not geocode location")
    else:
        messagebox.showerror("Error", "Please enter a location")


def delete_radar_gif(radar_gif_path):
    if os.path.isfile(radar_gif_path):
        os.remove(radar_gif_path)


def display_current(location_entry, weather_text):
    location = location_entry.get()
    if location:
        lat_lon = get_lat_lon(location)
        if lat_lon:
            lat, lon = lat_lon
            weather_data = get_weather_data(lat, lon)
            if weather_data:
                current = weather_data["properties"]["periods"][0]
                current_str = f"{current['name']}: {current['temperature']}°F, {current['shortForecast']}\n"
                weather_text.delete(1.0, tk.END)  # Clear previous text
                weather_text.insert(tk.END, current_str)
            else:
                messagebox.showinfo("Error", "Error retrieving weather data")
        else:
            messagebox.showerror("Error", "Could not geocode location")
    else:
        messagebox.showerror("Error", "Please enter a location")


def display_forecast(location_entry, weather_text):
    location = location_entry.get()
    if location:
        lat_lon = get_lat_lon(location)
        if lat_lon:
            lat, lon = lat_lon
            weather_data = get_weather_data(lat, lon)
            if weather_data:
                periods = weather_data["properties"]["periods"]
                forecast_str = ""
                for period in periods:
                    wrapped_forecast = textwrap.fill(period['detailedForecast'], width=70)  # Adjust the width as needed
                    forecast_str += f"{period['name']}\n{wrapped_forecast}\n\n"
                weather_text.delete(1.0, tk.END)
                weather_text.insert(tk.END, forecast_str)
            else:
                messagebox.showinfo("Error", "Error retrieving weather data")
        else:
            messagebox.showerror("Error", "Could not geocode location")
    else:
        messagebox.showerror("Error", "Please enter a location")


def display_alerts(location_entry, weather_text):
    location = location_entry.get()
    if location:
        lat_lon = get_lat_lon(location)
        if lat_lon:
            lat, lon = lat_lon
            zone_url = f"https://api.weather.gov/points/{lat},{lon}"
            zone_response = requests.get(zone_url)
            if zone_response.status_code == 200:
                zone_data = zone_response.json()
                zone_id = zone_data["properties"]["forecastZone"]
                zone_id_parts = zone_id.split('/')
                last_part = zone_id_parts[-1]
                alerts_url = f"https://api.weather.gov/alerts/active?zone={last_part}"
                alerts_response = requests.get(alerts_url)
                if alerts_response.status_code == 200:
                    alerts_data = alerts_response.json()
                    alerts = alerts_data["features"]
                    if alerts:
                        alert_str = ""
                        for alert in alerts:
                            event = alert["properties"]["event"]
                            description = alert["properties"]["description"]
                            severity = alert["properties"]["severity"]
                            alert_str += f"Title: {event}\n"
                            alert_str += f"Description: {description}\n"
                            alert_str += f"Severity: {severity}\n"
                            alert_str += "-------------------------\n"
                        weather_text.delete(1.0, tk.END) 
                        weather_text.insert(tk.END, alert_str)
                    else:
                        weather_text.delete(1.0, tk.END)  # Clear previous text
                        weather_text.insert(tk.END, 'No alerts found')
                else:
                    messagebox.showinfo("Error", f"Error retrieving alerts data. Status code:"
                                                 f" {alerts_response.status_code}")
            else:
                messagebox.showinfo("Error", "Error retrieving zone data.")
        else:
            messagebox.showerror("Error", "Could not geocode location")
    else:
        messagebox.showerror("Error", "Please enter a location")


create_gui()
