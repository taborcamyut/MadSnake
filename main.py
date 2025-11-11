"""
AppProject2
11/20/2024
Cameron Yutzy
Sources Used: https://github.com/rajatdiptabiswas/snake-pygame
https://gist.github.com/wynand1004/ec105fd2f457b10d971c09586ec44900
"""

import customtkinter as ctk
import random

# Settings
GAME_SPEED = 100
CELL_SIZE = 20 # How big each square in the background (cell) is on the board
GRID_WIDTH = 40 # How many cells are on the board horizontally
GRID_HEIGHT = 30 # How many cells are on the board vertically
SNAKE_LENGTH = 3 # The starting snake length
BACKGROUND_COLOR = "#4cba46"
SECONDARY_BACKGROUND_COLOR = None # Set to None and it will automatically create a secondary color
SNAKE_COLOR = "#00a0ff"

# Original Colors
# Background = 4cba46
# Snake = 00a0ff

LEMON_SPAWN_CHANCE = 1
ORANGE_SPAWN_CHANCE = 1
SUGAR_SPAWN_CHANCE = 1
BOMB_SPAWN_CHANCE = 1
PORTAL_SPAWN_CHANCE = 1

LEMON_DESPAWN_TIME = 200
ORANGE_DESPAWN_TIME = 200
SUGAR_DESPAWN_TIME = 200
BOMB_DESPAWN_TIME = 20
PORTAL_DESPAWN_TIME = 200

# I used an idea from another snake game where the positions of things are based on which cell (or which column and row) they are in,
# but because the size of the cell can be customized, I have to take the position of the object I have saved and multiply it by the size of the cell
# I only use the next two variables twice, but it helps simplify
WINDOW_WIDTH = GRID_WIDTH * CELL_SIZE
WINDOW_HEIGHT = GRID_HEIGHT * CELL_SIZE

