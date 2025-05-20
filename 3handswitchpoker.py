import pygame
import random
import itertools
from collections import Counter

pygame.init()

WIDTH, HEIGHT = 1000, 700
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Poker Game")

CARD_WIDTH, CARD_HEIGHT = 100, 145
card_images = {}
suits = ['clubs', 'diamonds', 'hearts', 'spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'jack', 'queen', 'king', 'ace']
rank_values = {r: i for i, r in enumerate(ranks, 2)}

FONT = pygame.font.SysFont(None, 32)
BIG_FONT = pygame.font.SysFont(None, 48, bold=True)

small_blind = 500
big_blind = 1000
bet_made = True
player_is_bb = True # this starts as false because of reset_round
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
if player_is_bb:
    bet_history = [(1, 0.5), (0, 1)]
else:
    bet_history = [(0, 0.5), (1, 1)]
show_cards = False
pre_flop = True
card_value_map = {f"card_{i}": i for i in range(5)}
hand_value_map = {f"hand_{i}": i for i in range(5)}
card_selected = ""
card_switched = False

def format_number(n):
    if n >= 1e12:
        return f"{n:.1e}"
    elif n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    elif n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    elif n >= 1_000:
        return f"{n / 1_000:.1f}K"
    else:
        return str(n)
    
def reset_round():
    global small_blind, big_blind, bet_made, round_stage, hands, deck, community_cards, pot_size, player_is_bb, bot_should_act, bet_history, bet_choice, show_cards, pre_flop, card_selected, card_switched
    bet_made = True
    round_stage = 0
    bet_choice = 1
    pot_size = 0
    player_is_bb = not player_is_bb
    bot_should_act = not bot_should_act
    deck = get_shuffled_deck()
    hands = [deck[0:3], deck[3:6]]
    community_cards = deck[6:11]
    if player_is_bb:
        bet_history = [(1, 0.5), (0, 1)]
    else:
        bet_history = [(0, 0.5), (1, 1)]
    show_cards = False
    pre_flop = True
    card_selected = ""
    card_switched = False

def load_card_images():
    global card_images
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
    global card_images
    for i, card in enumerate(hand):
        screen.blit(card_images[card], (x_start + i * (CARD_WIDTH + 10), y))

def draw_pot_size():
    global pot_size
    text = FONT.render(f"Pot: {format_number(pot_size)}", True, (255, 255, 0))
    text_rect = text.get_rect(center=(WIDTH // 2, 260 + CARD_HEIGHT + 20))
    screen.blit(text, text_rect)

def draw_card_backs(x_start, y):
    back = pygame.Surface((CARD_WIDTH, CARD_HEIGHT))
    back.fill((255, 0, 0))
    pygame.draw.rect(back, (255, 255, 255), back.get_rect(), 5)
    for i in range(3):
        screen.blit(back, (x_start + i * (CARD_WIDTH + 10), y))

def draw_buttons():
    #includes community cards, interactive buttons, and hand buttons
    global bet_made, round_stage, card_images
    buttons = []
    x_start = 175
    y = 500
    hand = hands[0]
    for i in range(len(hand)):
        x = x_start + i * (CARD_WIDTH + 10)
        rect = pygame.Rect(x, y, CARD_WIDTH, CARD_HEIGHT)
        if card_selected == f"hand_{i}":
            border = pygame.Rect(x-5, y-5, CARD_WIDTH+10, CARD_HEIGHT+10)
            pygame.draw.rect(screen, (0, 0, 255), border)
        screen.blit(card_images[hand[i]], rect)
        buttons.append((f"hand_{i}", rect))
    
    action_label = "RAISE" if bet_made else "BET"
    check_label = "CALL" if bet_made else "CHECK"
    actions = ['FOLD', check_label, action_label]

    shift = 100
    minus_10_rect = pygame.Rect(WIDTH - 500 + shift, HEIGHT - 180, 40, 40)
    minus_rect = pygame.Rect(WIDTH - 450 + shift, HEIGHT - 180, 40, 40)
    plus_rect = pygame.Rect(WIDTH - 400 + shift, HEIGHT - 180, 40, 40)
    plus_10_rect = pygame.Rect(WIDTH - 350 + shift, HEIGHT - 180, 40, 40)
    all_in_rect = pygame.Rect(WIDTH - 275 + shift, HEIGHT - 180, 80, 40)
    reset_rect = pygame.Rect(WIDTH - 275 + shift, HEIGHT - 130, 80, 40)

    for rect, label in [(minus_10_rect, "-10"), (minus_rect, "-"), (plus_rect, "+"), (plus_10_rect, "+10"), (all_in_rect, "ALL-IN"), (reset_rect, "RESET")]:
        pygame.draw.rect(screen, (60, 60, 60), rect, border_radius=6)
        text = FONT.render(label, True, (255, 255, 255))
        text_rect = text.get_rect(center=rect.center)
        screen.blit(text, text_rect)

    bet_text = FONT.render(f"{bet_choice:.1f} BB ({format_number(bet_choice * big_blind)})", True, (255, 255, 255))
    screen.blit(bet_text, (WIDTH - 470 + shift, HEIGHT - 130))

    for i, action in enumerate(actions):
        width = 140 if action == 'CHECK' else 120 if action == 'FOLD' else 130 if action == "RAISE" else 110 if action == "CALL" else 95
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
    buttons.append(("ALL-IN", all_in_rect))
    buttons.append(("RESET", reset_rect))

    y_pos = 260
    if round_stage >= 1:
        for i in range(3):
            x = 300 + i * (CARD_WIDTH + 10)
            rect = pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT)
            if card_selected == f"card_{i}":
                border = pygame.Rect(x-5, y_pos-5, CARD_WIDTH+10, CARD_HEIGHT+10)
                pygame.draw.rect(screen, (0, 0, 255), border)
            screen.blit(card_images[community_cards[i]], rect)
            buttons.append((f"card_{i}", rect))

    if round_stage >= 2:
        x = 300 + 3 * (CARD_WIDTH + 10)
        rect = pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT)
        if card_selected == f"card_{3}":
            border = pygame.Rect(x-5, y_pos-5, CARD_WIDTH+10, CARD_HEIGHT+10)
            pygame.draw.rect(screen, (0, 0, 255), border)
        screen.blit(card_images[community_cards[3]], rect)
        buttons.append(("card_3", rect))

    if round_stage >= 3:
        x = 300 + 4 * (CARD_WIDTH + 10)
        rect = pygame.Rect(x, y_pos, CARD_WIDTH, CARD_HEIGHT)
        if card_selected == f"card_{4}":
            border = pygame.Rect(x-5, y_pos-5, CARD_WIDTH+10, CARD_HEIGHT+10)
            pygame.draw.rect(screen, (0, 0, 255), border)
        screen.blit(card_images[community_cards[4]], rect)
        buttons.append(("card_4", rect))
    
    return buttons

def valid_raise(bet_amount):
    highest_bet = 0
    for i, j in bet_history:
        if j > highest_bet:
            highest_bet = j
    if bet_amount >= 2*highest_bet or (bet_amount == 3 and highest_bet == 2):
        return True
    else:
        return False

def choose_all_in():
    global bet_choice
    if bet_choice > player_stacks/big_blind:
        bet_choice = player_stacks/big_blind

def handle_action(action, bet_amount, player):
    global bet_made, round_stage, pot_size, bot_stacks, player_stacks, bet_history, show_cards, hands, pre_flop, card_selected, card_switched
    if action == "FOLD":
        print(f"{player}: FOLD")
        if player == 0:
            bot_stacks += pot_size
            highest_opp_bet = 0
            for i, j in bet_history:
                if i == 0 and j > highest_opp_bet:
                    highest_opp_bet = j
            bot_stacks += highest_opp_bet
            player_stacks -= highest_opp_bet
        else:
            player_stacks += pot_size
            highest_opp_bet = 0
            for i, j in bet_history:
                if i == 1 and j > highest_opp_bet:
                    highest_opp_bet = j
            player_stacks += highest_opp_bet
            bot_stacks -= highest_opp_bet
        pygame.time.delay(1500)
        reset_round()
        return
    elif action == "BET":
        print(f"{player}: {action} {bet_amount} BB")
        if pre_flop:
            pre_flop = False
        bet_history.append((player, bet_amount))
        bet_made = True
    elif action == "RAISE":
        print(f"{player}: {action} {bet_amount} BB")
        if pre_flop:
            pre_flop = False
        bet_history.append((player, bet_amount))
        bet_made = True
    elif action == "CALL":
        print(f"{player}: CALL {bet_history[-1][1]} BB")
        if pre_flop and len(bet_history) == 2:
            bet_made = False
            bet_history.append((player, bet_history[-1][1]))
        else:
            pot_size += bet_history[-1][1] * 2 * big_blind
            player_stacks -= bet_history[-1][1] * big_blind
            bot_stacks -= bet_history[-1][1] * big_blind
            if round_stage >= 3:
                show_cards = True
                draw_hand(hands[1], 175, 50)
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
            draw_hand(hands[1], 175, 50)
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
        elif pre_flop and len(bet_history) == 3:
            pre_flop = False
            pot_size += bet_history[-1][1] * 2 * big_blind
            player_stacks -= bet_history[-1][1] * big_blind
            bot_stacks -= bet_history[-1][1] * big_blind
    elif action in card_value_map.keys():
        if card_switched:
            pass
        elif card_selected == action:
            card_selected = ""
        elif (card_selected in card_value_map.keys() or card_selected == ""):
            card_selected = action
        else:
            temp = hands[0][hand_value_map.get(card_selected)]
            hands[0][hand_value_map.get(card_selected)] = community_cards[card_value_map.get(action)]
            community_cards[card_value_map.get(action)] = temp
            card_switched = True
            card_selected = ""
    elif action in hand_value_map.keys():
        if card_switched:
            pass
        elif card_selected == action:
            card_selected = ""
        elif (card_selected in hand_value_map.keys() or card_selected == ""):
            card_selected = action
        else:
            temp = community_cards[card_value_map.get(card_selected)]
            community_cards[card_value_map.get(card_selected)] = hands[0][hand_value_map.get(action)]
            hands[0][hand_value_map.get(action)] = temp
            card_switched = True
            card_selected = ""
            

    if action == "CALL" and not pre_flop:
        round_stage += 1
        bet_history = []
        card_switched = False
    elif player == 1 and action == "CHECK" and not player_is_bb:
        round_stage += 1
        bet_history = []
        card_switched = False
    elif player == 0 and action == "CHECK" and player_is_bb:
        round_stage += 1
        bet_history = []
        card_switched = False

def evaluate_hand(hand):
    values = sorted([rank_values[card[0]] for card in hand], reverse=True)
    suits_list = [card[1] for card in hand]
    value_counts = Counter(values)
    flush = len(set(suits_list)) == 1
    straight = all(values[i] - 1 == values[i+1] for i in range(len(values) - 1))

    if straight and flush:
        return (5, values)
    elif 3 in value_counts.values():
        triple = [v for v, count in value_counts.items() if count == 3]
        return (4, triple + [v for v in values if v not in triple])
    elif straight:
        return (3, values)
    elif flush:
        return (2, values)
    elif 2 in value_counts.values():
        pair = [v for v, count in value_counts.items() if count == 2]
        return (1, pair + [v for v in values if v not in pair])
    else:
        return (0, values)

def determine_winner():
    player_best = evaluate_hand(list(hands[0]))
    bot_best = evaluate_hand(list(hands[1]))
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
    bot_bet = 0
    for player, bet_amount in bet_history:
        if player == 1 and bot_bet < bet_amount:
            bot_bet = bet_amount
    screen.blit(FONT.render(format_number(bot_bet*big_blind), True, (255, 255, 255)), (45, 200))
    
    pygame.draw.circle(screen, (255, 255, 255), (70, 590), 60)
    screen.blit(FONT.render("You", True, (0, 0, 0)), (50, 565))
    screen.blit(FONT.render(format_number(player_stacks), True, (0, 0, 120)), (40, 590))
    player_bet = 0
    for player, bet_amount in bet_history:
        if player == 0 and player_bet < bet_amount:
            player_bet = bet_amount
    screen.blit(FONT.render(format_number(player_bet*big_blind), True, (255, 255, 255)), (45, 480))


def main():
    global bet_choice, button_locked_until, player_is_bb, bot_should_act, card_selected
    clock = pygame.time.Clock()
    running = True
    load_card_images()
    reset_round()
    
    while running:
        if round_stage >= 4:
            pygame.time.delay(3000)
            reset_round()
        screen.fill((0, 100, 0))
        draw_player_info()
        draw_pot_size()
        draw_card_backs(175, 50)
        
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
                            choose_all_in()
                        elif action == "-" and bet_choice > 1:
                            bet_choice -= 1
                        elif action == "+10":
                            bet_choice += 10
                            choose_all_in()
                        elif action == "-10" and bet_choice > 10:
                            bet_choice -= 10
                        elif action == "ALL-IN":
                            bet_choice = player_stacks/big_blind
                        elif action == "RESET":
                            bet_choice = 1
                        elif action == "-" or action == "-10":
                            continue
                        elif action in card_value_map.keys() or action in hand_value_map.keys():
                            handle_action(action, 0, 0)
                        elif action == "RAISE" or action  == "BET":
                            if valid_raise(bet_choice):
                                button_locked_until = pygame.time.get_ticks() + 3000
                                if not player_is_bb:
                                    handle_action(action, bet_choice, 0)
                                    pygame.time.delay(1000)
                                    if (action == "CALL" and not pre_flop) or action  == "FOLD":
                                        continue
                                    else:
                                        bot_action()
                                else:
                                    if (bot_current == "CALL" and not pre_flop) or action == "FOLD":
                                        continue
                                    else:
                                        handle_action(action, bet_choice, 0)
                                        bot_should_act = True
                        else:
                            button_locked_until = pygame.time.get_ticks() + 3000
                            if not player_is_bb:
                                handle_action(action, bet_choice, 0)
                                pygame.time.delay(1000)
                                if (action == "CALL" and not pre_flop) or action == "FOLD":
                                    continue
                                else:
                                    bot_action()
                            else:
                                if (bot_current == "CALL" and not pre_flop) or bot_current == "FOLD":
                                    continue
                                else:
                                    handle_action(action, bet_choice, 0)
                                    bot_should_act = True
                            
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == '__main__':
    main()