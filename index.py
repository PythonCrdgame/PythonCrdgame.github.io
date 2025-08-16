import pygame
import random
import sys
import math
from pygame import gfxdraw

# Initialize pygame
pygame.init()

# Set up display with reasonable default size
screen_width, screen_height = 1200, 800
screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
pygame.display.set_caption("AI Tools Matching Game")

# Colors
BACKGROUND = (240, 240, 245)
WHITE = (255, 255, 255)
BLACK = (30, 30, 30)
PRIMARY = (101, 84, 192)
SECONDARY = (67, 198, 172)
ACCENT = (255, 107, 107)
LIGHT_GRAY = (220, 220, 220)
DARK_GRAY = (100, 100, 100)

# Fonts
def get_scaled_fonts():
    base_size = min(screen.get_width(), screen.get_height())
    return {
        'title': pygame.font.Font(None, int(base_size * 0.06)),
        'header': pygame.font.Font(None, int(base_size * 0.04)),
        'button': pygame.font.Font(None, int(base_size * 0.035)),
        'question': pygame.font.Font(None, int(base_size * 0.03)),
        'tool': pygame.font.Font(None, int(base_size * 0.025))
    }

fonts = get_scaled_fonts()

class ScrollableArea:
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.content_height = height
        self.scroll_y = 0
        self.scroll_speed = 20
        self.dragging = False
        self.drag_start_y = 0
        self.scroll_start_y = 0
        
    def update_content_height(self, height):
        self.content_height = height
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.dragging = True
                self.drag_start_y = event.pos[1]
                self.scroll_start_y = self.scroll_y
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            delta_y = event.pos[1] - self.drag_start_y
            self.scroll_y = self.scroll_start_y - delta_y
            self.clamp_scroll()
        elif event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * self.scroll_speed
            self.clamp_scroll()
            
    def clamp_scroll(self):
        max_scroll = max(0, self.content_height - self.rect.height)
        self.scroll_y = max(0, min(max_scroll, self.scroll_y))
        
    def get_scroll_offset(self):
        return self.scroll_y

class Dice:
    def __init__(self):
        self.size = int(min(screen.get_width(), screen.get_height()) * 0.08)
        self.value = 1
        self.rolling = False
        self.roll_time = 0
        self.roll_duration = 1000
        
    def update_size(self):
        self.size = int(min(screen.get_width(), screen.get_height()) * 0.08)
        
    def draw(self, surface, x, y):
        # Draw dice base
        pygame.draw.rect(surface, WHITE, (x, y, self.size, self.size), border_radius=10)
        pygame.draw.rect(surface, PRIMARY, (x, y, self.size, self.size), 3, border_radius=10)
        
        # Draw dots
        dot_color = PRIMARY
        dot_radius = self.size // 10
        center_x, center_y = x + self.size//2, y + self.size//2
        offset = self.size // 3
        
        if self.rolling:
            temp_value = random.randint(1, 6)
            self.draw_dots(surface, temp_value, dot_radius, center_x, center_y, offset, dot_color)
        else:
            self.draw_dots(surface, self.value, dot_radius, center_x, center_y, offset, dot_color)
            
    def draw_dots(self, surface, value, radius, cx, cy, offset, color):
        positions = {
            1: [(cx, cy)],
            2: [(cx - offset, cy - offset), (cx + offset, cy + offset)],
            3: [(cx - offset, cy - offset), (cx, cy), (cx + offset, cy + offset)],
            4: [(cx - offset, cy - offset), (cx + offset, cy - offset), 
                (cx - offset, cy + offset), (cx + offset, cy + offset)],
            5: [(cx - offset, cy - offset), (cx + offset, cy - offset), (cx, cy),
                (cx - offset, cy + offset), (cx + offset, cy + offset)],
            6: [(cx - offset, cy - offset), (cx + offset, cy - offset),
                (cx - offset, cy), (cx + offset, cy),
                (cx - offset, cy + offset), (cx + offset, cy + offset)]
        }
        
        for pos in positions[value]:
            pygame.draw.circle(surface, color, pos, radius)
            
    def roll(self):
        if not self.rolling:
            self.rolling = True
            self.roll_time = pygame.time.get_ticks()
            return True
        return False
        
    def update(self):
        if self.rolling:
            if pygame.time.get_ticks() - self.roll_time > self.roll_duration:
                self.rolling = False
                self.value = random.randint(1, 6)
                return self.value
        return None

