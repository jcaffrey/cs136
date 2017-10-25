#!/usr/bin/env python

import random

from gsp import GSP

class VCG:
    """
    Implements the Vickrey-Clarke-Groves mechanism for ad auctions.
    """
    @staticmethod
    def compute(slot_clicks, reserve, bids):
        """
        Given info about the setting (clicks for each slot, and reserve price),
        and bids (list of (id, bid) tuples), compute the following:
          allocation:  list of the occupant in each slot
              len(allocation) = min(len(bids), len(slot_clicks))
          per_click_payments: list of payments for each slot
              len(per_click_payments) = len(allocation)

        If any bids are below the reserve price, they are ignored.

        Returns a pair of lists (allocation, per_click_payments):
         - allocation is a list of the ids of the bidders in each slot
            (in order)
         - per_click_payments is the corresponding payments.
        """

        # The allocation is the same as GSP, so we filled that in for you...

        valid = lambda (a, bid): bid >= reserve
        valid_bids = filter(valid, bids)

        rev_cmp_bids = lambda (a1, b1), (a2, b2): cmp(b2, b1)
        # shuffle first to make sure we don't have any bias for lower or
        # higher ids
        random.shuffle(valid_bids)
        valid_bids.sort(rev_cmp_bids)

        num_slots = len(slot_clicks)
        allocated_bids = valid_bids[:num_slots]
        if len(allocated_bids) == 0:
            return ([], [])

        (allocation, just_bids) = zip(*allocated_bids)

        # TODO: question: should we be using bids rather than valid_bids? probably!
        def total_payment(k):
            """
            Total payment for a bidder in slot k.
            """
            c = slot_clicks
            n = len(allocation)

            # print 'paybids' + str(payBids)
            #  TODO: is it possible daily spend to be less than utility???
            # print 'just_bids %s\n' + str(just_bids)

            # base case is the last bidder allocated..
            if n == k:
                try:
                    bi_one = valid_bids[k + 1][1]
                except:
                    # print 'in base except'
                    bi_one = valid_bids[len(valid_bids) - 1][1]
                # print 'special case' + str(bi_one)
                return max(bi_one, reserve)
            else:
                pi = .75 ** k
                pi_one = .75 ** (k + 1)
                try:
                    bi_one = valid_bids[k + 1][1]
                except:
                    # print 'other other other other except'
                    bi_one = valid_bids[len(valid_bids) - 1][1]
                # print 'k + 1 case' + str(bi_one)

                return (pi - pi_one) * bi_one + total_payment(k + 1)

            # TODO: Compute the payment and return it.

        def norm(totals):
            """Normalize total payments by the clicks in each slot"""
            return map(lambda (x,y): x/y, zip(totals, slot_clicks))

        per_click_payments = norm(
            [total_payment(k) for k in range(len(allocation))])

        return (list(allocation), per_click_payments)

    @staticmethod
    def bid_range_for_slot(slot, slot_clicks, reserve, bids):
        """
        Compute the range of bids that would result in the bidder ending up
        in slot, given that the other bidders submit bidders.
        Returns a tuple (min_bid, max_bid).
        If slot == 0, returns None for max_bid, since it's not well defined.
        """
        # Conveniently enough, bid ranges are the same for GSP and VCG:
        return GSP.bid_range_for_slot(slot, slot_clicks, reserve, bids)
