#!/usr/bin/env python

import sys

from gsp import GSP
from util import argmax_index

class Jc24bb:
    """Balanced bidding agent"""
    def __init__(self, id, value, budget):
        self.id = id
        self.value = value
        self.budget = budget

    def initial_bid(self, reserve):
        return self.value / 2


    def slot_info(self, t, history, reserve):
        """Compute the following for each slot, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns list of tuples [(slot_id, min_bid, max_bid)], where
        min_bid is the bid needed to tie the other-agent bid for that slot
        in the last round.  If slot_id = 0, max_bid is 2* min_bid.
        Otherwise, it's the next highest min_bid (so bidding between min_bid
        and max_bid would result in ending up in that slot)
        """
        prev_round = history.round(t-1)
        other_bids = filter(lambda (a_id, b): a_id != self.id, prev_round.bids)

        clicks = prev_round.clicks
        def compute(s):
            (min, max) = GSP.bid_range_for_slot(s, clicks, reserve, other_bids)
            if max == None:
                max = 2 * min
            return (s, min, max)

        info = map(compute, range(len(clicks)))

        return info


    def expected_utils(self, t, history, reserve):
        """
        Figure out the expected utility of bidding such that we win each
        slot, assuming that everyone else keeps their bids constant from
        the previous round.

        returns a list of utilities per slot.
        """
        utilities = []
        prev_round = history.round(t-1)
        other_bids = filter(lambda (a_id, b): a_id != self.id, prev_round.bids)
        clicks = prev_round.clicks

        num_slots = len(clicks)
        # todo: num bidders 1 bigger than num slots? --> add dumby of reserve price at the end
        if len(other_bids) < len(clicks) + 1:
            other_bids = other_bids + [(-1,reserve)] * (len(clicks)+1-len(other_bids))
        # print 'other_bids ' + str(other_bids) + ' len(other_bids) ' + str(len(other_bids)) + ' vs len(clicks) ' + str(len(clicks))
        for j in range(num_slots):
            pos_effect_j = clicks[j]
            cost = other_bids[j][1]
            utility = pos_effect_j * (self.value - cost)
            utilities.append(utility)

        return utilities

    def target_slot(self, t, history, reserve):
        """Figure out the best slot to target, assuming that everyone else
        keeps their bids constant from the previous rounds.

        Returns (slot_id, min_bid, max_bid), where min_bid is the bid needed to tie
        the other-agent bid for that slot in the last round.  If slot_id = 0,
        max_bid is min_bid * 2
        """
        i =  argmax_index(self.expected_utils(t, history, reserve))  # need to make sure that expected_utils is not an empty list!
        info = self.slot_info(t, history, reserve)
        return info[i]

    def bid(self, t, history, reserve):
        # The Balanced bidding strategy (BB) is the strategy for a player j that, given
        # bids b_{-j},
        # WE HAVE THIS s*_j ALREADY- targets the slot s*_j which maximizes his utility, that is,
        # s*_j = argmax_s {clicks_s (v_j - t_s(j))}.
        # NEED TO DO THIS - chooses his bid b' for the next round so as to
        # satisfy the following equation:
        # clicks_{s*_j} (v_j - t_{s*_j}(j)) = clicks_{s*_j-1}(v_j - b')
        # (p_x is the price/click in slot x)
        # If s*_j is the top slot, bid the value v_j
        prev_round = history.round(t-1)
        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)
        other_bids = filter(lambda (a_id, b): a_id != self.id, prev_round.bids)
        clicks = prev_round.clicks

        # going for top, bid true value
        if slot == 0:
            return self.value
        # not expecting to win
        t_star = min_bid
        if t_star >= self.value:
            return self.value


        # otherwise bid according to balanced bidding equation
        t_star = min_bid
        vi = self.value

        pj = clicks[slot]
        pj_one = clicks[slot - 1]

        effect =  (pj * float((vi - t_star)))/(float(pj_one))
        bid = vi - effect

        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)
