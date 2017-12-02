#!/usr/bin/python

# This is a dummy peer that just illustrates the available information your peers
# have available.

# You'll want to copy this file to AgentNameXXX.py for various versions of XXX,
# probably get rid of the silly logging messages, and then add more logic.

# TODO:
# 1 (uploads) :
    # - implement reciprocation
        ## -- figure out which peers have uploaded to me the most
    # - optimistic unchoking - every 3rd round, unchoke a random peer
# 2 (requests)

import random
import logging

from messages import Upload, Request
from util import even_split
from peer import Peer

class akjcstd(Peer):
    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"

    def get_piece_presences(self, peers, needed_pieces):
        piece_count_dict = {}
        piece_holder_dict = {}
        for peer in peers:
            for piece in peer.available_pieces:
                # increment counts to pieces found
                if piece in piece_count_dict and piece in needed_pieces:
                    piece_count_dict[piece] += 1
                    piece_holder_dict[piece].append(peer.id)
                # new piece found and in needed pieces
                elif piece in needed_pieces:
                    piece_count_dict[piece] = 1
                    piece_holder_dict[piece] = [peer.id]
        return (piece_count_dict, piece_holder_dict)

    def requests(self, peers, history):
        """
        ** must ask for pieces the peer has **

        peers: available info about the peers (who has what pieces)
        history: what's happened so far as far as this peer can see

        returns: a list of Request() objects

        This will be called after update_pieces() with the most recent state.
        """
        needed = lambda i: self.pieces[i] < self.conf.blocks_per_piece
        needed_pieces = filter(needed, range(len(self.pieces)))
        np_set = set(needed_pieces)  # sets support fast intersection ops.


        logging.debug("%s here: still need pieces %s" % (
            self.id, needed_pieces))

        logging.debug("%s still here. Here are some peers:" % self.id)
        for p in peers:
            logging.debug("id: %s, available pieces: %s" % (p.id, p.available_pieces))

        logging.debug("And look, I have my entire history available too:")
        logging.debug("look at the AgentHistory class in history.py for details")
        logging.debug(str(history))

        requests = []   # We'll put all the things we want here
        # Symmetry breaking is good...
        random.shuffle(needed_pieces)

        # get all peices and corresponding counts
        (viable_pieces_dict, piece_holder_dict) = self.get_piece_presences(peers, np_set)

        num_of_requests = min(self.max_requests, len(viable_pieces_dict.keys()))
        while (len(requests) < num_of_requests):
            rarest_piece_id = min(viable_pieces_dict, key=viable_pieces_dict.get)
            viable_pieces_dict.pop(rarest_piece_id, None)
            request = Request(self.id, random.choice(piece_holder_dict[rarest_piece_id]), rarest_piece_id, self.pieces[rarest_piece_id])
            requests.append(request)

        return requests

    def uploads(self, requests, peers, history):
        """
        ** must add up to no more than the peer's bandwidth cap **


        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """
        #todo: check we don't upload more than self.up_bw?


        rnd = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, rnd))
        # One could look at other stuff in the history too here.
        # For example, history.downloads[round-1] (if round != 0, of course)
        # has a list of Download objects for each Download to this peer in
        # the previous round.
        bws = []


        # get requester ids
        rids_set = set(map(lambda i: i.requester_id, requests))
        chosen_list_ids = []
        res = []
        logging.debug('RIDS %s' % (rids_set))

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:
            CUTOFF = 4
            # reciprocation
            # definitely upload to those who we have recently downloaded from - use similar logic for PropShare client also
            helpers = []
            empty_helpers = []
            for d in history.downloads[rnd - 1]:
                if d.to_id == self.id and d.from_id in rids_set:
                    helpers.append(d)

            # sort by highest value providers in preceding round
            helpers.sort(key=lambda i: i.blocks)

            helper_ids = list(map(lambda k: k.from_id, helpers))

            # lazy_nodes = list(filter(lambda x: x not in tmp, tmp))
            # if peers provided 0 value at beginning, append them

            if len(helper_ids) < CUTOFF:
                lazy_nodes = []
                for lazy_req in requests:
                    if lazy_req.requester_id not in helper_ids:
                        lazy_nodes.append(lazy_req)
                amount_to_add = min(CUTOFF - len(helper_ids), len(lazy_nodes))
                for x in range(amount_to_add):
                    empty_helpers.append(lazy_nodes[x])

            empty_ids = list(map(lambda l: l.requester_id, empty_helpers))
            # set complements
            chosen_list_ids = helper_ids + empty_ids
            chosen_set_ids = set(chosen_list_ids)
            not_chosen_ids = rids_set - chosen_set_ids

            # todo: kick them out after 3 rounds if not helping
            # optimistic unchoking
            if rnd % 3 == 0 and len(not_chosen_ids) != 0:
                request_id = random.choice(list(not_chosen_ids))
                res = chosen_list_ids[:CUTOFF - 1] + [request_id]
                self.dummy_state['unchoked_id'] = request_id
            else:
                try:
                    res = chosen_list_ids[:CUTOFF - 1] + [self.dummy_state['unchoked_id']]
                except:
                    res = chosen_list_ids[:CUTOFF]
                # todo: ? add something to internal state to remember who we
                # optimisticly unchoked so we can stop uploading to them after 3 rounds?
                logging.debug("Still here: uploading to a random peer")


            # Evenly "split" my upload bandwidth among the one chosen requester
            # only call this when chosen isn't empty?
            if len(res) != 0:
                bws = even_split(self.up_bw, len(res))
            else:
                return {}

            # change my internal state for no reason
            self.dummy_state["cake"] = "pie"

        #todo: decide how many requests to actually fill
            #(i.e. how many slots each peer should have - maybe some function of self.up_bw)



        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peer_id, bw)
                   for (peer_id, bw) in zip(res, bws)]

        return uploads
