import pygame
import random
import itertools
import pickle
import ast
import numpy as np
from collections import Counter
from itertools import zip_longest

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
bot_stacks = big_blind*20
player_stacks = big_blind*20
hands = []
deck = []
button_locked_until = 0
if player_is_bb:
	bet_history = [(1, 1), (0, 1)]
else:
	bet_history = [(0, 1), (1, 1)]
show_cards = False
pre_flop = True
import ast
from collections import defaultdict

strategy_dict = {}

with open('threehand1M.txt', 'r') as f:
	for line in f:
		if not line.strip():
			continue  # skip empty lines

		parts = line.strip().split('], ', 1)
		# print(parts)
		key_part = parts[0] + ']'  # first and second elements
		val_part = parts[1]
		# key_str = key_part + ']'  # Fix the key formatting
		# val_str = 'defaultdict' + val_part  # Reattach the header

		# # Safely parse the key using ast.literal_eval
		# key = ast.literal_eval(key_str)

		# # Clean up and parse the value
		# val_dict_str = val_str.split('(', 1)[1].rsplit(')', 1)[0]  # Extract dict content
		# strategy_map = ast.literal_eval(val_dict_str)  # Convert to dict
		# strategy_dict[key] = defaultdict(int, strategy_map)
		strategy_dict[key_part] = ast.literal_eval(val_part)

# counter = 0
# for i in strategy_dict:
# 	print(i, strategy_dict.get(i))
# 	counter += 1
# 	if counter > 20:
# 		break




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

def get_shuffled_deck():
	deck = [(rank, suit) for suit in suits for rank in ranks]
	random.shuffle(deck)
	return deck

def load_card_images():
	global card_images
	for suit in suits:
		for rank in ranks:
			filename = f'cards/{rank}_of_{suit}.png'
			image = pygame.image.load(filename)
			image = pygame.transform.scale(image, (CARD_WIDTH, CARD_HEIGHT))
			card_images[(rank, suit)] = image

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
	if bet_amount >= 2*highest_bet:
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
			print("Bot Wins!")
			bot_stacks += pot_size
			highest_opp_bet = 0
			for i, j in bet_history:
				if i == 0 and j > highest_opp_bet:
					highest_opp_bet = j
			bot_stacks += highest_opp_bet * big_blind
			player_stacks -= highest_opp_bet * big_blind
		else:
			print("Player Wins!")
			player_stacks += pot_size
			highest_opp_bet = 0
			for i, j in bet_history:
				if i == 1 and j > highest_opp_bet:
					highest_opp_bet = j
			player_stacks += highest_opp_bet * big_blind
			bot_stacks -= highest_opp_bet * big_blind
		if player_stacks == 0:
			player_stacks = big_blind * 20
		elif bot_stacks == 0:
			bot_stacks == big_blind * 20
		pygame.time.delay(1500)
		reset_round()
		return
	elif action == "BET":
		if bet_amount > bot_stacks and player == 1:
			bet_amount = bot_stacks
		elif bet_amount > 20:
			bet_amount = 20
		print(f"{player}: {action} {bet_amount} BB")
		if pre_flop:
			pre_flop = False
		bet_history.append((player, bet_amount))
		bet_made = True
	elif action == "RAISE":
		if bet_amount > bot_stacks and player == 1:
			bet_amount = bot_stacks
		elif bet_amount > 20:
			bet_amount = 20
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
			if determine_winner(hands) == "player":
				player_stacks += pot_size
				print("Player Wins!")
			elif determine_winner(hands) == "bot":
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
			if determine_winner(hands) == "player":
				player_stacks += pot_size
				print("Player Wins!")
			elif determine_winner(hands) == "bot":
				bot_stacks += pot_size
				print("Bot Wins!")
			else:
				player_stacks += pot_size/2
				bot_stacks += pot_size/2
				print("Tie!")
			bet_made = False
		elif pre_flop and len(bet_history) == 2:
			bet_made = False
			bet_history.append((player, bet_history[-1][1]))
		else:
			pot_size += bet_history[-1][1] * 2 * big_blind
			player_stacks -= bet_history[-1][1] * big_blind
			bot_stacks -= bet_history[-1][1] * big_blind
			show_cards = True
			draw_hand(hands[1], 175, 50)
			if determine_winner(hands) == "player":
				player_stacks += pot_size
				print("Player Wins!")
			elif determine_winner(hands) == "bot":
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
			if determine_winner(hands) == "player":
				player_stacks += pot_size
				print("Player Wins!")
			elif determine_winner(hands) == "bot":
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
			if determine_winner(hands) == "player":
				player_stacks += pot_size
				print("Player Wins!")
			elif determine_winner(hands) == "bot":
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

def determine_winner(hands):
	player_best = evaluate_hand(list(hands[0]))
	bot_best = evaluate_hand(list(hands[1]))
	if player_best > bot_best:
		return "player"
	elif bot_best > player_best:
		return "bot"
	else:
		return "tie"

def classify_value(value):
	return "low" if value <= 8 else "high"

