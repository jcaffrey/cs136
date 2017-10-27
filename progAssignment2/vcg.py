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

        # def total_payment(k):
        #     c = slot_clicks
        #     n = len(allocation)
        #     if n == k:
        #         pi = c[k-1]
        #         bi_one = valid_bids[k][1]
        #         return pi * max(reserve, bi_one)
        #     elif k <= n - 2:
        #         pi = c[k]
        #         pi_one = c[k+1]
        #         bi_one = valid_bids[k+1][1]
        #
        #         effect = (pi - pi_one) * bi_one
        #         print 'effect '  + str(effect) + ' at k ' + str(k)
        #
        #         return effect + total_payment(k + 1)
        #     else:
        #         return reserve


        # TODO: question: should we be using bids rather than valid_bids? probably!
        # careful to skip over where i wasn
        # just use slot_clicks for pos effect


        # just_bids = [0] + list(just_bids)
        # c = [0] + slot_clicks
        # def total_payment(k):
        #     payment = 0
        #     for i in range(k, len(just_bids)-1):
        #         payment += ( c[k] - c[k+1] ) * just_bids[k+1]
        #     return payment





        if len(valid_bids) < len(allocation)+1:
            valid_bids = valid_bids + [(-1,reserve)] * (len(allocation)+1-len(valid_bids))
        def total_payment(k):
            c = slot_clicks
            n = len(allocation)

            # be careful with off by one errors
            if (n-1) == k:
                pi = slot_clicks[k]

                bi_one = valid_bids[k+1][1]
                return pi * max(reserve, bi_one)
            else:
                pi = slot_clicks[k]
                pi_one = slot_clicks[k+1]

                bi_one = valid_bids[k+1][1]

                pos_diff = pi - pi_one
                effect = pos_diff * bi_one

                return effect + total_payment(k + 1)


        def norm(totals):
            """Normalize total payments by the clicks in each slot"""
            return map(lambda (x,y): x/y, zip(totals, slot_clicks))

        per_click_payments = norm(
            [total_payment(k) for k in range(len(allocation))])
        # pcp = []
        # # print 'valid_bids ' + str(valid_bids)
        # for k in range(len(allocation)):
        #     tpk = total_payment(k)
        #     print 'k value ' + str(k) + 'gives total payment ' + str(tpk)
        #     pcp.append(tpk)
        # per_click_payments = norm(pcp)

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
