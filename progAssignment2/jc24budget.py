#!/usr/bin/env python

import sys

from gsp import GSP
from util import argmax_index


class Jc24Budget:
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
#        sys.stdout.write("slot info: %s\n" % info)
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
        i =  argmax_index(self.expected_utils(t, history, reserve))
        info = self.slot_info(t, history, reserve)
        return info[i]

    def bid(self, t, history, reserve):
        NUMROUNDS = 48
        # calculate how much money per round you have. (val - price)/price. decide threshold, adaptively update throughout auction
        # ideally you'd want to check other slots other than the ideal slot bc maybe ratio would be better

        prev_round = history.round(t-1)
        (slot, min_bid, max_bid) = self.target_slot(t, history, reserve)
        other_bids = filter(lambda (a_id, b): a_id != self.id, prev_round.bids)
        clicks = prev_round.clicks


        cur_round = history.num_rounds()
        rounds_left = NUMROUNDS - cur_round

        money_spent = history.agents_spent[self.id] / cur_round
        print 'money_spent ' + str(money_spent)
        if (self.budget - money_spent) < 0:
            budget_per_round = self.value
        else:
            budget_per_round = float((self.budget - money_spent)) / float(rounds_left)  # why is this negative sometimes?

        vi = self.value

        # if the min bid less than your value and budget_per_round
        if min_bid < vi and min_bid < budget_per_round:
            return min_bid

        # if you have the money..bid your true value..
        if budget_per_round > vi:
            return min(vi, min_bid)

        threshold = min_bid
        if min_bid != 0:
            threshold = float(self.value - min_bid) / float(min_bid)
        else:
            return 1
        print('min_bid %d. value %d. threshold %d. budget_per_round %d' % (min_bid, self.value, threshold, budget_per_round))


        # going for top, bid true value
        if slot == 0:
         return vi
        # not expecting to win
        t_star = min_bid
        if t_star >= vi:
         return vi


        # otherwise bid according to balanced bidding equation
        t_star = min_bid

        pj = clicks[slot]
        pj_one = clicks[slot - 1]

        # bid for slot 1: 8 - 2/3 * (8 - 5) = 8 - 2/3(3) = 6
        effect =  (pj * float((vi - t_star)))/(float(pj_one))
        bid = vi - effect

        return bid

    def __repr__(self):
        return "%s(id=%d, value=%d)" % (
            self.__class__.__name__, self.id, self.value)