def classify_spec_value(value):
	return "lowest" if value <= 4 else "lower" if value <= 7 else "higher" if value <= 10 else "highest"

def bot_action():
	global bet_made
	history = [entry[1] for entry in bet_history[2:]]
	p0total = history[0::2]
	p1total = history[1::2]
	result0 = []
	result1 = []
	if len(p0total) > 0:
		result0 = [p0total[0]-1]
		for i in range(1, len(p0total)):
			result0.append(p0total[i] - p0total[i - 1]-1)
	if len(p1total) < 0:
		result1 = [p1total[0]-1] 
		for i in range(1, len(p1total)):
			result1.append(p1total[i] - p1total[i - 1]-1)
	bot = 0
	if len(p0total) == len(p1total):
		bot = 0
	else:
		bot = 1
	newresult = []
	for a, b in zip_longest(result0, result1):
		if a is not None:
			newresult.append(a)
		if b is not None:
			newresult.append(b)

	infoset = ""
	hand_strength = evaluate_hand(list(hands[1]))[0]
	if hand_strength == 0:
		infoset = classify_spec_value(evaluate_hand(list(hands[1]))[1][0]) + " card"
	elif hand_strength == 1:
		infoset = classify_spec_value(evaluate_hand(list(hands[1]))[1][0]) + " pair"
	elif hand_strength == 2:
		infoset = classify_value(evaluate_hand(list(hands[1]))[1][0]) + " flush"
	elif hand_strength == 3:
		infoset = classify_value(evaluate_hand(list(hands[1]))[1][0]) + " straight"
	elif hand_strength == 4:
		infoset = classify_value(evaluate_hand(list(hands[1]))[1][0]) + " triple"
	elif hand_strength == 5:
		infoset = "straight flush"
	infoset += str([int(k) for k in newresult])
	
	values = list(strategy_dict.get(infoset).keys())
	weights = list(strategy_dict.get(infoset).values())
	best_choice = random.choices(values, weights=weights, k=1)[0]
	
	# best_choice = 0
	# highest_percent = 0
	# for key, value in strategy_dict.get(infoset).items():
	# 	if value >= highest_percent:
	# 		best_choice = key
	# 		highest_percent = value
	
	action = ""
	# print(strategy_dict.get(infoset).items())
	# print(bet_history)
	# print(result0)
	# print(result1)
	# print(np.sum(result1))
	# print(best_choice)
	if bot == 0:
		if len(result1) > 0:
			if len(bet_history) == 3 and result1[0] == 0 and best_choice == 0:
				action = "CHECK"
			elif np.sum(result0) + 1 + best_choice == bet_history[-1][1]:
				action = "CALL"
			elif best_choice == 0:
				action = "FOLD"
			elif np.sum(result0) + 1 + best_choice > bet_history[-1][1]:
				action = "RAISE" if bet_made else "BET"
		else:
			if np.sum(result0) + 1 + best_choice == bet_history[-1][1]:
				action  = "CALL"
			elif best_choice == 0:
				action  = "FOLD"
			elif np.sum(result0) + 1 + best_choice > bet_history[-1][1]:
				action = "RAISE" if bet_made else "BET"
	else:
		if len(result0) > 0:
			if len(bet_history) == 3 and result0[0] == 0 and best_choice == 0:
				action = "CHECK"
			elif np.sum(result1) + 1 + best_choice == bet_history[-1][1]:
				action = "CALL"
			elif best_choice == 0:
				action = "FOLD"
			elif np.sum(result1) + 1 + best_choice > bet_history[-1][1]:
				action = "RAISE" if bet_made else "BET"
		else:
			if np.sum(result1) + 1 + best_choice == bet_history[-1][1]:
				action = "CALL"
			elif best_choice == 0:
				action = "FOLD"
			elif np.sum(result1) + 1 + best_choice > bet_history[-1][1]:
				action = "RAISE" if bet_made else "BET"
	# print(action)
	if action == "RAISE":
		bet_made = True
	if bot == 0:
		handle_action(action, np.sum(p0total) + 1 + best_choice, 1)
	else:
		handle_action(action, np.sum(p1total) + 1 + best_choice, 1)
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

	screen.blit(FONT.render("Round " + str(len(bet_history) - 1) + "/4", True, (255, 255, 255)), (30, 340))





def main():
	global bet_choice, button_locked_until, player_is_bb, bot_should_act, player_stacks, bot_stacks
	clock = pygame.time.Clock()
	running = True
	load_card_images()
	reset_round()
	
	while running:
		if show_cards:
			pygame.time.delay(3000)
			reset_round()
			if player_stacks == 0:
				player_stacks = big_blind * 20
			elif bot_stacks == 0:
				bot_stacks == big_blind * 20
		
		screen.fill((0, 100, 0))
		draw_player_info()
		draw_hand(hands[0], 175, 500)
		draw_pot_size()
		draw_card_backs(175, 50)
		round = len(bet_history) - 2

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
						elif action == "RAISE" or action  == "BET" and round < 3:
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