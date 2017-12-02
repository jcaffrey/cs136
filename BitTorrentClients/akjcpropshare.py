#!/usr/bin/python
#PROPSHARE
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

class akjcpropshare(Peer):
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

        uploads = []
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
            tot_downloaded = 0
            amt_share = {}  # amt_share[peer_id] = # blocks shared from that peer
            # ******* calculate proportion of download you recieved from each peer in that last round
            for d in history.downloads[rnd - 1]:
                # ASSUMPTION: we only consider peers who have requested something from us
                if d.to_id == self.id:
                    if d.from_id in rids_set:
                        if d.from_id not in amt_share:
                            amt_share[d.from_id] = d.blocks
                        else:
                            amt_share[d.from_id] += d.blocks
                    tot_downloaded += d.blocks

            # ******* allocate (roughly - round down every time for naive approach) the corresponding percentage of your up_bw to each peer
            if rnd % 3 == 0:
                SHAVE_OFF = .8
            else:
                SHAVE_OFF = 1

            tot_uploaded = 0
            for peer_id in amt_share:
                # ASSUMES we don't mind using all the slots
                # shave_off = AMOUNT_TO_UNCHOKE / len(amt_share.keys())
                prop_to_upload = float(amt_share[peer_id] / tot_downloaded)
                amt_to_upload =  int(prop_to_upload * self.up_bw * SHAVE_OFF)
                tot_uploaded += amt_to_upload
                uploads.append(Upload(self.id, peer_id, amt_to_upload))

            # ******* leave ~10% bw to optimisticly unchoke
            if rnd % 3 == 0:
                not_chosen_ids = rids_set - set(amt_share.keys())
                amt_bw_left = self.up_bw - tot_uploaded
                if len(not_chosen_ids) > 0:
                    unchoke_id = random.choice(list(not_chosen_ids))
                else:
                    unchoke_id = random.choice(list(amt_share.keys()))
                uploads.append(Upload(self.id, unchoke_id, amt_bw_left))
            # check what percentage is left over from just rounding down
        return uploads

    # PROPSHARE problems: downloads mostly just come from the peers in the first 100 rounds!