class SnakeGame(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Create window (the application itself)
        self.title("Mad Snake")
        self.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        # Create canvas (the area that I can draw everything on - the game)
        self.canvas = ctk.CTkCanvas(self, width=WINDOW_WIDTH, height=WINDOW_HEIGHT, bg=BACKGROUND_COLOR)
        self.canvas.pack()

        # Draw background
        self.draw_checkered_background()

        # Bind keys
        self.bind_keys()

        # Initialize game state
        self.snake = [] # A list of tuples, each tuple is the positions (x,y) of each snake segment
        self.score = 0
        for n in range(SNAKE_LENGTH): # Create the starting segments of the snake
            self.snake.append((GRID_WIDTH // 2, GRID_HEIGHT // 2 + n))
            self.score += 10
        # A dictionary of dictionaries. Used so items do not spawn in each other. {"item type":{instance:(x,y),instance:(x,y)}}
        # Normally set up like this: {"apple":{0:(4,5)},"lemon":{1:(15,14),2:(15,16)}}
        # Each dictionary of the items has instances of the items that exist of that type and their position
        self.item_positions = {"apple":{},"lemon":{},"orange":{},"sugar":{},"bomb":{},"portal":{}}
        # The following dictionary of dictionaries is set up similarly, but instead of a tuple of coordinates (x,y)
        # It is an integer of how many 'game loops' it will last until it despawns (I subtract one each game loop)
        self.item_cooldowns = {"lemon":{},"orange":{},"sugar":{},"bomb":{},"bomb_explosion":{},"portal":{}}
        # The following saves the duration of sugar effect (how long to keep the game going fast/slow)
        # I subtract one from each instance of an effect each 'game loop'.
        self.sugar_effect_duration = {"fast":{},"slow":{}}
        self.bomb_explosions = {}
        # A list of extra movements so I can input right and down before the snake actually moves
        self.movement_queue = []
        self.last_direction = "Up"
        self.direction = "Up"
        self.started = False
        self.running = False
        # A dictionary for portals, each instance of a portal group will have directions required to enter, and the axis its on and other things
        self.portals = {}
        # A seperate game speed variable that can be affected by the sugar effects
        self.game_speed = GAME_SPEED
        self.time_through_game = 1

        # Draw initial game state
        self.draw_snake()
        self.spawn_items()

    """Methods used once"""

    def draw_checkered_background(self):
        """Draw a checkerboard pattern on the background."""
        if SECONDARY_BACKGROUND_COLOR == None:
            secondary_color = self.adjust_color_brightness(BACKGROUND_COLOR, 1.2)
        else:
            secondary_color = SECONDARY_BACKGROUND_COLOR
        for row in range(GRID_HEIGHT):
            for col in range(GRID_WIDTH):
                if (row + col) % 2 == 0: # If its an even numbered cell, fill it with secondary color
                    x1, y1 = col * CELL_SIZE, row * CELL_SIZE
                    x2, y2 = x1 + CELL_SIZE, y1 + CELL_SIZE
                    self.canvas.create_rectangle(x1, y1, x2, y2,fill=secondary_color, outline="")

    def print_coordinates(self):
        """Print the X coordinates across the top row and Y coordinates down the left column.
        I used this for debugging."""
        
        # Print X coordinates across the top row
        for col in range(GRID_WIDTH):
            x1 = col * CELL_SIZE
            y1 = 0  # The y coordinate is at the top of the grid
            center_x = x1 + CELL_SIZE // 2
            center_y = y1 + CELL_SIZE // 2  # Placing the text in the center of the top row
            self.canvas.create_text(center_x, center_y, text=str(col), font=("Arial", 8, "bold"))
        
        # Print Y coordinates down the left column
        for row in range(GRID_HEIGHT):
            x1 = 0  # The x coordinate is at the left edge of the grid
            y1 = row * CELL_SIZE
            center_x = x1 + CELL_SIZE // 2  # Placing the text in the center of the left column
            center_y = y1 + CELL_SIZE // 2
            self.canvas.create_text(center_x, center_y, text=str(row), font=("Arial", 8, "bold"))

    def adjust_color_brightness(self, hex_color, factor):
        """Adjust the brightness of a hex color to have {factor} times more in rgb values."""
        # Take off the # and set r,g,b to each two digits in the hex code
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        # Multiply the value by {factor}, and incase the new value's too big, return 255
        r = min(255, int(r * factor))
        g = min(255, int(g * factor))
        b = min(255, int(b * factor))
        return f"#{r:02X}{g:02X}{b:02X}"

    def bind_keys(self):
        """Bind movement keys to change direction."""
        key_mapping = {
            "<Up>": "Up", "w": "Up",
            "<Down>": "Down", "s": "Down",
            "<Left>": "Left", "a": "Left",
            "<Right>": "Right", "d": "Right",}
        for key, direction in key_mapping.items():
            self.bind(key, lambda e, d=direction: self.queue_direction(d))
        self.focus_set()

    """Always active methods"""

    def queue_direction(self, new_direction):
        """Queue up to two movements and avoid opposite directions."""

        # Choose how many movement inputs to queue
        max_queue_length = 2

        # Only add the new direction if it's not opposite to the last direction
        opposite_directions = {
            "Up": "Down", "Down": "Up",
            "Left": "Right", "Right": "Left"
            }
        
        # Compare with last direction in movement queue
        if self.movement_queue:
            if (new_direction != opposite_directions.get(self.movement_queue[-1])
                and len(self.movement_queue) < max_queue_length): # Don't add movement to queue if queue is full
                self.movement_queue.append(new_direction)

        # Compare with self.last_direction if movement queue empty
        else:
            if new_direction != opposite_directions.get(self.last_direction):
                self.movement_queue.append(new_direction)
        
        # If game has not started, start game
        if not self.started:
            self.start_game()

    def start_game(self):
        """Start the main game loop."""
        self.started = True
        self.running = True
        self.game_loop()
    
    def game_loop(self):
        """Run the game."""
        if self.running:
            # print(f"{self.time_through_game}---------------------")
            # self.time_through_game += 1
            self.spawn_items()
            self.update_items()
            self.move_snake()
            self.draw_snake()
            self.after(int(self.game_speed), self.game_loop)

    def end_game(self):
        """Stop the game."""
        # If the game is already off, don't run again
        if self.running == False:
            return
        self.running = False
        self.canvas.create_text(
            WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2,
            text=f"Game Over\n Score: {self.score}", fill="white", font=("Arial", 24)
        )

    """Methods arranged in order of game loop execution"""

    """Spawn Items"""

    def spawn_items(self):
        """Spawn items."""
        self.spawn_apple()
        self.spawn_lemon()
        self.spawn_orange()
        self.spawn_sugar()
        self.spawn_bomb()
        self.spawn_portal()

    def spawn_apple(self):
        """Spawn apple at a random location."""
        # I only want one apple on the board, so first it makes sure there are no apple positions in the item_positions dictionary
        if self.item_positions["apple"] == {}:
            x,y = self.find_spot()
            self.item_positions["apple"][0] = (x,y) # Add apple to item positions
            # Draw apple
            self.canvas.create_oval(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill="red", tags="apple")
    
    def spawn_lemon(self):
        """Spawn lemon at a random location."""
        self.create_item("lemon","yellow",LEMON_SPAWN_CHANCE,LEMON_DESPAWN_TIME)

    def spawn_orange(self):
        """Spawn orange at a random location."""
        self.create_item("orange","orange",ORANGE_SPAWN_CHANCE,ORANGE_DESPAWN_TIME)

    def spawn_sugar(self):
        """Spawn sugar somewhere."""
        n,x,y = self.create_item("sugar","blue",SUGAR_SPAWN_CHANCE,SUGAR_DESPAWN_TIME)
        if n: # If it spawned a sugar bowl, draw the white sugar
            sugar_size = .2
            self.canvas.create_oval(
                (x + sugar_size) * CELL_SIZE, (y + sugar_size) * CELL_SIZE,
                (x + 1 - sugar_size) * CELL_SIZE, (y + 1 - sugar_size) * CELL_SIZE,
                fill="white", tags=f"sugarbowl{n}"
            )

    def spawn_bomb(self):
        """Spawn bomb."""
        self.create_item("bomb","black",BOMB_SPAWN_CHANCE,BOMB_DESPAWN_TIME)

    def create_item(self,name,color=None,chance=None,cooldown=None):
        """Create an item."""
        if random.randint(1,100) <= chance: # Use spawn chance to decide wether to spawn the item
            x,y = self.find_spot()
            n = self.next_index(name)
            if cooldown:
                self.item_cooldowns[name][n] = cooldown
            if color:
                self.item_positions[name][n] = (x,y) # if theres a color, add the item to the positions dictionary and draw it
                self.canvas.create_oval(
                    x * CELL_SIZE, y * CELL_SIZE,
                    (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                    fill=color, tags=f"{name}{n}"
                )
            return n,x,y
        else:
            return None,None,None

    def find_spot(self):
        """Finds an empty spot on the board."""
        while True:
            # Get a random position
            x = random.randint(0, GRID_WIDTH - 1)
            y = random.randint(0, GRID_HEIGHT - 1)

            # If those coordinates are in an item retry
            for name in self.item_positions:
                if self.item_positions[name] != {}:
                    for item_position in self.item_positions[name].values():
                        if (x,y) == item_position:
                            continue
            if not (x,y) in self.snake:
                return (x, y)

    def next_index(self,name,effect=None):
        """Returns 1 + amount of existing items with that name"""
        n = 1
        if effect == "sugar":
            while True:
                if self.sugar_effect_duration[name].get(n):
                    n += 1
                else:
                    return n
        while True:
            if self.item_positions[name].get(n):
                n += 1
            else:
                return n

    def spawn_portal(self):
        """Create a portal."""
        if random.randint(1,100) > PORTAL_SPAWN_CHANCE:
            return
        
        n = self.next_index("portal")
        self.item_positions["portal"][n] = (-2,-2) # Put in item positions list, just so I can use next_index function
        self.item_cooldowns["portal"][n] = PORTAL_DESPAWN_TIME
        self.portals[n] = {}

        # Randomize portal axis
        self.portals[n]["axisA"] = "vertical" if random.randint(0,1) == 0 else "horizontal"
        self.portals[n]["axisB"] = "vertical" if random.randint(0,1) == 0 else "horizontal"

        # Find safe spawn positions
        portal_positions = self.safe_portal_positions(n)

        # Create information variables about where positions/entrances of portals are
        # Each portal group has four portals. Four locations where if the snake is facing the right direction, it will teleport
        self.portals[n]["entrances"] = {}
        for i in range(4):
            self.portals[n]["entrances"][f"portal{i+1}"] = portal_positions[i]
        
        # Which direction is required to enter
        self.portals[n]["direction_in"] = {}
        self.portals[n]["direction_in"]["portal1"] = "Down" if self.portals[n]["axisA"] == "horizontal" else "Right"
        self.portals[n]["direction_in"]["portal2"] = "Up" if self.portals[n]["axisA"] == "horizontal" else "Left"
        self.portals[n]["direction_in"]["portal3"] = "Down" if self.portals[n]["axisB"] == "horizontal" else "Right"
        self.portals[n]["direction_in"]["portal4"] = "Up" if self.portals[n]["axisB"] == "horizontal" else "Left"

        # Which portal you will come out
        self.portals[n]["exits"] = {}
        self.portals[n]["exits"]["portal1"] = self.portals[n]["entrances"]["portal4"]
        self.portals[n]["exits"]["portal2"] = self.portals[n]["entrances"]["portal3"]
        self.portals[n]["exits"]["portal3"] = self.portals[n]["entrances"]["portal2"]
        self.portals[n]["exits"]["portal4"] = self.portals[n]["entrances"]["portal1"]

        # Which direction you will be when exiting
        self.portals[n]["direction_out"] = {}
        self.portals[n]["direction_out"]["portal1"] = "Down" if self.portals[n]["axisB"] == "horizontal" else "Right"
        self.portals[n]["direction_out"]["portal2"] = "Up" if self.portals[n]["axisB"] == "horizontal" else "Left"
        self.portals[n]["direction_out"]["portal3"] = "Down" if self.portals[n]["axisA"] == "horizontal" else "Right"
        self.portals[n]["direction_out"]["portal4"] = "Up" if self.portals[n]["axisA"] == "horizontal" else "Left"

        # Draw portals
        self.draw_portal(n,"axisA")
        self.draw_portal(n,"axisB")

    def draw_portal(self,n,axis):
        """Draws a portal."""
        portal = 1 if axis == "axisA" else 3
        x,y = self.portals[n]["entrances"][f"portal{portal}"]

        if self.portals[n][axis] == "vertical":
            x1 = x + 1
            y1 = y
            x2 = x + 1
            y2 = y + 1
        else: # if "horizontal"
            x1 = x
            y1 = y + 1
            x2 = x + 1
            y2 = y + 1
        self.canvas.create_line(x1*CELL_SIZE,y1*CELL_SIZE,x2*CELL_SIZE,y2*CELL_SIZE, fill="#8d01aa",width=10,tags=f"portal{n}")

    def safe_portal_positions(self,n):
        """Generates safe location for portal to spawn."""
        safe_distance = 5

        def generate_coords(axis,safe_area=None):
            """Generate coords that are safe_distance away from parallel wall.
            Also that are not in snake, and that are not in safe_area of other portal."""
            while True:
                if self.portals[n][axis] == "vertical":
                    x1 = random.randint(safe_distance, GRID_WIDTH - safe_distance)
                    y1 = random.randint(0, GRID_HEIGHT - 1)
                    x2 = x1 + 1
                    y2 = y1
                else: # if "horizontal"
                    x1 = random.randint(0, GRID_WIDTH - 1)
                    y1 = random.randint(safe_distance, GRID_HEIGHT - safe_distance)
                    x2 = x1
                    y2 = y1 + 1

                # if coords in snake, try again
                for segment in self.snake:
                    if segment in [(x1,y1),(x2,y2)]:
                        continue

                # if coords in safe_area of other portal, try again
                if safe_area:
                    for i in [(x1,y1),(x2,y2)]:
                        if i in safe_area:
                            continue
                break
            return x1,y1,x2,y2
        
        # Find coords for first portal
        x1,y1,x2,y2 = generate_coords("axisA")

        # Find safe area around first portal
        safe_zone = self.portal_safe_zone(n,x1,y1)

        # Find coords for second portal considering safe zone
        x3,y3,x4,y4 = generate_coords("axisB",safe_zone)
        
        # Return a list of the four spots on the board
        return [(x1,y1),(x2,y2),(x3,y3),(x4,y4)]
            
    def portal_safe_zone(self,n,x,y):
        """Create a list of coords around 1st two portal coords"""
        safe_distance = 2 # How wide and/or tall the safe zone will be

        # if axes are the same
        if self.portals[n]["axisA"] == self.portals[n]["axisB"]:

            # if axes are vertical, create a 2x1 area if safe_distance is 0
            if self.portals[n]["axisA"] == "vertical":

                top_left_x = x - safe_distance
                top_left_y = y
                bottom_right_x = x + 1 + safe_distance
                bottom_right_y = y

            # if axes are horizontal, create a 1x2 area if safe_distance is 0
            else:
                top_left_x = x
                top_left_y = y - safe_distance
                bottom_right_x = x
                bottom_right_y = y + 1 + safe_distance

        # if axes are different and axis is vertical, create 2x1 area if safe_distance is 0
        elif self.portals[n]["axisA"] == "vertical":

            top_left_x = x - safe_distance
            top_left_y = y - safe_distance
            bottom_right_x = x + 1 + safe_distance
            bottom_right_y = y + safe_distance
        
        # if axes are different and axis is horizontal, create 1x2 area if safe_distance is 0
        else:
            top_left_x = x - safe_distance
            top_left_y = y - safe_distance
            bottom_right_x = x + safe_distance
            bottom_right_y = y + 1 + safe_distance
        
        # Create a list of all the coordinates from the top left corner to the bottom right
        return [(x, y) for x in range(top_left_x, bottom_right_x) for y in range(top_left_y, bottom_right_y)]

    """Remove Items"""

    def update_items(self):
        """Update cooldown on all items"""
        for name in list(self.item_cooldowns):
            if self.item_cooldowns[name] != {}:
                for n in list(self.item_cooldowns[name]):
                    self.item_cooldowns[name][n] -= 1

                    # Remove items with cooldowns of 0
                    if self.item_cooldowns[name][n] == 0:
                        getattr(self, f"remove_{name}")(n)

        # Update sugar effect
        for effect in list(self.sugar_effect_duration):
            if self.sugar_effect_duration[effect] != {}:
                for n in list(self.sugar_effect_duration[effect]):
                    self.sugar_effect_duration[effect][n] -= 1

                    # Remove effects with cooldowns of 0
                    if self.sugar_effect_duration[effect][n] == 0:
                        self.sugar_effect_duration[effect].pop(n)
                        if effect == "fast":
                            self.game_speed *= 2
                        elif effect == "slow":
                            self.game_speed /= 2
                        else:
                            print("Just tried to delete a non-existent effect. >:)")

        # Try removing portals that have a snake in them
        for portal in list(self.portals):
            if self.portals[portal].get("in_snake") == True:
                self.remove_portal(portal)

    def remove_lemon(self,n):
        """Remove lemon n"""
        self.remove_item("lemon",n)

    def remove_orange(self,n):
        """Remove orange n"""
        self.remove_item("orange",n)

    def remove_sugar(self,n):
        """Remove sugar n"""
        self.remove_item("sugar",n)
        self.canvas.delete(f"sugarbowl{n}")

    def remove_bomb(self,n):
        """Explodes bomb n"""
        x,y = self.item_positions["bomb"][n]
        self.remove_item("bomb",n)
        # Create orange explosion
        self.canvas.create_rectangle(
                    (x - 1) * CELL_SIZE, (y - 1) * CELL_SIZE,
                    (x + 2) * CELL_SIZE, (y + 2) * CELL_SIZE,
                    fill="orange", tags=f"bomb_explosion{n}")
        # Add explosion area to bomb_explosions and item_cooldowns
        self.bomb_explosions[n] = [(x + dx, y + dy) for dx in range(-1, 2) for dy in range(-1, 2)]
        self.item_cooldowns["bomb_explosion"][n] = 2

    def remove_bomb_explosion(self,n):
        """Remove bomb explosion"""
        self.bomb_explosions.pop(n)
        self.canvas.delete(f"bomb_explosion{n}")

    def remove_portal(self,n):
        """Remove portal group n"""
        # Check for the portal being in a snake
        self.portals[n]["in_snake"] = False
        for portal in self.portals[n]["entrances"]:
            if portal in self.snake:
                self.portals[n]["in_snake"] = True
            
        # If the portal is not in snake, remove it
        if self.portals[n]["in_snake"] == False:
            self.remove_item("portal",n)
            self.portals.pop(n)

    def remove_item(self,name,n):
        """Removes most of item n"""
        if self.item_cooldowns.get(name,None): # If the item has a cooldown, remove the cooldown
            self.item_cooldowns[name].pop(n,None)
        self.item_positions[name].pop(n) # Remove the positions of the item
        self.canvas.delete(f"{name}{n}") # Delete the drawing of the item

    """Snake Movement"""

    def move_snake(self):
        """Move the snake and process collision logic."""
        # Check for movement from movement queue
        if self.movement_queue:
            self.direction = self.movement_queue[0]
            self.movement_queue.pop(0)

        # Ignore change in direction if you'll move into yourself or a wall
        # Get projected location
        projected_location = self.calculate_movement(self.snake[0],self.direction)
        # If inside end of tail, (check for multiple segments at the location of the tail incase of apple eating, if so revert) continue in new_direction because tail will move out of way
        # If inside self or inside wall, ignore change in direction, keep going the way you were going (self.direction = self.last_direction)
        # Even though these checks can, in the process of removing a movement from the movement queue, result in the next movement being opposite the current, you won't move into yourself
        # These checks will stop you from doing so. The only use of the code that checks for opposite movements in the queue_directions method is to save space in the queue
        if projected_location in self.snake or self.in_wall(projected_location):
            # If inside end of tail, skip to next if statement (Phrased differently: if not inside end of tail, revert to previous direction)
            if projected_location != self.snake[-1]:
                self.direction = self.last_direction
            # If tail will move (if theres not two segments there), don't revert direction (if multiple segments at location of tail (ate an apple on previous move) revert to previous direction)
            elif projected_location == self.snake[-2]:
                self.direction = self.last_direction

        # Check for portal collision
        n,i = self.entered_portal()
        if n:
            self.portals[n]["in_snake"] = True
            new_head = self.portals[n]["exits"][f"portal{i}"]
            self.direction = self.portals[n]["direction_out"][f"portal{i}"]
        else:
            new_head = self.calculate_movement(self.snake[0],self.direction)
        # Check for wall collision
        if self.in_wall(new_head):
            self.end_game()
            return

        # Move snake
        self.snake.insert(0, new_head) # Add head to list of snake positions (self.snake)
        self.snake.pop() # Remove tail

        # Check for self collision (check here so tail can move)
        if new_head in self.snake[1:]:
            self.end_game()
            return
        
        # Check for apple collision
        if self.item_positions["apple"] != {}:
            if new_head == self.item_positions["apple"][0]:
                self.canvas.delete("apple")
                self.item_positions["apple"].pop(0)
                self.add_snake_segment()

        # Check for lemon collision
        if self.item_positions["lemon"] != {}:
            for item_number,item_position in list(self.item_positions["lemon"].items()):
                if new_head == item_position:
                    self.remove_lemon(item_number)
                    # Add segments to the tail
                    for i in range(2):
                        self.add_snake_segment

        # Check for orange collision
        if self.item_positions["orange"] != {}:
            for item_number,item_position in list(self.item_positions["orange"].items()):
                if new_head == item_position:
                    self.remove_orange(item_number)
                    # Remove segments from the tail
                    for i in range(1):
                        self.remove_snake_segment()

        # Check for sugar collision
        if self.item_positions["sugar"] != {}:
            for item_number,item_position in list(self.item_positions["sugar"].items()):
                if new_head == item_position:
                    self.remove_sugar(item_number)
                    self.sugar_fast() if random.randint(0,3) else self.sugar_slow() # 75% Chance for fast, 25% chance for slow

        # Check for bomb collision
        if self.item_positions["bomb"] != {}:
            for item_number,item_position in list(self.item_positions["bomb"].items()):
                if new_head == item_position:
                    self.remove_snake_segment()
                    self.remove_bomb(item_number)
                    self.end_game()

        # Check for bomb explosion collision (check in dictionary of lists of tuples of coordinates)
        if self.bomb_explosions != {}:
            for area in self.bomb_explosions.values():
                if new_head in area:
                    self.remove_snake_segment()
                    self.end_game()

        # Update last direction to current direction
        self.last_direction = self.direction

    def calculate_movement(self,coords,direction):
        """Find where snake will be."""
        x,y = coords
        dx, dy = {"Up": (0, -1), "Down": (0, 1), "Left": (-1, 0), "Right": (1, 0)}[direction]
        return (x+dx,y+dy)

    def in_wall(self,coords):
        """Return boolean of: coords are in the wall."""
        x,y = coords
        return (x < 0 or x >= GRID_WIDTH or
                y < 0 or y >= GRID_HEIGHT)

    def entered_portal(self):
        """Check if snake is in any of the positions of portals.
        If so, for that portal, check if snake is facing the direction to enter it.
        If so, return portal group and specifically which portal."""
        # I added print statements because I kept having issues
        for portal_group in self.portals:
            for portal in range(4):
                portal_position = self.portals[portal_group]["entrances"][f"portal{portal + 1}"]
                if self.snake[0] == portal_position:
                    print(f"In portal {portal + 1} {portal_position} of group {portal_group}.", end = " ")
                    portal_direction = self.portals[portal_group]["direction_in"][f"portal{portal + 1}"]
                    if self.direction == portal_direction:
                        print(f"Facing into portal! Portal: {portal_direction}. Snake: {self.direction}.")
                        return portal_group,portal + 1
                    else:
                        print(f"Not facing portal. Portal: {portal_direction}. Snake: {self.direction}.")
                        print(self.portals)
        return None,None

    def add_snake_segment(self):
        """Add snake segment and increase score."""
        self.snake.append(self.snake[-1])
        self.score += 10

    def remove_snake_segment(self):
        """Remove snake segment and decrease score."""
        self.snake.pop()
        self.score -= 10
        # If you ate enough oranges to wipe the snake from existence, stop the game
        if self.snake == []:
            self.end_game()

    def sugar_fast(self):
        self.game_speed /= 2
        n = self.next_index("fast","sugar")
        self.sugar_effect_duration["fast"][n] = 60

    def sugar_slow(self):
        self.game_speed *= 2
        n = self.next_index("slow","sugar")
        self.sugar_effect_duration["slow"][n] = 30

    def draw_snake(self):
        """Draw the snake on the canvas."""
        self.canvas.delete("snake")
        for x, y in self.snake:
            self.canvas.create_rectangle(
                x * CELL_SIZE, y * CELL_SIZE,
                (x + 1) * CELL_SIZE, (y + 1) * CELL_SIZE,
                fill=SNAKE_COLOR, tags="snake")

# Run the game
if __name__ == "__main__":
    app = SnakeGame()
    app.mainloop()
