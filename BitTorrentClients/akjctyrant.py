#!/usr/bin/python

# TYRANT

import random
import logging

from messages import Upload, Request
from util import even_split
from peer import Peer


class akjctyrant(Peer):
    def post_init(self):
        print "post_init(): %s here!" % self.id
        self.dummy_state = dict()
        self.dummy_state["cake"] = "lie"
        self.download_changes = dict()
        self.prev_round_uploaded_to = dict()
        self.upload_increment_amount = 0.2
        self.tyrant_round_count = 3
        self.upload_decrement_amount = 0.1
        self.upload_round_counter = {}
        self.peer_node_limit = 4

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

        requests = []  # We'll put all the things we want here
        # Symmetry breaking is good...
        random.shuffle(needed_pieces)

        # get all peices and corresponding counts
        (viable_pieces_dict, piece_holder_dict) = self.get_piece_presences(peers, np_set)

        num_of_requests = min(self.max_requests, len(viable_pieces_dict.keys()))

        # Instead of just taking the rarest one, it selects from rarest third of pieces
        piece_rarity_list = sorted(viable_pieces_dict, key=viable_pieces_dict.get, reverse=True)

        """
        Used for rarest thirds method
        num_rare_pieces = len(piece_rarity_list)
        first_thirds_list = piece_rarity_list[:num_rare_pieces/3]
        second_thirds_list = piece_rarity_list[num_rare_pieces/3: + 2*(num_rare_pieces/3)]
        last_thirds_list = piece_rarity_list[2*(num_rare_pieces/3):]"""
        while (len(requests) < num_of_requests):

            """"
            This was the rarest thirds method, it ended up being less effective
            than just selecting a random piece with some probability

            # Iterates through rarest subsections of pieces
            selected_list = []
            if first_thirds_list:
                selected_list = first_thirds_list
            elif second_thirds_list:
                selected_list = second_thirds_list
            else:
                selected_list = last_thirds_list

            if len(first_thirds_list) <= 1:
                rand_index = 0
            else:
                rand_index = random.randint(0, len(selected_list) - 1)
            rand_rare_piece = selected_list[rand_index]
            selected_list = selected_list[:rand_index] + selected_list[(rand_index+1):]"""
            rand_probability = 1
            if random.randint(0, rand_probability) == rand_probability:
                rand_index = random.randint(0, len(piece_rarity_list) - 1)
                rand_rare_piece = piece_rarity_list.pop(rand_index)
            else:
                rand_rare_piece = piece_rarity_list.pop(0)

            request = Request(self.id, random.choice(piece_holder_dict[rand_rare_piece]), rand_rare_piece,
                              self.pieces[rand_rare_piece])
            requests.append(request)

        return requests

    """This makes:
        peers_sending_to_me: keys = peers, values = count of blocks they're sending
        self.upload_round_counter: keys = peers, values = number of rounds they've been sending"""
    def get_peers_sending_to_me(self, history):
        # Find peers that unchoked me last round
        peers_sending_to_me = {}
        for d in history.downloads[history.current_round() - 1]:
            peers_sending_to_me[d.from_id] = d.blocks
            if d.from_id in self.upload_round_counter:
                self.upload_round_counter[d.from_id] += 1
            else:
                self.upload_round_counter[d.from_id] = 1
        # Keep track of rounds people have uploaded to me, and delete them if they aren't
        for node_id in self.upload_round_counter:
            if node_id not in peers_sending_to_me:
                self.upload_round_counter[node_id] = 0
        return peers_sending_to_me

    """This makes:
        peer_download_rates: keys = peers, values = how much they downloaded last round"""
    def get_peer_download_rates(self, peers):
        peer_download_rates = {}
        for peer in peers:
            if peer not in self.download_changes:
                self.download_changes[peer.id] = len(peer.available_pieces)
                peer_download_rates[peer.id] = len(peer.available_pieces)
            else:
                if peer.available_pieces != self.download_changes[peer.id]:
                    # User has downloaded since last round
                    peer_download_rates[peer.id] = len(peer.available_pieces) - self.download_changes[peer]
                    self.download_changes[peer.id] = len(peer.available_pieces)
        return peer_download_rates

    """"This estimates F(j,i) for each user
        estimated_flow_rates: keys = peers, values = download rates / amount expected downloading from"""
    def get_estimated_flow_rates(self, peer_download_rates):
        estimated_flow_rates = {}
        for peer in list(peer_download_rates.keys()):
            estimated_flow_rates[peer] = float(peer_download_rates[peer]) / float(self.peer_node_limit)
        return estimated_flow_rates

    def uploads(self, requests, peers, history):
        """
        ** must add up to no more than the peer's bandwidth cap **


        requests -- a list of the requests for this peer for this round
        peers -- available info about all the peers
        history -- history for all previous rounds

        returns: list of Upload objects.

        In each round, this will be called after requests().
        """

        rnd = history.current_round()
        logging.debug("%s again.  It's round %d." % (
            self.id, rnd))
        recipient_node_bws = {}
        # get requester ids
        rids_set = set(map(lambda i: i.requester_id, requests))
        logging.debug('RIDS %s' % (rids_set))

        if len(requests) == 0:
            logging.debug("No one wants my pieces!")
        else:
            self.peer_node_limit = 4
            peers_sending_to_me = self.get_peers_sending_to_me(history)
            peer_download_rates = self.get_peer_download_rates(peers)
            estimated_flow_rates = self.get_estimated_flow_rates(peer_download_rates)

            cur_upload_rate = 0
            # While we have bw left and there are peers left to send to
            while (cur_upload_rate <= self.up_bw and peer_download_rates):
                # Iterates through taking max downloaders
                node_id = max(peer_download_rates, key=peer_download_rates.get)
                # If this top downloader is requesting from us
                if (node_id in rids_set):
                    # Check if we sent to them before but they didn't unchoke us to adjust sending rate
                    if (node_id in self.prev_round_uploaded_to) and (node_id not in peers_sending_to_me):
                        # Set their upload rate
                        incremented_upload_rate = self.prev_round_uploaded_to[node_id] * (1.0 + self.upload_increment_amount)
                        upload_rate = min(incremented_upload_rate, self.up_bw-cur_upload_rate)
                        cur_upload_rate += upload_rate
                        # Reset how much we are uploading to them
                        self.prev_round_uploaded_to[node_id] = float(incremented_upload_rate)
                        # Set in dict that we upload data from in Uploads
                        recipient_node_bws[node_id] = upload_rate
                        del peer_download_rates[node_id]
                    # If they unchoked us and they are top sender we maintain relationship
                    elif (node_id in self.prev_round_uploaded_to) and (node_id in peers_sending_to_me):
                        # Update how much they are sending to us just enough to maintain relationship
                        if self.upload_round_counter[node_id] >= self.tyrant_round_count:
                            decremented_upload_rate = self.prev_round_uploaded_to[node_id] * (1.0-self.upload_decrement_amount)
                            upload_rate = min(decremented_upload_rate, self.up_bw-cur_upload_rate)
                            self.prev_round_uploaded_to[node_id] = float(decremented_upload_rate)
                            del self.upload_round_counter[node_id]
                        else:
                            self.prev_round_uploaded_to[node_id] = float(peers_sending_to_me[node_id])
                            cur_upload_rate += self.prev_round_uploaded_to[node_id]
                            recipient_node_bws[node_id] = estimated_flow_rates[node_id]
                        del peer_download_rates[node_id]
                    # If they are top uploader but we have no relationship
                    else:
                        recipient_node_bws[node_id] = min(estimated_flow_rates[node_id], self.up_bw-cur_upload_rate)
                        cur_upload_rate += estimated_flow_rates[node_id]
                        del peer_download_rates[node_id]
                else:
                    del peer_download_rates[node_id]

        recipient_nodes = []
        recipient_bws = []
        for node in recipient_node_bws:
            recipient_nodes.append(node)
            recipient_bws.append(recipient_node_bws[node])
        # create actual uploads out of the list of peer ids and bandwidths
        uploads = [Upload(self.id, peer_id, bw)
                   for (peer_id, bw) in zip(recipient_nodes, recipient_bws)]

        return uploads
