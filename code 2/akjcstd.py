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

        # not sure this helps vvv
        peers.sort(key=lambda p: len(p.available_pieces))
        # request all available pieces from all peers!
        # (up to self.max_requests from each)
        for peer in peers:
            av_set = set(peer.available_pieces)
            isect = av_set.intersection(np_set)
            n = min(self.max_requests, len(isect))
            # More symmetry breaking -- ask for random pieces.
            # This would be the place to try fancier piece-requesting strategies
            # to avoid getting the same thing from multiple peers at a time.
            for piece_id in random.sample(isect, n):
                # aha! The peer has this piece! Request it.
                # which part of the piece do we need next?
                # (must get the next-needed blocks in order)
                start_block = self.pieces[piece_id]
                r = Request(self.id, peer.id, piece_id, start_block)
                requests.append(r)

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
        # rid = lambda i: i.requester_id is type(String)
        # rids = list(filter(rid, requests))
        rids = list(map(lambda i: i.requester_id, requests))
        logging.debug('RIDS %s' % (rids))

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
            chosen = []
            bws = []
        else:
            chosen = []

            # reciprocation
            # definitely upload to those who we have recently downloaded from - use similar logic for PropShare client also
            best_friend = 0
            for d in history.downloads[rnd - 1]:
                if d.to_id == self.id and d.from_id in rids:
                    if d.blocks > best_friend:
                        chosen.insert(0, d.from_id)
                        best_friend = d.blocks
                    else:
                        chosen.append(d.from_id)
                    logging.debug('ID %s was nice by sending %s to %s (me)' % (d.from_id, d.blocks, self.id))

            # optimistic unchoking
            if rnd % 3 == 0:
                request = random.choice(requests)
                chosen.insert(0, request.requester_id)
                # todo: ? add something to internal state to remember who we
                # optimisticly unchoked so we can stop uploading to them after 3 rounds?
                logging.debug("Still here: uploading to a random peer")

            # Evenly "split" my upload bandwidth among the one chosen requester
            # only call this when chosen isn't empty?
            if len(chosen) != 0:
                logging.debug('%s chosen ones!' % (len(chosen)))
                bws = even_split(self.up_bw, len(chosen))
            else:
                return {}

            # change my internal state for no reason
            self.dummy_state["cake"] = "pie"

        #todo: decide how many requests to actually fill
            #(i.e. how many slots each peer should have - maybe some function of self.up_bw)

        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peer_id, bw)
                   for (peer_id, bw) in zip(chosen, bws)]

        return uploads
