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

small_blind = 1000
big_blind = 1000
bet_made = True
player_is_bb = True
bot_should_act = player_is_bb
pot_size = 0
bet_choice = 1
bot_stacks = big_blind*100
player_stacks = big_blind*100
hands = []
deck = []
button_locked_until = 0
if player_is_bb:
    bet_history = [(1, 1), (0, 1)]
else:
    bet_history = [(0, 1), (1, 1)]
show_cards = False
pre_flop = True

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
    global small_blind, big_blind, bet_made, hands, deck, pot_size, player_is_bb, bot_should_act, bet_history, bet_choice, show_cards, pre_flop
    bet_made = True
    bet_choice = 1
    pot_size = 0
    player_is_bb = not player_is_bb
    bot_should_act = not bot_should_act
    deck = get_shuffled_deck()
    hands = [deck[0:3], deck[3:6]]
    if player_is_bb:
        bet_history = [(1, 1), (0, 1)]
    else:
        bet_history = [(0, 1), (1, 1)]
    show_cards = False
    pre_flop = True

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
    global bet_made
    action_label = "RAISE" if bet_made else "BET"
    check_label = "CALL" if bet_made else "CHECK"
    actions = ['FOLD', check_label, action_label]
    buttons = []

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
    global bet_made, pot_size, bot_stacks, player_stacks, bet_history, show_cards, hands, pre_flop
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
        if (bet_history[-1][1] > player_stacks and player == 0):
            pot_size += bet_history[-1][1] * big_blind + player_stacks
            player_stacks = 0
            bot_stacks -= bet_history[-1][1] * big_blind
            show_cards = True
            draw_hand(hands[1], 175, 50)
            if determine_winner(hands[0], hands[1]) == "player":
                player_stacks += pot_size
                print("Player Wins!")
            elif determine_winner(hands[0], hands[1]) == "bot":
                bot_stacks += pot_size
                print("Bot Wins!")
            else:
                player_stacks += pot_size/2
                bot_stacks += pot_size/2
                print("Tie!")
            bet_made = False
        elif (bet_history[-1][1] > bot_stacks and player == 1):
            pot_size += bet_history[-1][1] * 2 * big_blind
            player_stacks -= bet_history[-1][1] * big_blind
            bot_stacks -= bet_history[-1][1] * big_blind
            show_cards = True
            draw_hand(hands[1], 175, 50)
            if determine_winner(hands[0], hands[1]) == "player":
                player_stacks += pot_size
                print("Player Wins!")
            elif determine_winner(hands[0], hands[1]) == "bot":
                bot_stacks += pot_size
                print("Bot Wins!")
            else:
                player_stacks += pot_size/2
                bot_stacks += pot_size/2
                print("Tie!")
            bet_made = False
        if pre_flop and len(bet_history) == 2:
            bet_made = False
            bet_history.append((player, bet_history[-1][1]))
        else:
            pot_size += bet_history[-1][1] * 2 * big_blind
            player_stacks -= bet_history[-1][1] * big_blind
            bot_stacks -= bet_history[-1][1] * big_blind
            show_cards = True
            draw_hand(hands[1], 175, 50)
            if determine_winner(hands[0], hands[1]) == "player":
                player_stacks += pot_size
                print("Player Wins!")
            elif determine_winner(hands[0], hands[1]) == "bot":
                bot_stacks += pot_size
                print("Bot Wins!")
            else:
                player_stacks += pot_size/2
                bot_stacks += pot_size/2
                print("Tie!")
            bet_made = False
    elif action == "CHECK":
        print(f"{player}: CHECK")
        if (player == 0 and player_is_bb) or (player == 1 and not player_is_bb):
            show_cards = True
            draw_hand(hands[1], 175, 50)
            if determine_winner(hands[0], hands[1]) == "player":
                player_stacks += pot_size
                print("Player Wins!")
            elif determine_winner(hands[0], hands[1]) == "bot":
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
            if determine_winner(hands[0], hands[1]) == "player":
                player_stacks += pot_size
                print("Player Wins!")
            elif determine_winner(hands[0], hands[1]) == "bot":
                bot_stacks += pot_size
                print("Bot Wins!")
            else:
                player_stacks += pot_size/2
                bot_stacks += pot_size/2
                print("Tie!")
            bet_made = False


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

def determine_winner(hand1, hand2):
    player_best = evaluate_hand(list(hand1))
    bot_best = evaluate_hand(list(hand2))
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