class Card:
    def __init__(self, x, y, width, height, text, card_type):
        self.rect = pygame.Rect(x, y, width, height)
        self.original_y = y
        self.text = text
        self.card_type = card_type
        self.matched = False
        self.highlight = False
        self.connected_to = None
        self.line_pos = None
        
    def update_position(self, scroll_offset):
        self.rect.y = self.original_y - scroll_offset
        
    def draw(self, surface):
        # Draw card
        if self.matched:
            color = SECONDARY
            border_color = DARK_GRAY
        elif self.highlight:
            color = (PRIMARY[0]-30, PRIMARY[1]-30, PRIMARY[2]-30)
            border_color = PRIMARY
        else:
            color = WHITE
            border_color = PRIMARY if self.card_type == 'question' else (PRIMARY[0]+30, PRIMARY[1]+30, PRIMARY[2]+30)
        
        pygame.draw.rect(surface, color, self.rect, border_radius=12)
        pygame.draw.rect(surface, border_color, self.rect, 2, border_radius=12)
        
        # Draw text with wrapping
        font = fonts['question'] if self.card_type == 'question' else fonts['tool']
        words = self.text.split(' ')
        lines = []
        current_line = []
        max_width = self.rect.width - 20
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            if font.size(test_line)[0] <= max_width:
                current_line.append(word)
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        total_height = len(lines) * font.get_linesize()
        start_y = self.rect.centery - total_height // 2
        
        for i, line in enumerate(lines):
            text_surf = font.render(line, True, BLACK)
            text_rect = text_surf.get_rect(
                centerx=self.rect.centerx,
                y=start_y + i * font.get_linesize()
            )
            surface.blit(text_surf, text_rect)
        
        # Draw connection line if matched
        if self.connected_to and self.line_pos:
            color = SECONDARY if self.matched else PRIMARY
            pygame.draw.line(surface, color, self.rect.center, self.line_pos, 3)
            pygame.draw.circle(surface, ACCENT, self.rect.center, 6)
            pygame.draw.circle(surface, ACCENT, self.line_pos, 6)

