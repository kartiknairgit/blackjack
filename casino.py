import pygame
import random
from typing import List, Dict, Tuple
from dataclasses import dataclass
import math

pygame.init()

# Constants
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 768
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (34, 139, 34)
RED = (220, 20, 60)
GOLD = (255, 215, 0)
BLUE = (30, 144, 255)
GRAY = (128, 128, 128)

@dataclass
class Card:
    rank: str
    suit: str
    value: int
    prob_win: float = 0.0

class BlackjackTeacher:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Blackjack Probability Teacher")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game state
        self.credits = 1000
        self.bet = 100
        self.deck = []
        self.player_hand = []
        self.dealer_hand = []
        self.game_state = "betting"  # betting, playing, dealer_turn, game_over
        
        # Probability tracking
        self.cards_seen = []
        self.running_count = 0
        self.true_count = 0
        self.probability_breakdown = {}
        self.optimal_action = ""
        self.last_simulation_results = []
        
        self.create_deck()
        
    def create_deck(self, num_decks: int = 6):
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        suits = ['♠', '♥', '♦', '♣']
        
        for _ in range(num_decks):
            for suit in suits:
                for rank in ranks:
                    value = 0
                    if rank == 'A':
                        value = 11
                    elif rank in ['K', 'Q', 'J']:
                        value = 10
                    else:
                        value = int(rank)
                    self.deck.append(Card(rank, suit, value))
        
        random.shuffle(self.deck)
        
    def calculate_hand_value(self, hand: List[Card]) -> int:
        value = 0
        aces = 0
        
        for card in hand:
            if card.rank == 'A':
                aces += 1
            else:
                value += card.value
        
        # Add aces
        for _ in range(aces):
            if value + 11 <= 21:
                value += 11
            else:
                value += 1
                
        return value
    
    def get_card_probabilities(self) -> Dict[str, float]:
        """Calculate probability of drawing each card value"""
        remaining_cards = [card for card in self.deck]
        total_cards = len(remaining_cards)
        
        probabilities = {}
        for value in range(2, 12):  # 2-10 plus Ace (11)
            count = sum(1 for card in remaining_cards if card.value == value)
            probabilities[str(value)] = count / total_cards if total_cards > 0 else 0
            
        return probabilities
    
    def calculate_detailed_probability(self) -> Dict[str, float]:
        """Calculate detailed probabilities for different outcomes"""
        player_value = self.calculate_hand_value(self.player_hand)
        if player_value > 21:
            return {"bust": 1.0, "win": 0.0, "push": 0.0, "lose": 0.0}
            
        outcomes = {"bust": 0, "win": 0, "push": 0, "lose": 0}
        simulations = 1000
        
        for _ in range(simulations):
            # Run Monte Carlo simulation
            temp_hand = self.player_hand.copy()
            if self.game_state == "playing":
                # Simulate drawing one more card
                available_cards = [card for card in self.deck if card not in self.player_hand + self.dealer_hand]
                if available_cards:
                    temp_hand.append(random.choice(available_cards))
                    
            temp_value = self.calculate_hand_value(temp_hand)
            
            if temp_value > 21:
                outcomes["bust"] += 1
            else:
                # Simulate dealer's hand
                temp_dealer = self.dealer_hand.copy()
                while self.calculate_hand_value(temp_dealer) < 17:
                    available_cards = [card for card in self.deck if card not in temp_hand + temp_dealer]
                    if available_cards:
                        temp_dealer.append(random.choice(available_cards))
                        
                dealer_value = self.calculate_hand_value(temp_dealer)
                
                if dealer_value > 21:
                    outcomes["win"] += 1
                elif temp_value > dealer_value:
                    outcomes["win"] += 1
                elif temp_value == dealer_value:
                    outcomes["push"] += 1
                else:
                    outcomes["lose"] += 1
                    
        # Store last 10 simulation results for visualization
        self.last_simulation_results = [(k, v/simulations) for k, v in outcomes.items()]
        
        return {k: v/simulations for k, v in outcomes.items()}
    
    def get_optimal_action(self) -> str:
        """Determine the optimal action based on basic strategy"""
        player_value = self.calculate_hand_value(self.player_hand)
        dealer_up_card = self.dealer_hand[0].value if self.dealer_hand else 0
        
        has_ace = any(card.rank == 'A' for card in self.player_hand)
        is_pair = len(self.player_hand) == 2 and self.player_hand[0].rank == self.player_hand[1].rank
        
        # Basic strategy logic
        if player_value > 21:
            return "Bust"
        elif player_value == 21:
            return "Stand"
        elif has_ace:  # Soft hands
            if player_value >= 19:
                return "Stand"
            elif player_value == 18:
                return "Stand" if dealer_up_card < 9 else "Hit"
            else:
                return "Hit"
        elif is_pair:  # Pairs
            pair_value = self.player_hand[0].value
            if pair_value in [8, 11]:
                return "Split"
            elif pair_value == 10:
                return "Stand"
            elif pair_value <= 7:
                return "Hit"
        else:  # Hard hands
            if player_value >= 17:
                return "Stand"
            elif player_value <= 11:
                return "Hit"
            elif 12 <= player_value <= 16:
                return "Stand" if dealer_up_card < 7 else "Hit"
                
        return "Consider odds"
    
    def draw_probability_panel(self):
        """Draw the probability teaching panel on the right side"""
        panel_x = 800
        panel_width = SCREEN_WIDTH - panel_x
        
        # Draw panel background with a cleaner border
        pygame.draw.rect(self.screen, BLACK, (panel_x, 0, panel_width, SCREEN_HEIGHT))
        pygame.draw.line(self.screen, GOLD, (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)
        
        # Title with padding and underline
        title = self.font.render("Probability Analysis", True, GOLD)
        self.screen.blit(title, (panel_x + 30, 30))
        pygame.draw.line(self.screen, GOLD, (panel_x + 30, 70), (panel_x + 330, 70), 1)
        
        y = 100
        
        # Current hand analysis with better spacing
        if self.player_hand:
            player_value = self.calculate_hand_value(self.player_hand)
            hand_text = self.font.render(f"Your Hand: {player_value}", True, WHITE)
            self.screen.blit(hand_text, (panel_x + 30, y))
            
            # Probability bars with consistent spacing and alignment
            y += 60
            probs = self.calculate_detailed_probability()
            for i, (outcome, prob) in enumerate(probs.items()):
                # Bar label
                label = self.font.render(f"{outcome.capitalize()}", True, WHITE)
                self.screen.blit(label, (panel_x + 30, y + i*50))
                
                # Draw bar background
                bar_rect = pygame.Rect(panel_x + 150, y + i*50, 300, 30)
                pygame.draw.rect(self.screen, GRAY, bar_rect)
                
                # Draw filled bar
                fill_rect = pygame.Rect(panel_x + 150, y + i*50, int(300 * prob), 30)
                color = GOLD if outcome == "win" else BLUE if outcome == "push" else RED
                pygame.draw.rect(self.screen, color, fill_rect)
                
                # Percentage label
                percentage = self.font.render(f"{prob:.1%}", True, WHITE)
                self.screen.blit(percentage, (panel_x + 460, y + i*50))
        
        # Recommended action section
        y += 250
        pygame.draw.line(self.screen, GOLD, (panel_x + 30, y), (panel_x + 330, y), 1)
        y += 20
        action = self.get_optimal_action()
        action_text = self.font.render("Recommended Action", True, GOLD)
        self.screen.blit(action_text, (panel_x + 30, y))
        action_value = self.font.render(action, True, WHITE)
        self.screen.blit(action_value, (panel_x + 30, y + 40))
        
        # Card probabilities section
        y += 100
        pygame.draw.line(self.screen, GOLD, (panel_x + 30, y), (panel_x + 330, y), 1)
        y += 20
        prob_title = self.font.render("Next Card Probabilities", True, GOLD)
        self.screen.blit(prob_title, (panel_x + 30, y))
        
        # Two-column layout for card probabilities
        y += 40
        card_probs = self.get_card_probabilities()
        col_width = 200
        for i, (value, prob) in enumerate(card_probs.items()):
            col = i // 5  # Split into two columns after 5 items
            row = i % 5
            x = panel_x + 30 + (col * col_width)
            prob_text = self.small_font.render(f"Card {value}: {prob:.1%}", True, WHITE)
            self.screen.blit(prob_text, (x, y + row * 30))

    
    def update_card_counting(self, card: Card):
        # Hi-Lo counting system
        if card.value >= 2 and card.value <= 6:
            self.running_count += 1
        elif card.value >= 10 or card.rank == 'A':
            self.running_count -= 1
            
        # Calculate true count
        remaining_decks = len(self.deck) / 52
        self.true_count = self.running_count / remaining_decks if remaining_decks > 0 else 0
    
    def draw_card(self, for_player: bool = True) -> Card:
        if not self.deck:
            self.create_deck()
        card = self.deck.pop()
        self.update_card_counting(card)
        if for_player:
            self.player_hand.append(card)
        else:
            self.dealer_hand.append(card)
        return card
    
    def draw(self):
        # Main game background
        self.screen.fill(GREEN)
        
        # Header section with game info
        pygame.draw.rect(self.screen, BLACK, (0, 0, 800, 100))
        credits_text = self.font.render(f"Credits: ${self.credits}", True, GOLD)
        bet_text = self.font.render(f"Bet: ${self.bet}", True, GOLD)
        count_text = self.font.render(f"True Count: {self.true_count:.1f}", True, GOLD)
        
        self.screen.blit(credits_text, (30, 30))
        self.screen.blit(bet_text, (250, 30))
        self.screen.blit(count_text, (450, 30))
        
        # Dealer section
        dealer_y = 150
        pygame.draw.line(self.screen, WHITE, (30, dealer_y), (770, dealer_y), 1)
        dealer_text = self.font.render("Dealer's Hand", True, WHITE)
        self.screen.blit(dealer_text, (30, dealer_y + 20))
        
        # Draw dealer's cards with better spacing
        for i, card in enumerate(self.dealer_hand):
            card_x = 200 + i * 80
            pygame.draw.rect(self.screen, WHITE, (card_x, dealer_y + 60, 60, 90), 2)
            if i == 0 or self.game_state in ["dealer_turn", "game_over"]:
                card_text = self.font.render(f"{card.rank}{card.suit}", True, WHITE)
            else:
                card_text = self.font.render("??", True, WHITE)
            self.screen.blit(card_text, (card_x + 10, dealer_y + 85))
        
        # Player section
        player_y = SCREEN_HEIGHT - 250
        pygame.draw.line(self.screen, WHITE, (30, player_y), (770, player_y), 1)
        player_text = self.font.render("Your Hand", True, WHITE)
        self.screen.blit(player_text, (30, player_y + 20))
        
        # Draw player's cards
        for i, card in enumerate(self.player_hand):
            card_x = 200 + i * 80
            pygame.draw.rect(self.screen, WHITE, (card_x, player_y + 60, 60, 90), 2)
            card_text = self.font.render(f"{card.rank}{card.suit}", True, WHITE)
            self.screen.blit(card_text, (card_x + 10, player_y + 85))
        
        # Hand value
        if self.player_hand:
            player_value = self.calculate_hand_value(self.player_hand)
            value_text = self.font.render(f"Total: {player_value}", True, WHITE)
            self.screen.blit(value_text, (30, player_y + 170))
        
        # Game messages
        if self.game_state == "betting":
            msg = "Press SPACE to deal. UP/DOWN to adjust bet."
        elif self.game_state == "playing":
            msg = "Press H to hit, S to stand"
        elif self.game_state == "game_over":
            dealer_value = self.calculate_hand_value(self.dealer_hand)
            player_value = self.calculate_hand_value(self.player_hand)
            if player_value > 21:
                msg = "Bust! Press SPACE to play again"
            elif dealer_value > 21 or player_value > dealer_value:
                msg = "You win! Press SPACE to play again"
            else:
                msg = "Dealer wins! Press SPACE to play again"
                
        msg_text = self.font.render(msg, True, WHITE)
        msg_rect = msg_text.get_rect(center=(400, SCREEN_HEIGHT//2))
        self.screen.blit(msg_text, msg_rect)
        
        # Draw probability panel
        self.draw_probability_panel()
        
        pygame.display.flip()
    
    def run(self):
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and self.game_state in ["betting", "game_over"]:
                        if self.credits >= self.bet:
                            # Start new game
                            self.player_hand = []
                            self.dealer_hand = []
                            self.draw_card(True)
                            self.draw_card(True)
                            self.draw_card(False)
                            self.game_state = "playing"
                    elif event.key == pygame.K_UP and self.game_state == "betting":
                        self.bet = min(self.bet + 100, self.credits)
                    elif event.key == pygame.K_DOWN and self.game_state == "betting":
                        self.bet = max(self.bet - 100, 100)
                    elif event.key == pygame.K_h and self.game_state == "playing":
                        # Hit
                        self.draw_card(True)
                        if self.calculate_hand_value(self.player_hand) > 21:
                            self.credits -= self.bet
                            self.game_state = "game_over"
                    elif event.key == pygame.K_s and self.game_state == "playing":
                        # Stand - dealer's turn
                        self.game_state = "dealer_turn"
                        while self.calculate_hand_value(self.dealer_hand) < 17:
                            self.draw_card(False)
                        
                        player_value = self.calculate_hand_value(self.player_hand)
                        dealer_value = self.calculate_hand_value(self.dealer_hand)
                        
                        if dealer_value > 21 or player_value > dealer_value:
                            self.credits += self.bet
                        else:
                            self.credits -= self.bet
                        
                        self.game_state = "game_over"
            
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = BlackjackTeacher()
    game.run()
