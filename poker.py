import pygame
import random
import itertools
from collections import Counter

# Initialize pygame
pygame.init()

# Screen settings
WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Poker Game")

# Load card images
CARD_WIDTH, CARD_HEIGHT = 100, 145
card_images = {}
suits = ['clubs', 'diamonds', 'hearts', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
rank_values = {r: i for i, r in enumerate(ranks, 2)}

FONT = pygame.font.SysFont(None, 32)
BIG_FONT = pygame.font.SysFont(None, 48, bold=True)

# Game state variables
small_blind = 500
big_blind = 1000
bet_made = False
player_is_bb = True
bot_should_act = player_is_bb
round_stage = 0
pot_size = 0
bet_choice = 1
bot_stacks = big_blind*100
player_stacks = big_blind*100
hands = []
deck = []
community_cards = []
button_locked_until = 0
bet_history = []
show_cards = False

def format_number(n):
    if n >= 1e12:
        return f"{n:.1e}"  # Scientific notation like 1.3e+12
    elif n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    else:
        return str(n)
    
def reset_round():
    global small_blind, big_blind, bet_made, round_stage, hands, deck, community_cards, pot_size, player_is_bb, bot_should_act, bet_history, bet_choice, show_cards
    bet_made = False
    round_stage = 0
    bet_choice = 1
    pot_size = 0
    player_is_bb = not player_is_bb
    bot_should_act = not bot_should_act
    deck = get_shuffled_deck()
    hands = [deck[0:2], deck[2:4]]
    community_cards = deck[4:9]
    bet_history = []
    show_cards = False

def load_card_images():
    for suit in suits:
        for rank in ranks:
            filename = f'cards/{rank}_of_{suit}.png'
            image = pygame.image.load(filename)
            image = pygame.transform.scale(image, (CARD_WIDTH, CARD_HEIGHT))
            card_images[(rank, suit)] = image

def get_shuffled_deck():
    deck = [(rank, suit) for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def draw_hand(hand, x_start, y):
    for i, card in enumerate(hand):
        screen.blit(card_images[card], (x_start + i * (CARD_WIDTH + 10), y))

def draw_pot_size():
    text = FONT.render(f"Pot: {pot_size}", True, (255, 255, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, 260 + CARD_HEIGHT + 20))
    screen.blit(text, text_rect)

def draw_card_backs(x_start, y):
    back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    back.fill((255, 0, 0))
    pygame.draw.rect(back, (255, 255, 255), back.get_rect(), 5)
    for i in range(2):
        screen.blit(back, (x_start + i * (CARD_WIDTH + 10), y))

def draw_community_cards():
    y_pos = 260
    if round_stage >= 1:
        for i in range(min(3, len(community_cards))):
            screen.blit(card_images[community_cards[i]], (300 + i * (CARD_WIDTH + 10), y_pos))
    if round_stage >= 2:
        screen.blit(card_images[community_cards[3]], (300 + 3 * (CARD_WIDTH + 10), y_pos))
    if round_stage >= 3:
        screen.blit(card_images[community_cards[4]], (300 + 4 * (CARD_WIDTH + 10), y_pos))

def draw_buttons():
    global bet_made
    action_label = "RAISE" if bet_made else "BET"
    check_label = "CALL" if bet_made else "CHECK"
    actions = ['FOLD', check_label, action_label]
    buttons = []

    minus_10_rect = pygame.Rect(WIDTH - 500, HEIGHT - 180, 40, 40)
    minus_rect = pygame.Rect(WIDTH - 450, HEIGHT - 180, 40, 40)
    plus_rect = pygame.Rect(WIDTH - 400, HEIGHT - 180, 40, 40)
    plus_10_rect = pygame.Rect(WIDTH - 350, HEIGHT - 180, 40, 40)

    for rect, label in [(minus_10_rect, "-10"), (minus_rect, "-"), (plus_rect, "+"), (plus_10_rect, "+10")]:
        pygame.draw.rect(screen, (60, 60, 60), rect, border_radius=6)
        text = FONT.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    bet_text = FONT.render(f"{bet_choice} BB ({bet_choice * big_blind:,})", True, (255, 255, 255))
    screen.blit(bet_text, (WIDTH - 470, HEIGHT - 130))

    for i, action in enumerate(actions):
        width = 140 if action == 'CHECK' else 120 if action == 'FOLD' else 110
        rect = pygame.Rect(WIDTH - 470 + i * 150, HEIGHT - 70, width, 50)
        pygame.draw.rect(screen, (60, 60, 60), rect, border_radius=6)
        text = BIG_FONT.render(action, True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)
        buttons.append((action, rect))

    buttons.append(("+", plus_rect))
    buttons.append(("-", minus_rect))
    buttons.append(("+10", plus_10_rect))
    buttons.append(("-10", minus_10_rect))
    return buttons

def handle_action(action, bet_amount, player):
    global bet_made, round_stage, pot_size, bot_stacks, player_stacks, bet_history, show_cards, hands
    if action == "FOLD":
        print(f"{player}: FOLD")
        if player == 0:
            bot_stacks += pot_size
            highest_opp_bet = 0
            for i, j in bet_history:
                if i == 0 and j > highest_opp_bet:
                    highest_opp_bet = j
            bot_stacks += highest_opp_bet
        else:
            player_stacks += pot_size
            highest_opp_bet = 0
            for i, j in bet_history:
                if i == 1 and j > highest_opp_bet:
                    highest_opp_bet = j
            player_stacks += highest_opp_bet
        pygame.time.delay(1500)
        reset_round()
        return
    elif action == "BET":
        print(f"{player}: {action} {bet_amount} BB")
        bet_history.append((player, bet_amount))
        bet_made = True
    elif action == "RAISE":
        print(f"{player}: {action} {bet_amount} BB")
        bet_history.append((player, bet_amount))
        bet_made = True
    elif action == "CALL":
        print(f"{player}: CALL {bet_history[-1][1]} BB")
        pot_size += bet_history[-1][1] * 2 * big_blind
        player_stacks -= bet_history[-1][1] * big_blind
        bot_stacks -= bet_history[-1][1] * big_blind
        if round_stage >= 3:
            show_cards = True
            draw_hand(hands[1], 250, 50)
            if determine_winner() == "player":
                player_stacks += pot_size
                print("Player Wins!")
            elif determine_winner() == "bot":
                bot_stacks += pot_size
                print("Bot Wins!")
            else:
                player_stacks += pot_size/2
                bot_stacks += pot_size/2
                print("Tie!")
        bet_made = False
    elif action == "CHECK":
        print(f"{player}: CHECK")
        if (round_stage >= 3 and player == 0 and player_is_bb) or (round_stage >= 3 and player == 1 and not player_is_bb):
            show_cards = True
            draw_hand(hands[1], 250, 50)
            if determine_winner() == "player":
                player_stacks += pot_size
                print("Player Wins!")
            elif determine_winner() == "bot":
                bot_stacks += pot_size
                print("Bot Wins!")
            else:
                player_stacks += pot_size/2
                bot_stacks += pot_size/2
                print("Tie!")

    if action == "CALL":
        round_stage += 1
        bet_history = []
    elif player == 1 and action == "CHECK" and not player_is_bb:
        round_stage += 1
        bet_history = []
    elif player == 0 and action == "CHECK" and player_is_bb:
        round_stage += 1
        bet_history = []

    if round_stage >= 4:
        pygame.time.delay(3000)
        reset_round()

def evaluate_hand(hand):
    values = sorted([rank_values[card[0]] for card in hand], reverse=True)
    suits_list = [card[1] for card in hand]
    value_counts = Counter(values)
    flush = len(set(suits_list)) == 1
    straight = all(values[i] - 1 == values[i+1] for i in range(len(values) - 1))

    if straight and flush:
        return (8, values)
    elif 4 in value_counts.values():
        four = [v for v, count in value_counts.items() if count == 4]
        return (7, four + [v for v in values if v not in four])
    elif 3 in value_counts.values() and 2 in value_counts.values():
        triple = [v for v, count in value_counts.items() if count == 3]
        pair = [v for v, count in value_counts.items() if count == 2]
        return (6, triple + pair)
    elif flush:
        return (5, values)
    elif straight:
        return (4, values)
    elif 3 in value_counts.values():
        triple = [v for v, count in value_counts.items() if count == 3]
        return (3, triple + [v for v in values if v not in triple])
    elif list(value_counts.values()).count(2) == 2:
        pairs = sorted([v for v, count in value_counts.items() if count == 2], reverse=True)
        return (2, pairs + [v for v in values if v not in pairs])
    elif 2 in value_counts.values():
        pair = [v for v, count in value_counts.items() if count == 2]
        return (1, pair + [v for v in values if v not in pair])
    else:
        return (0, values)

def determine_winner():
    player_best = max((evaluate_hand(list(combo)) for combo in itertools.combinations(hands[0] + community_cards, 5)), key=lambda x: x)
    bot_best = max((evaluate_hand(list(combo)) for combo in itertools.combinations(hands[1] + community_cards, 5)), key=lambda x: x)
    if player_best > bot_best:
        return "player"
    elif bot_best > player_best:
        return "bot"
    else:
        return "tie"


def bot_action():
    global bet_made
    action = random.choice(["CALL" if bet_made else "CHECK", "RAISE" if bet_made else "BET"])
    if action == "RAISE":
        bet_made = True
    handle_action(action, 2, 1)
    return action

def draw_player_info():
    pygame.draw.circle(screen, (255, 255, 255), (70, 110), 60)
    screen.blit(FONT.render("Bot", True, (0, 0, 0)), (50, 85))
    screen.blit(FONT.render(format_number(bot_stacks), True, (0, 0, 120)), (40, 110))

    pygame.draw.circle(screen, (255, 255, 255), (70, 590), 60)
    screen.blit(FONT.render("You", True, (0, 0, 0)), (50, 565))
    screen.blit(FONT.render(format_number(player_stacks), True, (0, 0, 120)), (40, 590))

def main():
    global bet_choice, button_locked_until, player_is_bb, bot_should_act
    clock = pygame.time.Clock()
    running = True
    load_card_images()
    reset_round()

    
    while running:
        screen.fill((0, 100, 0))
        draw_player_info()
        draw_hand(hands[0], 250, 500)
        draw_community_cards()
        draw_pot_size()
        if show_cards:
            draw_hand(hands[1], 250, 50)
        else:
            draw_card_backs(250, 50)
        
        buttons = draw_buttons()

        current_time = pygame.time.get_ticks()

        if bot_should_act and current_time >= button_locked_until:
            button_locked_until = current_time + 1000
            bot_current = bot_action()
            bot_should_act = False


        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for action, rect in buttons:
                    if rect.collidepoint(event.pos):
                        if current_time < button_locked_until:
                            continue
                        elif action == "+":
                            bet_choice += 1
                        elif action == "-" and bet_choice > 1:
                            bet_choice -= 1
                        elif action == "+10":
                            bet_choice += 10
                        elif action == "-10" and bet_choice > 10:
                            bet_choice -= 10
                        else:
                            button_locked_until = pygame.time.get_ticks() + 3000
                            #Not big blind scenario
                            if not player_is_bb:
                                handle_action(action, bet_choice, 0)
                                pygame.time.delay(1000)
                                if action == "CALL":
                                    continue
                                else:
                                    bot_action()
                            else:
                                if bot_current == "CALL":
                                    continue
                                else:
                                    handle_action(action, bet_choice, 0)
                                    bot_should_act = True
                            
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == '__main__':
    main()