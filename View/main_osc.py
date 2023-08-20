import pygame
import sys
from pythonosc.dispatcher import Dispatcher
from pythonosc.osc_server import ThreadingOSCUDPServer
import threading
import pygame.display


# Initialize Pygame
pygame.init()

# Initialize variable for toggling full-screen mode
fullscreen = True

# Get the screen dimensions
screen_info = pygame.display.Info()
window_width = screen_info.current_w
window_height = screen_info.current_h

# Create the screen (windowed mode)
screen = pygame.display.set_mode((window_width, window_height), pygame.FULLSCREEN)
pygame.display.set_caption("Mouse Path Drawing")

# Clock for controlling frame rate
clock = pygame.time.Clock()

# Initialize variables for tracking the mouse path
mouse_path = []

# Initialize variables for tracking OSC coordinates
received_osc_x = None
received_osc_y = None

# Initialize variables for simulated mouse movement
mouse_position = (window_width // 2, window_height // 2)
mouse_speed = 0.1

# Initialize variables for line thickness
min_thickness = 1
max_thickness = 15
current_thickness = max_thickness

# Initialize variables for smoothing mouse movement
smoothing_factor = 0.2  # Adjust this value for desired smoothness

# Initialize variable for hiding condition
hide_drawing = False

# Initialize variable for erasing condition
erase_drawing = False


# Initialize variables for dynamic angle calculation
prev_angle = 0.0

# Hide the system mouse cursor at the beginning of the program
pygame.mouse.set_visible(False)

# OSC handler for receiving x and y coordinates
def draw_with_osc(address, *args):
    global received_osc_x, received_osc_y, hide_drawing, erase_drawing
    if address == "/mouse":
        x, y = args
        received_osc_x = x
        received_osc_y = y
    elif address == "/hide" and args[0] == 1:
        hide_drawing = True
    elif address == "/hide" and args[0] == 0:
        hide_drawing = False
    elif address == "/erase" and args[0] == 1:
        erase_drawing = True
    # print("Received OSC x:", received_osc_x)
    # print("Received OSC y:", received_osc_y)
    # print("Received OSC erase:", erase_drawing)


# Initialize the OSC dispatcher
osc_dispatcher = Dispatcher()
osc_dispatcher.map("/mouse", draw_with_osc)
osc_dispatcher.map("/hide", draw_with_osc)
osc_dispatcher.map("/erase", draw_with_osc)

# Create an OSC server on a separate thread
osc_server = ThreadingOSCUDPServer(("10.0.0.37", 12345), osc_dispatcher)
server_thread = threading.Thread(target=osc_server.serve_forever)
server_thread.daemon = True
server_thread.start()


# Initialize variables for storing the last mouse position
last_mouse_position = (window_width // 2, window_height // 2)

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_f:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((window_width, window_height), pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((1024, 1024))
                pygame.display.set_caption("Mouse Path Drawing")
            elif event.key == pygame.K_c:  # Press 'c' key to hide the drawing
                hide_drawing = not hide_drawing
            elif event.key == pygame.K_e:  # Press 'e' key to erase the drawing
                erase_drawing = True

    # Fill the screen with a white background
    screen.fill((255, 255, 255))

    # Erase the drawing if erase condition is met
    if erase_drawing:
        mouse_path.clear()
        erase_drawing = False  # Reset the erase condition

    # Update simulated mouse movement based on received OSC coordinates
    if received_osc_x is not None and received_osc_y is not None:
        if abs(received_osc_x) > 0.01 or abs(received_osc_y) > 0.01:
            target_x = int((received_osc_x + 1) * window_width / 2)
            target_y = int((received_osc_y + 1) * window_height / 2)

            diff_x = target_x - mouse_position[0]
            diff_y = target_y - mouse_position[1]

            # Calculate the movement step based on mouse_speed and smoothing_factor
            step_x = diff_x * mouse_speed * smoothing_factor
            step_y = diff_y * mouse_speed * smoothing_factor

            # Smoothly move the mouse position towards the target position
            mouse_position = (
                int(mouse_position[0] + step_x),
                int(mouse_position[1] + step_y)
            )

            # Calculate line thickness based on distance
            distance = pygame.math.Vector2(diff_x, diff_y).length()
            current_thickness = max_thickness - (distance / (window_width + window_height)) * (max_thickness - min_thickness)
            current_thickness = max(min_thickness, min(max_thickness, current_thickness))

            # Update the mouse path
            mouse_path.append((mouse_position, int(current_thickness)))
        else:
            # Ignore OSC input near (0, 0) but keep the last known mouse position
            last_mouse_position = mouse_position
    else:
        # Reset last_mouse_position and clear mouse_path when OSC values are None
        last_mouse_position = mouse_position
        mouse_path.clear()

    # Draw the mouse path with linearly changing line thickness, only if not hidden
    if not hide_drawing and len(mouse_path) > 1:
        for i in range(1, len(mouse_path)):
            start_pos, thickness = mouse_path[i - 1]
            end_pos, _ = mouse_path[i]
            pygame.draw.line(screen, (0, 0, 0), start_pos, end_pos, thickness)

    # Draw a white layer to hide the drawing if the hide condition is met
    if hide_drawing:
        pygame.draw.rect(screen, (255, 255, 255), pygame.Rect(0, 0, window_width, window_height))

    # Update the display
    pygame.display.flip()
    clock.tick(60)  # Limit to 60 frames per second

# Quit Pygame
pygame.quit()