import numpy as np
import random
from collections import defaultdict

class Node:
	def __init__(self, bet_options):
		self.num_actions = len(bet_options)
		self.regret_sum = defaultdict(int)
		self.strategy = defaultdict(int)
		self.strategy_sum = defaultdict(int)
		self.bet_options = bet_options

	def get_strategy(self):
		normalizing_sum = 0
		for a in self.bet_options:
			if self.regret_sum[a] > 0:
				self.strategy[a] = self.regret_sum[a]
			else:
				self.strategy[a] = 0
			normalizing_sum += self.strategy[a]

		for a in self.bet_options:
			if normalizing_sum > 0:
				self.strategy[a] /= normalizing_sum
			else:
				self.strategy[a] = 1.0/self.num_actions

		return self.strategy

	def get_average_strategy(self):
		avg_strategy = defaultdict(int)
		normalizing_sum = 0
		
		for a in self.bet_options:
			normalizing_sum += self.strategy_sum[a]
		for a in self.bet_options:
			if normalizing_sum > 0:
				avg_strategy[a] = self.strategy_sum[a] / normalizing_sum
			else:
				avg_strategy[a] = 1.0 / self.num_actions
		
		return avg_strategy

class LeducCFR:
	def __init__(self, iterations, decksize, starting_stack):
		#self.nbets = 2
		self.iterations = iterations
		self.decksize = decksize
		self.bet_options = starting_stack
		self.cards = sorted(np.concatenate((np.arange(decksize),np.arange(decksize))))
		self.nodes = {}

	def cfr_iterations_external(self):
		util = np.zeros(2)
		for t in range(1, self.iterations + 1): 
			for i in range(2):
					random.shuffle(self.cards)
					util[i] += self.external_cfr(self.cards[:3], [[], []], 0, 2, 0, i, t)
		print('Average game value: {}'.format(util[0]/(self.iterations)))
		
		# with open('leducnlstrat.txt', 'w+') as f:
		# 	for i in sorted(self.nodes):
		# 		f.write('{}, {}\n'.format(i, self.nodes[i].get_average_strategy()))
		# 		print(i, self.nodes[i].get_average_strategy())

	def winning_hand(self, cards):
		if cards[0] == cards[2]:
			return 0
		elif cards[1] == cards[2]:
			return 1
		elif cards[0] > cards[1]:
			return 0
		elif cards[1] > cards[0]:
			return 1
		elif cards[1] == cards[0]:
			return -1

	def valid_bets(self, history, rd, acting_player):
		if acting_player == 0:
			acting_stack = int(19 - (np.sum(history[0][0::2]) + np.sum(history[1][0::2])))
		elif acting_player == 1:
			acting_stack = int(19 - (np.sum(history[0][1::2]) + np.sum(history[1][1::2])))


		# print('VALID BETS CHECK HISTORY', history)
		# print('VALID BETS CHECK ROUND', rd)
		# print('VALID BETS CHECK ACTING STACK', acting_stack)
		curr_history = history[rd]


		if len(history[rd]) == 0:
			# print('CASE LEN 0', [*np.arange(acting_stack+1)])
			return [*np.arange(acting_stack+1)]

		elif len(history[rd]) == 1:
			min_raise = curr_history[0]*2
			call_amount = curr_history[0]
			if min_raise > acting_stack:
				if history[rd] == [acting_stack]:
					# print('CASE LEN 1', [0, acting_stack])
					return [0, acting_stack]
				else:
					# print('CASE LEN 1', [0, call_amount, acting_stack])
					return [0, call_amount, acting_stack]
			else:
				if history[rd] == [0]:
					# print('CASE LEN 1', [*np.arange(min_raise, acting_stack+1)])
					return [*np.arange(min_raise, acting_stack+1)]
				else:
					# print('CASE LEN 1', [0, call_amount, *np.arange(min_raise, acting_stack+1)])
					return [0, call_amount, *np.arange(min_raise, acting_stack+1)]

		elif len(history[rd]) == 2:
			min_raise = 2*(curr_history[1] - curr_history[0])
			call_amount = curr_history[1] - curr_history[0]
			if min_raise > acting_stack:
				if call_amount == acting_stack:
					# print('CASE LEN 2', [0, acting_stack])
					return [0, acting_stack]
				else:
					# print('CASE LEN 2', [0, call_amount, acting_stack])
					return [0, call_amount, acting_stack]
			else:
				# print('CASE LEN 2', [0, call_amount, *np.arange(min_raise, acting_stack+1)])
				return [0, call_amount, *np.arange(min_raise, acting_stack+1)]

		elif len(history[rd]) == 3:
			call_amount = np.abs(curr_history[1] - curr_history[2] - curr_history[0])
			# print('CASE LEN 3', [0, call_amount])
			return [0, call_amount] #final bet (4 maximum per rd)

	def external_cfr(self, cards, history, rd, pot, nodes_touched, traversing_player, t):
		if t % 1000 == 0 and t>0:
			print('THIS IS ITERATION', t)
		plays = len(history[rd])
		acting_player = plays % 2
		# print('*************')
		# print('HISTORY RD', history[rd])
		# print('PLAYS', plays)

		if plays >= 2:
			p0total = np.sum(history[rd][0::2])
			p1total = np.sum(history[rd][1::2])
			# print('P0 TOTAL', p0total)
			# print('P1 TOTAL', p1total)
			# print('ROUND BEG', rd)
				
			if p0total == p1total:
				if rd == 0 and p0total != 19:
					rd = 1
					# print('ROUND TO 1')
				else:
					# print('SHOWDOWN RETURN')
					winner = self.winning_hand(cards)
					if winner == -1:
						return 0
					elif traversing_player == winner:
						return pot/2
					elif traversing_player != winner:
						return -pot/2

			elif history[rd][-1] == 0: #previous player folded
				# print('FOLD RETURN')
				if acting_player == 0 and acting_player == traversing_player:
					return p1total+1
				elif acting_player == 0 and acting_player != traversing_player:
					return -(p1total +1)
				elif acting_player == 1 and acting_player == traversing_player:
					return p0total+1
				elif acting_player == 1 and acting_player != traversing_player:
					return -(p0total +1)
		# print('ROUND AFTER', rd)
		if rd == 0:
			infoset = str(cards[acting_player]) + str(history)
		elif rd == 1:
			infoset = str(cards[acting_player]) + str(cards[2]) + str(history)

		if acting_player == 0:
			infoset_bets = self.valid_bets(history, rd, 0)
		elif acting_player == 1:
			infoset_bets = self.valid_bets(history, rd, 1)
		# print('ROUND', rd)
		# print('INFOSET BETS', infoset_bets)
		if infoset not in self.nodes:
			self.nodes[infoset] = Node(infoset_bets)

		# print(self.nodes[infoset])
		# print(infoset)

		nodes_touched += 1

		if acting_player == traversing_player:
			util = defaultdict(int)
			node_util = 0
			strategy = self.nodes[infoset].get_strategy()
			for a in infoset_bets:
				if rd == 0:
					next_history = [history[0] + [a], history[1]]
				elif rd == 1:
					next_history = [history[0], history[1] + [a]]
				pot += a
				util[a] = self.external_cfr(cards, next_history, rd, pot, nodes_touched, traversing_player, t)
				node_util += strategy[a] * util[a]

			for a in infoset_bets:
				regret = util[a] - node_util
				self.nodes[infoset].regret_sum[a] += regret
			return node_util

		else: #acting_player != traversing_player
			strategy = self.nodes[infoset].get_strategy()
			# print('STRATEGY', strategy)
			dart = random.random()
			# print('DART', dart)
			strat_sum = 0
			for a in strategy:
				strat_sum += strategy[a]
				if dart < strat_sum:
					action = a
					break
			# print('ACTION', action)
			if rd == 0:
				next_history = [history[0] + [action], history[1]]
			elif rd == 1:
				next_history = [history[0], history[1] + [action]]
			pot += action
			# if acting_player == 0:
			# 	p0stack -= action
			# elif acting_player == 1:
			# 	p1stack -= action
			# print('NEXT HISTORY2', next_history)
			util = self.external_cfr(cards, next_history, rd, pot, nodes_touched, traversing_player, t)
			for a in infoset_bets:
				self.nodes[infoset].strategy_sum[a] += strategy[a]
			return util




def main():
    global bet_choice, button_locked_until, player_is_bb, bot_should_act
    clock = pygame.time.Clock()
    running = True
    load_card_images()
    reset_round()
    
    while running:
        if show_cards:
            pygame.time.delay(3000)
            reset_round()
        screen.fill((0, 100, 0))
        draw_player_info()
        draw_hand(hands[0], 175, 500)
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
                            
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()

if __name__ == '__main__':
    main()