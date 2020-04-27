# ckwg +28
# Copyright 2018 by Kitware, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
#  * Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  * Neither name of Kitware, Inc. nor the names of any contributors may be used
#    to endorse or promote products derived from this software without specific
#    prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS ``AS IS''
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE AUTHORS OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import numpy as np
import torch
import collections

class track_state(object):
    def __init__(self, frame_id, bbox_center, ref_point,
                 interaction_feature, app_feature, bbox, ref_bbox,
                 detected_object, sys_frame_id, sys_frame_time):
        self.bbox_center = bbox_center
        self.ref_point = ref_point

        '''a list [x, y, w, h]'''
        self.bbox = bbox
        self.ref_bbox = ref_bbox

        # got required AMI features in torch.tensor format
        self.app_feature = app_feature
        self.motion_feature = torch.FloatTensor(2).zero_()
        self.interaction_feature = interaction_feature
        self.bbar_feature = torch.FloatTensor(2).zero_()

        self.track_id = -1
        self.frame_id = frame_id

        self.detected_object = detected_object

        self.sys_frame_id = sys_frame_id
        self.sys_frame_time = sys_frame_time

        # FIXME: the detected_object confidence does not work
        # For now, I just set the confidence = 1.0
        #self.conf = detectedObject.confidence()
        self.conf = 1.0


class track(object):
    def __init__(self, track_id):
        self.track_id = track_id
        self.track_state_list = []
        self.max_conf = 0.0

    def __len__(self):
        return len(self.track_state_list)

    def __getitem__(self, idx):
        return self.track_state_list[idx]

    def __iter__(self):
        return iter(self.track_state_list)

    def append(self, new_track_state):
        if not self.track_state_list:
            new_track_state.motion_feature = torch.FloatTensor(2).zero_()
        else:
            pre_ref_point = np.asarray(self.track_state_list[-1].ref_point, dtype=np.float32).reshape(2)
            cur_ref_point = np.asarray(new_track_state.ref_point, dtype=np.float32).reshape(2)
            new_track_state.motion_feature = torch.from_numpy(cur_ref_point - pre_ref_point)

        new_track_state.track_id = self.track_id
        self.track_state_list.append(new_track_state)
        self.max_conf = max(self.max_conf, new_track_state.conf)

    def duplicate_track_state(self, timestep_len = 6):
        du_track = track(self.track_id)
        tsl = self.track_state_list
        tsl = [tsl[0]] * (timestep_len - len(tsl)) + tsl
        du_track.track_state_list = tsl
        du_track.max_conf = self.max_conf

        return du_track

class track_set(object):
    def __init__(self):
        self.id_ts_dict = collections.OrderedDict()
        # We implement an ordered set by mapping to None
        self.active_id_set = collections.OrderedDict()

    def __len__(self):
        return len(self.id_ts_dict)

    def __iter__(self):
        return iter(self.id_ts_dict.values())

    def iter_active(self):
        return (self[i] for i in self.active_id_set)

    def __getitem__(self, track_id):
        return self.id_ts_dict[track_id]

    def get_all_track_id(self):
        return sorted(self.id_ts_dict)

    def get_max_track_id(self):
        return max(self.id_ts_dict) if self.id_ts_dict else 0

    def deactivate_track(self, track):
        del self.active_id_set[track.track_id]

    def deactivate_all_tracks(self):
        self.active_id_set.clear()

    def active_count(self):
        return len(self.active_id_set)

    def make_track(self, track_id, exist_ok=None):
        """Create a new track in this track_set with the provided track ID,
        mark it as active, and return it.

        If exist_ok is true (default false), then track_id may be the
        ID of an existing track, in which case it is remarked as
        active and returned.

        """
        if track_id in self.id_ts_dict:
            if not exist_ok:
                raise ValueError("Track ID exists in the track set!")
            new_track = self.id_ts_dict[track_id]
        else:
            new_track = track(track_id)
            self.id_ts_dict[track_id] = new_track
        self.active_id_set[track_id] = None
        return new_track


if __name__ == '__main__':
    t = track(0)
    for i in range(10):
        t.append(track_state((i, i*i*0.1), [], []))

    for item in t[:]:
        print(item.motion_feature)