class Game:
    def __init__(self):
        self.dice = Dice()
        self.questions = self.load_questions()
        self.question_cards = []
        self.tool_cards = []
        self.current_matches = 0
        self.total_matches = 0
        self.score = 0
        self.feedback = ""
        self.feedback_time = 0
        self.game_state = "start"
        self.dragging_line = None
        
        # Create scrollable areas
        header_height = int(screen.get_height() * 0.25)
        self.question_scroll = ScrollableArea(
            int(screen.get_width() * 0.05), 
            header_height,
            int(screen.get_width() * 0.35),
            screen.get_height() - header_height - 50
        )
        self.tool_scroll = ScrollableArea(
            int(screen.get_width() * 0.6), 
            header_height,
            int(screen.get_width() * 0.35),
            screen.get_height() - header_height - 50
        )
        
        self.create_ui_elements()
        
    def create_ui_elements(self):
        # Create roll button
        btn_width = int(screen.get_width() * 0.2)
        btn_height = int(screen.get_height() * 0.08)
        self.roll_button = {
            'rect': pygame.Rect(
                screen.get_width()//2 - btn_width//2, 
                int(screen.get_height() * 0.2), 
                btn_width, btn_height
            ),
            'text': "Roll Dice",
            'color': PRIMARY,
            'hover': False
        }
        
    def load_questions(self):
        return [
            {"question": "Which tool performs calculations?", "correct_tool": "Calculator", "wrong_tools": ["Distance", "Color Picker"]},
            {"question": "Which tool measures distance?", "correct_tool": "Distance", "wrong_tools": ["Calculator", "Translator"]},
            {"question": "Which tool translates languages?", "correct_tool": "Translator", "wrong_tools": ["Calculator", "Object Detector"]},
            {"question": "Which tool detects objects?", "correct_tool": "Object Detector", "wrong_tools": ["Face Recognizer", "Text Reader"]},
            {"question": "Which tool picks colors?", "correct_tool": "Color Picker", "wrong_tools": ["Image Enhancer", "Font Matcher"]},
            {"question": "Which tool recognizes faces?", "correct_tool": "Face Recognizer", "wrong_tools": ["Object Detector", "Age Predictor"]}
        ]
        
    def setup_round(self, num_questions):
        self.question_cards = []
        self.tool_cards = []
        self.current_matches = 0
        self.total_matches = num_questions
        self.dragging_line = None
        
        # Calculate positions and sizes
        card_width = int(screen.get_width() * 0.35)
        card_height = int(screen.get_height() * 0.12)
        card_spacing = int(screen.get_height() * 0.02)
        
        # Select questions and create cards
        selected_questions = random.sample(self.questions, min(num_questions, len(self.questions)))
        all_tools = []
        
        # Calculate content height for scroll areas
        question_content_height = len(selected_questions) * (card_height + card_spacing)
        self.question_scroll.update_content_height(question_content_height)
        
        for i, question in enumerate(selected_questions):
            y_pos = i * (card_height + card_spacing)
            self.question_cards.append(Card(
                int(screen.get_width() * 0.05), 
                y_pos, 
                card_width, 
                card_height, 
                question["question"], 
                'question'
            ))
            all_tools.append(question["correct_tool"])
            all_tools.extend(random.sample(question["wrong_tools"], 2))
        
        random.shuffle(all_tools)
        
        # Calculate tool content height
        tool_content_height = len(all_tools) * (card_height + card_spacing)
        self.tool_scroll.update_content_height(tool_content_height)
        
        for i, tool in enumerate(all_tools):
            y_pos = i * (card_height + card_spacing)
            self.tool_cards.append(Card(
                int(screen.get_width() * 0.6), 
                y_pos, 
                card_width, 
                card_height, 
                tool, 
                'tool'
            ))
    
    def draw_button(self, button):
        color = (button['color'][0]-20, button['color'][1]-20, button['color'][2]-20) if button['hover'] else button['color']
        pygame.draw.rect(screen, color, button['rect'], border_radius=10)
        pygame.draw.rect(screen, BLACK, button['rect'], 2, border_radius=10)
        
        text_surf = fonts['button'].render(button['text'], True, WHITE)
        text_rect = text_surf.get_rect(center=button['rect'].center)
        screen.blit(text_surf, text_rect)
        
    def draw_title(self):
        title_text = "AI Tools Matching Game"
        text_surf = fonts['title'].render(title_text, True, PRIMARY)
        
        # Draw dice as part of title
        dice_x = screen.get_width()//2 - text_surf.get_width()//2 - self.dice.size - 10
        dice_y = 20
        self.dice.draw(screen, dice_x, dice_y)
        
        # Draw title text
        screen.blit(text_surf, (dice_x + self.dice.size + 10, dice_y + self.dice.size//2 - text_surf.get_height()//2))
        
    def draw(self):
        screen.fill(BACKGROUND)
        
        # Draw title with integrated dice
        self.draw_title()
        
        # Draw score
        score_text = fonts['header'].render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (screen.get_width() - score_text.get_width() - 20, 20))
        
        # Draw roll button
        self.draw_button(self.roll_button)
        
        if self.game_state == "playing":
            # Update card positions based on scroll
            question_scroll_offset = self.question_scroll.get_scroll_offset()
            tool_scroll_offset = self.tool_scroll.get_scroll_offset()
            
            for card in self.question_cards:
                card.update_position(question_scroll_offset)
            for card in self.tool_cards:
                card.update_position(tool_scroll_offset)
            
            # Draw scrollable areas
            self.draw_scrollable_areas()
            
            # Draw dragging line
            if self.dragging_line:
                pygame.draw.line(screen, PRIMARY, self.dragging_line[0], self.dragging_line[1], 3)
                pygame.draw.circle(screen, ACCENT, self.dragging_line[0], 8)
                pygame.draw.circle(screen, ACCENT, self.dragging_line[1], 5)
            
            # Draw progress
            progress_text = fonts['button'].render(
                f"Matches: {self.current_matches}/{self.total_matches}", True, BLACK)
            screen.blit(progress_text, (screen.get_width()//2 - progress_text.get_width()//2, screen.get_height() - 50))
            
        elif self.game_state == "start":
            instructions = [
                "Welcome to AI Tools Matching Game!",
                "",
                "1. Roll the dice to determine how many questions you'll get",
                "2. Click and drag from questions to tools",
                "3. Match all questions to complete the round",
                "4. Earn points for each correct match",
                "",
                "Click 'Roll Dice' to begin!"
            ]
            
            for i, line in enumerate(instructions):
                color = BLACK if i > 0 else PRIMARY
                font = fonts['header'] if i == 0 else fonts['button']
                text = font.render(line, True, color)
                screen.blit(text, (screen.get_width()//2 - text.get_width()//2, screen.get_height() * 0.4 + i * 40))
                
        elif self.game_state == "feedback":
            feedback_text = fonts['header'].render(self.feedback, True, SECONDARY if "Correct" in self.feedback else ACCENT)
            screen.blit(feedback_text, (screen.get_width()//2 - feedback_text.get_width()//2, screen.get_height()//2))
            
            continue_text = fonts['button'].render("Click to continue", True, DARK_GRAY)
            screen.blit(continue_text, (screen.get_width()//2 - continue_text.get_width()//2, screen.get_height()//2 + 50))
            
        if self.feedback and pygame.time.get_ticks() - self.feedback_time < 2000:
            feedback_text = fonts['button'].render(self.feedback, True, SECONDARY if "Correct" in self.feedback else ACCENT)
            screen.blit(feedback_text, (screen.get_width()//2 - feedback_text.get_width()//2, screen.get_height() - 100))
    
    def draw_scrollable_areas(self):
        # Create surfaces for scrollable content
        question_surface = pygame.Surface((self.question_scroll.rect.width, self.question_scroll.content_height))
        question_surface.fill(BACKGROUND)
        
        tool_surface = pygame.Surface((self.tool_scroll.rect.width, self.tool_scroll.content_height))
        tool_surface.fill(BACKGROUND)
        
        # Draw cards onto scroll surfaces
        for card in self.question_cards:
            if card.rect.bottom > 0 and card.rect.top < self.question_scroll.rect.height:
                card.draw(question_surface)
        
        for card in self.tool_cards:
            if card.rect.bottom > 0 and card.rect.top < self.tool_scroll.rect.height:
                card.draw(tool_surface)
        
        # Draw scrollable areas onto screen
        screen.blit(question_surface, (self.question_scroll.rect.x, self.question_scroll.rect.y), 
                    (0, self.question_scroll.get_scroll_offset(), self.question_scroll.rect.width, self.question_scroll.rect.height))
        
        screen.blit(tool_surface, (self.tool_scroll.rect.x, self.tool_scroll.rect.y), 
                    (0, self.tool_scroll.get_scroll_offset(), self.tool_scroll.rect.width, self.tool_scroll.rect.height))
        
        # Draw scroll bars if needed
        self.draw_scroll_bars()
    
    def draw_scroll_bars(self):
        # Question area scroll bar
        if self.question_scroll.content_height > self.question_scroll.rect.height:
            scroll_height = self.question_scroll.rect.height
            content_height = self.question_scroll.content_height
            scroll_ratio = scroll_height / content_height
            thumb_height = max(20, scroll_height * scroll_ratio)
            
            thumb_top = (self.question_scroll.get_scroll_offset() / content_height) * scroll_height
            thumb_rect = pygame.Rect(
                self.question_scroll.rect.right - 10,
                self.question_scroll.rect.y + thumb_top,
                8,
                thumb_height
            )
            pygame.draw.rect(screen, LIGHT_GRAY, thumb_rect, border_radius=4)
        
        # Tool area scroll bar
        if self.tool_scroll.content_height > self.tool_scroll.rect.height:
            scroll_height = self.tool_scroll.rect.height
            content_height = self.tool_scroll.content_height
            scroll_ratio = scroll_height / content_height
            thumb_height = max(20, scroll_height * scroll_ratio)
            
            thumb_top = (self.tool_scroll.get_scroll_offset() / content_height) * scroll_height
            thumb_rect = pygame.Rect(
                self.tool_scroll.rect.right - 10,
                self.tool_scroll.rect.y + thumb_top,
                8,
                thumb_height
            )
            pygame.draw.rect(screen, LIGHT_GRAY, thumb_rect, border_radius=4)
    
    def handle_event(self, event):
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
            
        if event.type == pygame.VIDEORESIZE:
            global screen_width, screen_height
            screen_width, screen_height = event.w, event.h
            screen = pygame.display.set_mode((screen_width, screen_height), pygame.RESIZABLE)
            fonts = get_scaled_fonts()
            self.dice.update_size()
            
            # Update scroll areas
            header_height = int(screen.get_height() * 0.25)
            self.question_scroll.rect = pygame.Rect(
                int(screen.get_width() * 0.05), 
                header_height,
                int(screen.get_width() * 0.35),
                screen.get_height() - header_height - 50
            )
            self.tool_scroll.rect = pygame.Rect(
                int(screen.get_width() * 0.6), 
                header_height,
                int(screen.get_width() * 0.35),
                screen.get_height() - header_height - 50
            )
            
            self.create_ui_elements()
            if self.game_state == "playing":
                self.setup_round(self.total_matches)
            
        # Handle scroll events
        if self.game_state == "playing":
            mouse_pos = pygame.mouse.get_pos()
            if self.question_scroll.rect.collidepoint(mouse_pos):
                self.question_scroll.handle_event(event)
            if self.tool_scroll.rect.collidepoint(mouse_pos):
                self.tool_scroll.handle_event(event)
            
        if event.type == pygame.MOUSEMOTION:
            self.roll_button['hover'] = self.roll_button['rect'].collidepoint(event.pos)
            
            # Update card highlights considering scroll offset
            q_scroll_offset = self.question_scroll.get_scroll_offset() if self.game_state == "playing" else 0
            t_scroll_offset = self.tool_scroll.get_scroll_offset() if self.game_state == "playing" else 0
            
            for card in self.question_cards:
                adjusted_rect = pygame.Rect(
                    card.rect.x,
                    card.rect.y + q_scroll_offset,
                    card.rect.width,
                    card.rect.height
                )
                card.highlight = adjusted_rect.collidepoint(event.pos) and not card.matched
                
            for card in self.tool_cards:
                adjusted_rect = pygame.Rect(
                    card.rect.x,
                    card.rect.y + t_scroll_offset,
                    card.rect.width,
                    card.rect.height
                )
                card.highlight = adjusted_rect.collidepoint(event.pos) and not card.matched
                
            if self.dragging_line:
                self.dragging_line = (self.dragging_line[0], event.pos)
            
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and 
            self.roll_button['rect'].collidepoint(event.pos) and 
            self.game_state == "start" and not self.dice.rolling):
            if self.dice.roll():
                self.game_state = "waiting_for_dice"
                
        dice_result = self.dice.update()
        if dice_result and self.game_state == "waiting_for_dice":
            self.setup_round(dice_result)
            self.game_state = "playing"
            
        if self.game_state == "playing":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Check if clicking on a question card (considering scroll)
                q_scroll_offset = self.question_scroll.get_scroll_offset()
                for card in self.question_cards:
                    adjusted_rect = pygame.Rect(
                        card.rect.x,
                        card.rect.y + q_scroll_offset,
                        card.rect.width,
                        card.rect.height
                    )
                    if adjusted_rect.collidepoint(event.pos) and not card.matched:
                        self.dragging_line = (adjusted_rect.center, event.pos)
                        break
            
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.dragging_line:
                start_pos, end_pos = self.dragging_line
                self.dragging_line = None
                
                matched = False
                # Check if dropped on a tool card (considering scroll)
                t_scroll_offset = self.tool_scroll.get_scroll_offset()
                for t_card in self.tool_cards:
                    adjusted_rect = pygame.Rect(
                        t_card.rect.x,
                        t_card.rect.y + t_scroll_offset,
                        t_card.rect.width,
                        t_card.rect.height
                    )
                    if adjusted_rect.collidepoint(end_pos) and not t_card.matched:
                        # Find which question card we started from
                        q_scroll_offset = self.question_scroll.get_scroll_offset()
                        for q_card in self.question_cards:
                            q_adjusted_rect = pygame.Rect(
                                q_card.rect.x,
                                q_card.rect.y + q_scroll_offset,
                                q_card.rect.width,
                                q_card.rect.height
                            )
                            if q_adjusted_rect.collidepoint(start_pos) and not q_card.matched:
                                for q in self.questions:
                                    if q["question"] == q_card.text and q["correct_tool"] == t_card.text:
                                        q_card.matched = True
                                        t_card.matched = True
                                        q_card.connected_to = t_card
                                        t_card.connected_to = q_card
                                        q_card.line_pos = adjusted_rect.center
                                        t_card.line_pos = q_adjusted_rect.center
                                        self.current_matches += 1
                                        self.score += 1
                                        self.feedback = "Correct match! +1 point"
                                        self.feedback_time = pygame.time.get_ticks()
                                        matched = True
                                        break
                                
                                if not matched:
                                    self.feedback = "Incorrect match! Try again"
                                    self.feedback_time = pygame.time.get_ticks()
                                break
                        break
                
                if self.current_matches == self.total_matches:
                    self.feedback = f"Round complete! Score: {self.score}"
                    self.feedback_time = pygame.time.get_ticks()
                    self.game_state = "feedback"
                    
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and 
            self.game_state == "feedback"):
            self.game_state = "start"

def main():
    clock = pygame.time.Clock()
    game = Game()
    
    while True:
        for event in pygame.event.get():
            game.handle_event(event)
        
        game.draw()
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
