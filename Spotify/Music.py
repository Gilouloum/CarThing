from tkinter import Tk, Label, Canvas, PhotoImage, StringVar, Button, Frame
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import io
import os

# Spotify API Credentials
CLIENT_ID = "0d1d1fc0abae4092b1c31bcbb270b037"
CLIENT_SECRET = "ea422221f9a74bc9a4b23adbb68048e2"
REDIRECT_URI = "http://localhost:8888/callback"

# Scope for Spotify Controls
SCOPE = "user-read-playback-state user-modify-playback-state user-read-currently-playing"

# Initialize Spotify Client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    redirect_uri=REDIRECT_URI,
    scope=SCOPE,
    cache_path=".spotify_cache"
))


class SpotifyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Controller")
        self.root.geometry("450x450")
        self.root.configure(bg=None)

        # Create a canvas for the blurred background
        self.canvas = Canvas(self.root, width=450, height=450)
        self.canvas.pack()

        # Album Art Label
        self.canvas.configure(bg=None)  # Or match the background to the app
        self.album_art_label = Label(self.root, bg=None)

        self.album_art_label.place(x=100, y=60)  # Positioning the album art higher

        # Current Track Info
        self.current_track = StringVar()
        self.current_track.set("No track playing")
        self.track_label = Label(self.root, textvariable=self.current_track, font=("Helvetica", 12), wraplength=400, bg="#1A1A1A", fg="white")
        self.track_label.place(x=60, y=315)  # Position track label below album art, above buttons

        # Create a frame to hold the buttons and text on top of the background
        controls_frame = Frame(self.root, bg="#1A1A1A")
        controls_frame.place(relx=0.5, rely=0.85, anchor="center")

        # Get the directory where the script is located
        script_dir = os.path.dirname(os.path.abspath(__file__))

        # Define the relative path to 'speed' folder
        Base_Path = os.path.join(script_dir, ".")

        # Resize PNG Button Images
        self.play_img = self.resize_image(os.path.join(Base_Path, "Play.png"), (50, 50))
        self.pause_img = self.resize_image(os.path.join(Base_Path, "Pause.png"), (50, 50))
        self.next_img = self.resize_image(os.path.join(Base_Path, "Next.png"), (50, 50))
        self.prev_img = self.resize_image(os.path.join(Base_Path, "Previous.png"), (50, 50))
        self.like_img = self.resize_image(os.path.join(Base_Path, "Like.png"), (50, 50))

        # Control Buttons
        self.prev_button = Button(controls_frame, image=self.prev_img, command=self.previous_track, bg="#1A1A1A", borderwidth=0)
        self.prev_button.grid(row=0, column=0, padx=10)

        self.play_button = Button(controls_frame, image=self.play_img, command=self.play_pause_track, bg="#1A1A1A", borderwidth=0)
        self.play_button.grid(row=0, column=1, padx=10)

        self.next_button = Button(controls_frame, image=self.next_img, command=self.next_track, bg="#1A1A1A", borderwidth=0)
        self.next_button.grid(row=0, column=2, padx=10)

        self.like_button = Button(controls_frame, image=self.like_img, command=self.like_track, bg=None, borderwidth=0)
        self.like_button.grid(row=0, column=3, padx=10)

        # Update Track Information Periodically
        self.update_current_track()
        


    def resize_image(self, path, size):
        """Resize PNG images for buttons."""
        img = Image.open(path).resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)




    def update_album_art(self, image_url):
        """Download, blur, and display album art with rounded corners as background."""
        try:
            from urllib.request import urlopen
            # Download the image
            img_data = urlopen(image_url).read()
            img = Image.open(io.BytesIO(img_data)).resize((250, 250), Image.Resampling.LANCZOS)

            # Resize the image to match the window size
            img_resized = img.resize((450, 450), Image.Resampling.LANCZOS)

            # Create a blurred background
            blurred_img = img_resized.filter(ImageFilter.GaussianBlur(radius=10))

            # Convert the blurred image to a format suitable for Tkinter
            blurred_background = ImageTk.PhotoImage(blurred_img)

            # Set the blurred background as the canvas background
            self.canvas.create_image(0, 0, anchor="nw", image=blurred_background)
            self.canvas.image = blurred_background  # Keep a reference to avoid garbage collection

            # Display the rounded, unblurred album art
            album_art_resized = img.resize((250, 250), Image.Resampling.LANCZOS)
     
            album_art = ImageTk.PhotoImage(album_art_resized)

            self.album_art_label.config(image=album_art)
            self.album_art_label.image = album_art

            

        except Exception as e:
            print(f"Error updating album art: {e}")
            self.album_art_label.config(image="")  # Clear image on error

    def update_current_track(self):
        """Update the currently playing track."""
        try:
            current = sp.current_playback()
            if current and current.get("item"):
                track = current["item"]
                track_name = track["name"]
                artists = ", ".join(artist["name"] for artist in track["artists"])
                self.current_track.set(f"{track_name} - {artists}")

                # Update album art
                if track.get("album") and track["album"].get("images"):
                    self.update_album_art(track["album"]["images"][0]["url"])
                else:
                    self.album_art_label.config(image="")
            else:
                self.current_track.set("No track playing")
                self.album_art_label.config(image="")
        except Exception as e:
            self.current_track.set("Error: Unable to fetch track")

        # Schedule the next update
        self.root.after(1000, self.update_current_track)

    def play_pause_track(self):
        """Toggle play/pause."""
        try:
            current = sp.current_playback()
            if current and current["is_playing"]:
                sp.pause_playback()
            else:
                sp.start_playback()
            self.update_current_track()
        except Exception as e:
            print(f"Error toggling play/pause: {e}")

    def next_track(self):
        """Skip to the next track."""
        try:
            sp.next_track()
            self.update_current_track()
        except Exception as e:
            print(f"Error skipping to next track: {e}")

    def previous_track(self):
        """Skip to the previous track."""
        try:
            sp.previous_track()
            self.update_current_track()
        except Exception as e:
            print(f"Error skipping to previous track: {e}")

    def like_track(self):
        """Add the current track to the user's library."""
        try:
            current = sp.current_playback()
            if current and current.get("item"):
                track_id = current["item"]["id"]
                sp.current_user_saved_tracks_add([track_id])
                print("Track liked!")
        except Exception as e:
            print(f"Error liking track: {e}")


# Main Program
if __name__ == "__main__":
    root = Tk()
    app = SpotifyApp(root)
    root.mainloop()




