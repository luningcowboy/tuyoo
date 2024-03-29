# coding=utf-8

import copy
import time
from functools import wraps

card_num_to_human_map = {
    0: 'A', 13: 'A', 26: 'A', 39: 'A',
    1: '2', 14: '2', 27: '2', 40: '2',
    2: '3', 15: '3', 28: '3', 41: '3',
    3: '4', 16: '4', 29: '4', 42: '4',
    4: '5', 17: '5', 30: '5', 43: '5',
    5: '6', 18: '6', 31: '6', 44: '6',
    6: '7', 19: '7', 32: '7', 45: '7',
    7: '8', 20: '8', 33: '8', 46: '8',
    8: '9', 21: '9', 34: '9', 47: '9',
    9: '10', 22: '10', 35: '10', 48: '10',
    10: 'J', 23: 'J', 36: 'J', 49: 'J',
    11: 'Q', 24: 'Q', 37: 'Q', 50: 'Q',
    12: 'K', 25: 'K', 38: 'K', 51: 'K',
    52: 'joker',
    53: 'JOKER'
}

s2v = {
    '3': 0, '4': 1, '5': 2, '6': 3,
    '7': 4, '8': 5, '9': 6, '10': 7,
    'J': 8, 'j': 8,
    'Q': 9, 'q': 9,
    'K': 10, 'k': 10,
    'A': 11, 'a': 11,
    '2': 12,
    'Y': 13, 'y': 13, 'joker': 13,
    'Z': 14, 'z': 14, 'JOKER': 14

}

v2s = {
    0: '3', 1: '4', 2: '5', 3: '6',
    4: '7', 5: '8', 6: '9', 7: '10',
    8: 'J',
    9: 'Q',
    10: 'K',
    11: 'A',
    12: '2',
    13: 'joker',
    14: 'JOKER'
}



MIN_SINGLE_CARDS = 5
MIN_PAIRS = 3
MIN_TRIPLES = 2


def validate_cards(cards):
    for card in cards:
        if int(card) not in card_num_to_human_map.keys():
            return False
    return True


def tuyoo_card_to_human(cards):
    return [card_num_to_human_map[int(card)] for card in cards]


def format_input_cards(cards):
    return sorted([s2v[i] if i in s2v else i for i in cards])


def format_output_cards(cards):
    return sorted([v2s[i] if i in v2s else i for i in cards])


def calc_time(fn):
    @wraps(fn)
    def wrapper(*args, **kw):
        begin = time.time()
        result = fn(*args, **kw)
        end = time.time()
        print("Calc Time: %.2f seconds" % (end-begin))
        return result
    return wrapper


def print_func_name(fn):
    @wraps(fn)
    def wrapper(*args, **kw):
        print("--- %s ---" % fn.__name__)
        result = fn(*args, **kw)
        print("-" * 50)
        return result
    return wrapper


def get_rest_cards(cards, move):
    """
    :param cards: a list, current cards
    :param move: a list, current move
    :return: rest_cards, a list, rest cards
    """
    rest_cards = copy.deepcopy(cards)
    current_move = copy.deepcopy(move)
    while len(current_move) > 0:
        if current_move[0] in rest_cards:
            rest_cards.remove(current_move[0])
            current_move.remove(current_move[0])
        else:
            raise Exception("move is not a sub set of cards")
    return rest_cards


class GenAnyN(object):
    """
    Get any N cards from a card list
    Usage:
        gan = GenAnyN(a_card_list, n)
        n_cards_lists = gan.gen_n_cards_lists()
    """
    def __init__(self, array, count):
        self.array = array
        self.count = count
        self.all_listed = list()
        self.final_result = list()

    def _get_any_n(self, array, count, result=list()):
        if count == 0:
            tmp_result = copy.deepcopy(result)
            self.all_listed.append(tmp_result)
            return

        for i in array:
            new_array = copy.deepcopy(array)
            new_array.remove(i)
            result.append(i)
            self._get_any_n(new_array, count - 1, result)
            result.remove(i)

    def gen_n_cards_lists(self):
        array = copy.deepcopy(self.array)
        count = self.count
        self._get_any_n(array, count)

        tmp_result = [sorted(item) for item in self.all_listed]
        duplicated = list()
        i = 0
        while i < len(tmp_result) - 1:
            j = i + 1
            while j < len(tmp_result):
                if tmp_result[i] == tmp_result[j]:
                    duplicated.append(j)
                j += 1
            i += 1

        self.final_result = list()
        for i in range(len(tmp_result)):
            if i not in duplicated:
                self.final_result.append(tmp_result[i])

        return self.final_result


def show_situation(lorder_cards=(), farmer_cards=list(),
                   move=list(), next_player=''):
    print("Move is: %s" % format_output_cards(move))
    print("lorder cards: %s" % format_output_cards(lorder_cards))
    print("farmer cards: %s" % format_output_cards(farmer_cards))
    print("Next player: %s" % next_player)
    print("-" * 20)


def check_win(cards, role):
    if len(cards) == 0:
        print('%s win!' % role)
        return True
    return False


cardToPoint = [11, 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
               11, 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
               11, 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
               11, 12, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
               13, 14]


def translate_human_card_to_tycard(nongmin_cards, dizhu_cards):
    total_cards = list(reversed(range(54)))
    if isinstance(nongmin_cards, list) and isinstance(dizhu_cards, list):
        return nongmin_cards, dizhu_cards

    nongmin_cards = nongmin_cards.split()
    points_nongmin = [s2v[v] for v in nongmin_cards]
    dizhu_cards = dizhu_cards.split()
    points_dizhu = [s2v[v] for v in dizhu_cards]

    dizhu_out = []
    for point in points_dizhu:
        for card in total_cards:
            if cardToPoint[card] == point:
                dizhu_out.append(card)
                total_cards.remove(card)
                break

    nongmin_out = []
    for point in points_nongmin:
        for card in total_cards:
            if cardToPoint[card] == point:
                nongmin_out.append(card)
                total_cards.remove(card)
                break

    return nongmin_out, dizhu_out
